from openai import AzureOpenAI
from config import get_config

config = get_config()

# Initialize Azure OpenAI client
client = AzureOpenAI(
    azure_endpoint=config["ENDPOINT_URL"],
    api_key=config["LLM_API_KEY"],
    api_version="2024-05-01-preview",
)

def call_llm_api(messages: list) -> str:
    """Calls LLM API with the given messages."""
    response = client.chat.completions.create(
        model=config["DEPLOYMENT_NAME"],
        messages=messages
    )
    return response.choices[0].message.content