import json

from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['sales']

# Import customers
with open('customers.json', 'r') as f:
    customers_data = json.load(f)
    if customers_data:
        db.customers.insert_many(customers_data)
        print(f"Successfully imported {len(customers_data)} customers")

# Import orders
with open('orders.json', 'r') as f:
    orders_data = json.load(f)
    if orders_data:
        db.orders.insert_many(orders_data)
        print(f"Successfully imported {len(orders_data)} orders")

# Import products
with open('products.json', 'r') as f:
    products_data = json.load(f)
    if products_data:
        db.products.insert_many(products_data)
        print(f"Successfully imported {len(products_data)} products")

print("Data import completed!")