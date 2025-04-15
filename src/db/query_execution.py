# Executes and validates SQL queries
import sqlparse

from db.nosql_connector import connect_to_nosql
from db.postgres_connector import connect_to_postgres
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


def execute_postgres(query: str):
    """Executes a PostgreSQL query."""
    print("Executing PostgreSQL query:", query)
    connection = connect_to_postgres()
    try:
        with connection.cursor() as cursor:
            cursor.execute(query)
            if query.strip().upper().startswith('SELECT'):
                results = cursor.fetchall()
                print("Query results:", results)
                return results
            else:
                connection.commit()
                return f"{cursor.rowcount} rows affected."
    except Exception as e:
        print("Error executing PostgreSQL query:", str(e))
        raise
    finally:
        connection.close()


def execute_nosql(nosql_query: str):
    """
    执行 MongoDB 查询。
    参数 nosql_query 预期为一个可以在 MongoDB 上执行的 Python 表达式字符串，
    例如："db['students'].find({'name': 'Alice'})"。

    注意：这里使用 eval 执行查询，请确保查询内容受信任。
    """
    print("Executing MongoDB query:", nosql_query)
    db = connect_to_nosql()  # Already returns the database object
    try:
        # 在安全上下文中执行查询，提供 db 变量供表达式使用
        result = eval(nosql_query, {"db": db})
        # 如果返回的是 pymongo Cursor，则转换为列表
        if hasattr(result, "sort") or hasattr(result, "batch_size"):
            result = list(result)
        print("MongoDB query result:", result)
        return result
    except Exception as e:
        error_msg = f"Error executing MongoDB query: {str(e)}"
        print(error_msg)
        return error_msg