# Converts natural language queries into structured database queries
import json
import re

from db.nosql_connector import connect_to_nosql
from db.postgres_connector import connect_to_postgres
from db.rdbms_connector import connect_to_rdbms
from llm.llm_integration import call_llm_api


def get_sql_schema():
    """Retrieves MySQL database schema with detailed column info."""
    connection = connect_to_rdbms()
    schema = {}
    try:
        with connection.cursor() as cursor:
            cursor.execute("SHOW TABLES;")
            tables = [row[0] for row in cursor.fetchall()]

            for table in tables:
                cursor.execute(f"SHOW FULL COLUMNS FROM {table};")
                columns = []
                for col in cursor.fetchall():
                    # SHOW FULL COLUMNS 返回顺序: Field, Type, Collation, Null, Key, Default, Extra, Privileges, Comment
                    columns.append({
                        "name": col[0],
                        "type": col[1],
                        "nullable": col[3] == "YES",
                        "key": col[4],  # 'PRI' for primary key
                        "default": col[5],
                        "extra": col[6]
                    })
                schema[table] = columns
    finally:
        connection.close()
    return schema


def get_postgres_schema():
    """Retrieves PostgreSQL database schema."""
    connection = connect_to_postgres()
    schema = {}
    try:
        with connection.cursor() as cursor:
            # Get all tables
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            tables = [row['table_name'] for row in cursor.fetchall()]

            # Get columns for each table
            for table in tables:
                cursor.execute("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = %s
                """, (table,))
                schema[table] = [row['column_name'] for row in cursor.fetchall()]
    finally:
        connection.close()
    return schema


def get_nosql_schema(sample_size=20, example_limit=3):
    """Retrieves MongoDB collection structure with field types and example values."""
    db = connect_to_nosql()
    schema = {}
    collections = db.list_collection_names()
    print("Available collections:", collections)

    for collection in collections:
        samples = list(db[collection].aggregate([{"$sample": {"size": sample_size}}]))
        field_types = {}
        for doc in samples:
            for key, value in doc.items():
                if key == '_id':
                    continue
                t = type(value).__name__
                if key not in field_types:
                    field_types[key] = set()
                field_types[key].add(t)

        schema[collection] = {
            k: {"types": list(field_types[k])} for k in field_types
        }
        print(f"Schema for {collection}:", schema[collection])
    return schema


def extract_sql_from_response(llm_response: str) -> str:
    """
    Extracts SQL statements or MongoDB queries from an LLM response.
    Supports code blocks (```python ... ```) or inline responses.
    """
    pattern = r"```[^\n]*\n([\s\S]*?)```"
    match = re.search(pattern, llm_response)
    if match:
        query = match.group(1).strip()
    else:
        query = llm_response.strip()

    if "db[" in query or "db." in query:
        query = query.strip()
        if query.startswith("result ="):
            query = query[len("result ="):].strip()
        return query

    return query


def generate_query(user_query: str, db_type: str) -> tuple:
    """Uses LLM to generate a database query based on schema."""
    if db_type == "mysql":
        schema = get_sql_schema()
        db_type_desc = "MySQL"
        schema_str = json.dumps(schema, indent=2, ensure_ascii=False)
    elif db_type == "postgres":
        schema = get_postgres_schema()
        db_type_desc = "PostgreSQL"
        schema_str = str(schema)
    else:  # mongodb
        schema = get_nosql_schema()
        db_type_desc = "MongoDB"
        schema_str = json.dumps(schema, indent=2, ensure_ascii=False)

    system_prompt = f"""
You are a professional database query generator. Your task is to convert the following natural language query into a valid database query, based on the provided schema.
The target database type is {db_type_desc}.

General rules:
- Only output the final query code, do not include any explanations, comments, or natural language.
- Always use the table/collection and column/field names exactly as provided in the schema.
- Never use or assume any field, table, or relationship that does not appear in the schema.
- If unsure, generate the simplest and safest query possible.
- Always wrap your output in a code block (e.g., ```sql ... ``` for MySQL, ```python ... ``` for MongoDB).

For MySQL queries:
- Use standard MySQL syntax only.
- Do not use PostgreSQL or any other database-specific syntax.
- Do not include comments or explanations.
- Only use table and column names that appear in the schema. Do not assume any extra fields or relationships.
- If you need to join tables, only use columns that exist in both tables as shown in the schema. Do not assume foreign keys unless they are explicitly present in the schema.
- If the query is about "the most", "the least", "top N", always use ORDER BY and LIMIT.
- If the query cannot be generated with the given schema, output a simple SELECT statement from an existing table.
- Never generate queries that cannot be executed with the provided schema.

For MongoDB queries:
- Use Python syntax for MongoDB queries (PyMongo style).
- Start with db["collection_name"].
- Always output a complete and executable query. Never output incomplete code (e.g., do not end with an open bracket).
- If you use aggregate, the pipeline must be complete and valid. If you cannot generate a complete and valid aggregate pipeline, you MUST output a simple find query instead, such as db["collection_name"].find({{}}).
- Never output only the beginning of an aggregate statement. Outputting only db["collection_name"].aggregate([ is strictly forbidden.
- Do not include comments or explanations.

Schema:
{schema_str}
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_query}
    ]

    completion = call_llm_api(messages)
    extracted_query = extract_sql_from_response(completion)
    print("Generated query:", extracted_query)
    
    # Determine query type based on content
    if db_type in ["mysql", "postgres"]:
        if extracted_query.upper().startswith(("SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "DROP")):
            return db_type.upper(), extracted_query
    else:  # mongodb
        if ".find(" in extracted_query or ".aggregate(" in extracted_query:
            return "NOSQL", extracted_query
    
    # Default to the specified database type
    return db_type.upper(), extracted_query