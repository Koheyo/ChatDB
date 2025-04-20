# Converts natural language queries into structured database queries
import json
import re
import pymysql

from ..db.nosql_connector import connect_to_nosql
from ..db.postgres_connector import connect_to_postgres
from ..db.rdbms_connector import connect_to_rdbms
from .llm_integration import call_llm_api

def infer_json_array_type(connection, table_name: str, field_name: str, sample_size: int = 5):
    cursor = connection.cursor()
    query = f"SELECT `{field_name}` FROM `{table_name}` WHERE `{field_name}` IS NOT NULL LIMIT {sample_size};"
    cursor.execute(query)
    rows = cursor.fetchall()
    element_types = set()
    for (json_str,) in rows:
        try:
            parsed = json.loads(json_str)
            if isinstance(parsed, list):
                for item in parsed:
                    element_types.add(type(item))
        except Exception:
            return "invalid_json"

    if not element_types:
        return "empty_array"
    elif element_types == {str}:
        return "array<string>"
    elif element_types == {int}:
        return "array<int>"
    else:
        return "array<mixed>"

def get_sql_schema():
    """Retrieves MySQL database schema."""
    connection = connect_to_rdbms()
    schema = {}
    try:
        with connection.cursor() as cursor:
            cursor.execute("SHOW TABLES;")
            tables = [row[0] for row in cursor.fetchall()]

            for table in tables:
                cursor.execute(f"DESCRIBE {table};")
                columns = cursor.fetchall()
                schema[table] = {}
                for column in columns:
                    field_name = column[0]
                    field_type = column[1]
                    if "json" in field_type.lower() or "text" in field_type.lower():
                        inferred_type = infer_json_array_type(connection, table, field_name)
                        schema[table][field_name] = inferred_type
                    else:
                        schema[table][field_name] = field_type
    finally:
        connection.close()
    return schema

def get_postgres_schema():
    connection = connect_to_postgres()
    schema = {}
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            tables = [row['table_name'] for row in cursor.fetchall()]
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

def get_nosql_schema():
    db = connect_to_nosql()
    schema = {}
    collections = db.list_collection_names()
    for collection in collections:
        document = db[collection].find_one()
        if document:
            fields = [key for key in document.keys() if key != '_id']
            schema[collection] = fields
    return schema

def extract_sql_from_response(llm_response: str) -> str:
    try:
        pattern =  r"```[^\n]*\n([\s\S]*?)```"
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
    except re.error as e:
        print(f"Regex parse error: {e}")
        return llm_response.strip()

def fix_common_sql_errors(query: str) -> str:
    query = re.sub(r"CAST\(([^)]+?)\s+AS\s+JSON\)", r"JSON_QUOTE(\1)", query)
    query = re.sub(r"JSON_QUOTE\((\w+\.(?:\w*id|\w*_id))\)", r"CAST(\1 AS JSON)", query)
    return query

def rewrite_field_for_json(schema: dict, query: str) -> str:
    for table, fields in schema.items():
        for field, type_str in fields.items():
            if isinstance(type_str, str) and "array<string>" in type_str:
                # Replace actor_id in JSON_CONTAINS context with name
                query = re.sub(r"JSON_CONTAINS\([^,]+,\s*CAST\((\w+)\.actor_id\s+AS\s+JSON\)\s*,\s*'\$'\)",
                               r"JSON_CONTAINS(\g<1>.actors_json, JSON_QUOTE(\g<1>.name), '$')", query)
    return query

def generate_query(user_query: str, db_type: str) -> tuple:
    if db_type == "mysql":
        schema = get_sql_schema()
        db_type_desc = "MySQL"
        schema_str = json.dumps(schema, indent=2, ensure_ascii=False)
    elif db_type == "postgres":
        schema = get_postgres_schema()
        db_type_desc = "PostgreSQL"
        schema_str = str(schema)
    else:
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
    fixed_query = fix_common_sql_errors(extracted_query)
    final_query = rewrite_field_for_json(schema, fixed_query)
    print("Generated query:", final_query)

    if db_type in ["mysql", "postgres"]:
        if final_query.upper().startswith(("SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "DROP")):
            return db_type.upper(), final_query
    else:
        if ".find(" in final_query or ".aggregate(" in final_query:
            return "NOSQL", final_query

    return db_type.upper(), final_query
