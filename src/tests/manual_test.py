# src/tests/manual_test.py
from llm.query_processing import generate_query, extract_sql_from_response
from db.query_execution import execute_sql,execute_nosql
from db.nosql_connector import connect_to_nosql

# 测试 SQL 查询
print("====== 测试 SQL 查询 ======")
user_input = "查询学生姓名"
query_type, sql_query = generate_query(user_input, db_type="sql")
if query_type.upper() == "SQL":
    sql_query = extract_sql_from_response(sql_query)

print("生成的 SQL 命令:")
print(sql_query)

if query_type.upper() == "SQL":
    result = execute_sql(sql_query)
    print("执行结果:", result)
elif query_type.upper() == "NOSQL":
    result=execute_nosql(sql_query)
    print("NoSQL执行结果:", result)
else:
    print("SQL 语句无效！")