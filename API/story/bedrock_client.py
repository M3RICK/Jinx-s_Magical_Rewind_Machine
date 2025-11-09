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
- ALWAYS include actionable advice, even when roasting

TONE MODES:
- Coach tone: Supportive, encouraging, constructive advice with positive framing
- Roast tone: Savage, funny, brutally honest humor BUT still includes useful tips and actionable advice
  * The roast should hurt because it's TRUE
  * Follow up the burn with what they should actually do to improve
  * Think: "You're trash at this... here's how to fix it"

OUTPUT FORMAT:
- Exactly 2-3 sentences
- Second person perspective
- Natural storytelling flow
- DO NOT include mode labels like "COACH MODE:" or "ROAST MODE:" in your response
- Start directly with the story content
- End with actionable advice (what they should actually DO to improve)"""


def create_bedrock_client():
    """
    Create Bedrock client for story generation.
    """
    chat = ChatBedrock(
        model_id="eu.anthropic.claude-sonnet-4-5-20250929-v1:0",
        region_name=os.getenv('AWS_DEFAULT_REGION', 'eu-west-3'),
        model_kwargs={
            "temperature": 0.7,
            "max_tokens": 4092
        }
    )
    return chat


def generate_story(prompt, zone_id=None, mode='coach'):
    """
    Generate zone story using Bedrock AI.
    """
    if USE_MOCK:
        print(f"[MOCK MODE] Using mock AI responses in {mode.upper()} mode")
        return generate_mock_story(zone_id or "default", mode=mode)

    chat = create_bedrock_client()

    messages = [
        SystemMessage(content=STORY_SYSTEM_PROMPT),
        HumanMessage(content=prompt)
    ]

    max_retries = 5
    for attempt in range(max_retries):
        try:
            response = chat.invoke(messages)
            return response.content.strip()

        except Exception as retry_error:
            error_str = str(retry_error)

            # Check for rate limiting errors
            is_rate_limit = any(keyword in error_str.lower() for keyword in [
                "too many requests",
                "too many connections",
                "throttlingexception",
                "throttling",
                "rate limit"
            ])

            if is_rate_limit and attempt < max_retries - 1:
                wait_time = (2 ** attempt) * 2
                print(f"Rate limited. Waiting {wait_time}s before retry (attempt {attempt + 1}/{max_retries})...")
                time.sleep(wait_time)
            else:
                print(f"ERROR: AI story generation failed for zone {zone_id}")
                print(f"Error type: {type(retry_error).__name__}")
                print(f"Error message: {error_str}")

                if is_rate_limit:
                    print("RATE LIMIT ERROR - User should wait before retrying")
                    raise Exception("RATE_LIMIT_ERROR: Too many requests to AI service. Please wait a moment and try again.")

                import traceback
                traceback.print_exc()
                return None

    print(f"ERROR: AI story generation failed after {max_retries} retries for zone {zone_id}")
    raise Exception("RATE_LIMIT_ERROR: Too many requests to AI service. Please wait a moment and try again.")
