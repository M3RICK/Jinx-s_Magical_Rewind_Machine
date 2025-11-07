import os
import time
from dotenv import load_dotenv
from langchain_aws import ChatBedrock
from langchain_core.messages import SystemMessage, HumanMessage

load_dotenv()

USE_MOCK = os.getenv('USE_MOCK_AI', 'false').lower() == 'true'

if USE_MOCK:
    from testing.mocks.mock_ai import generate_mock_story


# System prompt for zone story generation
STORY_SYSTEM_PROMPT = """You are a League of Legends coach generating brief, personalized feedback stories for players.

YOUR ROLE:
- Analyze player statistics for specific map zones
- Generate 2-3 sentence stories that are engaging and helpful
- Use second person ("You", "Your") to address the player directly
- Be concise but impactful

STORY MODES:
1. COACH MODE: Supportive, constructive, actionable advice
2. ROAST MODE: Savage, funny, brutal humor

OUTPUT FORMAT:
- Exactly 2-3 sentences
- Second person perspective
- Natural storytelling flow"""


def create_bedrock_client():
    """
    Create Bedrock client using the EXACT same pattern as ai_chat.py.
    This is the working implementation.
    """
    chat = ChatBedrock(
        model_id="eu.anthropic.claude-sonnet-4-5-20250929-v1:0",  # Same as ai_chat.py
        region_name=os.getenv('AWS_DEFAULT_REGION', 'eu-west-3'),
        model_kwargs={
            "temperature": 0.7,
            "max_tokens": 4092
        }
    )
    return chat


def generate_story(prompt, zone_id=None, mode='coach'):
    """
    Generate zone story using the EXACT same logic as ai_chat.py.
    This matches the working chat implementation.
    """
    if USE_MOCK:
        print(f"[MOCK MODE] Using mock AI responses in {mode.upper()} mode")
        return generate_mock_story(zone_id or "default", mode=mode)

    # Create chat using the same function as ai_chat.py
    chat = create_bedrock_client()

    # Build messages array (same pattern as ai_chat.py)
    messages = [
        SystemMessage(content=STORY_SYSTEM_PROMPT),
        HumanMessage(content=prompt)
    ]

    # Use EXACT same retry logic as ai_chat.py
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Invoke with messages (same as ai_chat.py line 98)
            response = chat.invoke(messages)

            # Return the content (same as ai_chat.py line 109)
            return response.content.strip()

        except Exception as retry_error:
            # Same error handling as ai_chat.py (lines 100-106)
            if "Too many connections" in str(retry_error) and attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                print(f"\nRate limited. Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
            else:
                # Failed permanently
                print(f"   ERROR: Error generating story: {retry_error}")
                return None

    return None
