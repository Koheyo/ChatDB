# Executes and validates SQL queries
import pandas as pd
import sqlparse
from bson import ObjectId

from db.nosql_connector import connect_to_nosql
#from db.postgres_connector import connect_to_postgres
from db.rdbms_connector import connect_to_rdbms


def validate_sql(sql_query: str) -> bool:
    """Validates the basic structure of an SQL statement."""
    try:
        statements = sqlparse.parse(sql_query)
        return bool(statements and len(statements) > 0)
    except Exception:
        return False


def execute_sql(sql_query: str):
    """Executes an SQL query with validation."""
    if not validate_sql(sql_query):
        return "SQL statement is invalid and cannot be executed."

    connection = connect_to_rdbms()
    try:
        with connection.cursor() as cursor:
            affected_rows = cursor.execute(sql_query)
            query_lower = sql_query.strip().lower()
            if query_lower.startswith(("select", "show", "describe")):
                # Get column names
                columns = [desc[0] for desc in cursor.description]
                # Fetch results and convert to list of dictionaries
                results = []
                for row in cursor.fetchall():
                    result_dict = {}
                    for i, value in enumerate(row):
                        result_dict[columns[i]] = value
                    results.append(result_dict)
                return results
            else:
                connection.commit()
                return f"{affected_rows} rows affected."
    finally:
        connection.close()


# def execute_postgres(query: str):
#     """Executes a PostgreSQL query."""
#     print("Executing PostgreSQL query:", query)
#     connection = connect_to_postgres()
#     try:
#         with connection.cursor() as cursor:
#             cursor.execute(query)
#             if query.strip().upper().startswith('SELECT'):
#                 results = cursor.fetchall()
#                 print("Query results:", results)
#                 return results
#             else:
#                 connection.commit()
#                 return f"{cursor.rowcount} rows affected."
#     except Exception as e:
#         print("Error executing PostgreSQL query:", str(e))
#         raise
#     finally:
#         connection.close()


def execute_nosql(nosql_query: str):
    """
    Execute a MongoDB query.
    The parameter `nosql_query` is expected to be a Python expression string that can be executed on MongoDB,
    for example: "db['students'].find({'name': 'Alice'})".

    Note: This uses eval to execute the query, so make sure the query content is trusted.
    """
    print("Executing MongoDB query:", nosql_query)
    db = connect_to_nosql()  # Already returns the database object
    try:
        # Execute the query in a secure context, providing the `db` variable for use in the expression
        result = eval(nosql_query, {"db": db})
        # If the result is a pymongo Cursor, convert it to a list
        if hasattr(result, "sort") or hasattr(result, "batch_size"):
            result = list(result)
        print("MongoDB query result:", result)
        return result
    except Exception as e:
        error_msg = f"Error executing MongoDB query: {str(e)}"
        print(error_msg)
        return error_msg

def clean_mongodb_data(data):
    """Clean MongoDB data by converting special types to strings, and flatten lists to comma-separated strings for DataFrame compatibility."""
    if isinstance(data, dict):
        return {k: clean_mongodb_data(v) for k, v in data.items()}
    elif isinstance(data, list):
        return ', '.join([str(clean_mongodb_data(item)) for item in data])
    elif isinstance(data, ObjectId):
        return str(data)
    elif isinstance(data, (pd.Timestamp, pd.DatetimeTZDtype)):
        return str(data)
    return data