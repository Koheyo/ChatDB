# Converts natural language queries into structured database queries
import re

from db.nosql_connector import connect_to_nosql
from db.rdbms_connector import connect_to_rdbms
from llm.llm_integration import call_llm_api


def get_sql_schema():
    """Retrieves SQL database schema."""
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


def get_nosql_schema():
    """Retrieves MongoDB collection structure."""
    db = connect_to_nosql()["student"]
    schema = {}
    collections = db.list_collection_names()

    for collection in collections:
        document = db[collection].find_one()
        if document:
            schema[collection] = list(document.keys())
    print("attension!!!!!!!!!:",schema)
    return schema


def extract_sql_from_response(llm_response: str) -> str:
    """
    Extracts SQL statements from an LLM response, removing triple backticks if present.
    If no code block is detected, returns the original response.
    """
    # try:
    #     pattern = r"```[^\n]*\n([\s\S]*?)```"
    #     match = re.search(pattern, llm_response, re.DOTALL)
    #     if match:
    #         return match.group(1).strip()
    #     return llm_response.strip()
    # except Exception as e:
    #     return f"Error extracting SQL: {str(e)}"
    pattern = r"```[^\n]*\n([\s\S]*?)```"
    match = re.search(pattern, llm_response)
    if match:
        sql_query = match.group(1).strip()
    else:
        sql_query = llm_response.strip()

    return sql_query



def generate_query(user_query: str, db_type) -> tuple:
    """Uses LLM to generate an SQL/NoSQL query based on schema."""
    schema = get_sql_schema() if db_type == "sql" else get_nosql_schema()

    system_prompt = f"""
    You are a database query assistant. Based on the provided database schema, convert the following natural language query into a valid query.
    The target database type is specified as {db_type.upper()}.
    When the database type is SQL, output a valid SQL statement.
    When the database type is NOSQL, output a valid MongoDB query in Python syntax.
    IMPORTANT:
    - For NOSQL queries, use the collection names exactly as provided in the schema.
      For example, if the schema is {schema}, then the collection name to be used is "info".
      Your output for a NOSQL query must be a single Python expression starting with db["info"]
    - For SQL queries, use the provided schema as guidance.
    Schema:
    {schema}
    """

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_query}
    ]

    completion = call_llm_api(messages)
    extracted_query = extract_sql_from_response(completion)
    print("Generated query:", extracted_query)  # Debug print

    # First check if it's a NoSQL query
    if db_type == "nosql" and (".find(" in extracted_query or ".aggregate(" in extracted_query):
        return "NOSQL", extracted_query

    # Then check if it's a SQL query
    if db_type == "sql":
        # Check for SQL keywords
        if extracted_query.upper().startswith(("SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "SHOW", "DESCRIBE")):
            return "SQL", extracted_query
        # If it's not a clear SQL query, try to parse it as SQL
        try:
            import sqlparse
            parsed = sqlparse.parse(extracted_query)
            if parsed:
                return "SQL", extracted_query
        except:
            pass

    # Default to SQL if we can't determine the type
    return "SQL", extracted_query