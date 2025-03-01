# Handles MongoDB database connection
from pymongo import MongoClient

def connect_to_nosql():
    """Establishes a connection to a NoSQL database."""
    return MongoClient("mongodb://localhost:27017/")
