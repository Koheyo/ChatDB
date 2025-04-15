# Handles MongoDB database connection
from pymongo import MongoClient


def connect_to_nosql():
    """Establishes a connection to a NoSQL database."""
    try:
        client = MongoClient("mongodb://localhost:27017/")
        # Test the connection
        client.server_info()
        db = client["world"]  # Use the existing database
        
        # Debug: Print available collections
        collections = db.list_collection_names()
        print("Available collections:", collections)
        
        return db
    except Exception as e:
        print(f"Error connecting to MongoDB: {str(e)}")
        raise
