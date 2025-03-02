# Executes and validates SQL queries
import sqlparse
from db.rdbms_connector import connect_to_rdbms
from db.nosql_connector import connect_to_nosql

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


def execute_nosql(nosql_query: str):
    """
    执行 MongoDB 查询。
    参数 nosql_query 预期为一个可以在 MongoDB 上执行的 Python 表达式字符串，
    例如："db['students'].find({'name': 'Alice'})"。

    注意：这里使用 eval 执行查询，请确保查询内容受信任。
    """
    db = connect_to_nosql()["student"]
    try:
        # 在安全上下文中执行查询，提供 db 变量供表达式使用
        result = eval(nosql_query, {"db": db})
        # 如果返回的是 pymongo Cursor，则转换为列表
        if hasattr(result, "sort") or hasattr(result, "batch_size"):
            result = list(result)
        return result
    except Exception as e:
        return f"Error executing nosql query: {str(e)}"