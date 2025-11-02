import os
from dotenv import load_dotenv
from langchain_aws import ChatBedrock
from langchain_core.messages import HumanMessage

load_dotenv()

USE_MOCK = os.getenv('USE_MOCK_AI', 'false').lower() == 'true'

if USE_MOCK:
    from .mock_client import generate_mock_story


def create_bedrock_client():
    return ChatBedrock(
        model_id="eu.anthropic.claude-sonnet-4-5-20250929-v1:0",
        region_name=os.getenv('AWS_DEFAULT_REGION', 'eu-west-3'),
        model_kwargs={
            "temperature": 0.8,
            "max_tokens": 500
        }
    )


def generate_story(prompt, zone_id=None):
    if USE_MOCK:
        print("[MOCK MODE] Using mock AI responses")
        return generate_mock_story(zone_id or "default")

    client = create_bedrock_client()
    message = HumanMessage(content=prompt)

    try:
        response = client.invoke([message])
        return response.content.strip()
    except Exception as e:
        print(f"Error generating story: {e}")
        return None
