# Converts natural language queries into structured database queries
import re

from db.nosql_connector import connect_to_nosql
from db.postgres_connector import connect_to_postgres
from db.rdbms_connector import connect_to_rdbms
from llm.llm_integration import call_llm_api


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
                schema[table] = [column[0] for column in cursor.fetchall()]
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


def get_nosql_schema():
    """Retrieves MongoDB collection structure."""
    db = connect_to_nosql()
    schema = {}
    
    # Get all collections
    collections = db.list_collection_names()
    print("Available collections:", collections)
    
    # Get schema for each collection
    for collection in collections:
        # Get one document from the collection to determine fields
        document = db[collection].find_one()
        if document:
            # Remove _id field as it's MongoDB specific
            fields = [key for key in document.keys() if key != '_id']
            schema[collection] = fields
            print(f"Schema for {collection}:", fields)
    
    return schema


def extract_sql_from_response(llm_response: str) -> str:
    """
    Extracts SQL statements or MongoDB queries from an LLM response.
    If no code block is detected, returns the original response.
    """
    pattern = r"```[^\n]*\n([\s\S]*?)```"
    match = re.search(pattern, llm_response)
    if match:
        query = match.group(1).strip()
    else:
        query = llm_response.strip()

    # For MongoDB queries, extract only the db.collection part
    if "db[" in query or "db." in query:
        lines = query.split('\n')
        for line in lines:
            if "db[" in line or "db." in line:
                query = line.strip()
                if query.startswith("result = "):
                    query = query[9:]  # Remove "result = " prefix
                break

    return query


def generate_query(user_query: str, db_type: str) -> tuple:
    """Uses LLM to generate a database query based on schema."""
    if db_type == "mysql":
        schema = get_sql_schema()
        db_type_desc = "MySQL"
    elif db_type == "postgres":
        schema = get_postgres_schema()
        db_type_desc = "PostgreSQL"
    else:  # mongodb
        schema = get_nosql_schema()
        db_type_desc = "MongoDB"

    system_prompt = f"""
    You are a database query assistant. Based on the provided database schema, convert the following natural language query into a valid query.
    The target database type is {db_type_desc}.
    
    For {db_type_desc} queries:
    - Use the table names and column names exactly as provided in the schema
    - Follow {db_type_desc} syntax and conventions
    - For PostgreSQL, use proper parameterized queries with %s for parameters
    - For MySQL, use proper MySQL syntax
    
    For MongoDB queries:
    - Use the collection names exactly as provided in the schema
    - Output a valid MongoDB query in Python syntax
    - Start with db["collection_name"]
    
    Schema:
    {schema}
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