# Configuration file
import os

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
LLM_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
ENDPOINT_URL = os.getenv("ENDPOINT_URL")
DEPLOYMENT_NAME = os.getenv("DEPLOYMENT_NAME")

def get_config():
    """Returns the configuration settings."""
    return {
        "DATABASE_URL": DATABASE_URL,
        "LLM_API_KEY": LLM_API_KEY,
        "ENDPOINT_URL": ENDPOINT_URL,
        "DEPLOYMENT_NAME": DEPLOYMENT_NAME,
    } 