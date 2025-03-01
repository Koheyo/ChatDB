# Executes and validates SQL queries
import sqlparse
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
                return cursor.fetchall()
            else:
                connection.commit()
                return f"{affected_rows} rows affected."
    finally:
        connection.close()