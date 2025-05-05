import json

from pymongo import MongoClient

# 连接到MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['sales']

# 导入customers数据
with open('src/databases/mangodb/customers.json', 'r') as f:
    customers_data = json.load(f)
    if customers_data:
        db.customers.insert_many(customers_data)
        print(f"Successfully imported {len(customers_data)} customers")

# 导入orders数据
with open('src/databases/mangodb/orders.json', 'r') as f:
    orders_data = json.load(f)
    if orders_data:
        db.orders.insert_many(orders_data)
        print(f"Successfully imported {len(orders_data)} orders")

# 导入products数据
with open('src/databases/mangodb/products.json', 'r') as f:
    products_data = json.load(f)
    if products_data:
        db.products.insert_many(products_data)
        print(f"Successfully imported {len(products_data)} products")

print("Data import completed!") 