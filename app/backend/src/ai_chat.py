import os
import time
from dotenv import load_dotenv
from langchain_aws import ChatBedrock
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

load_dotenv()

SYSTEM_PROMPT = """You are the AI chatbot for the RiftRewind website.

YOUR ROLE:
You are primarily a League of Legends coach, and secondarily a website assistant.

PRIMARY FUNCTION - League of Legends Coach:
- Analyze player gameplay statistics
- Compare player performance to improvement benchmarks
- Provide actionable advice for climbing ranked
- Remember each player and their preferences, adapting your answers accordingly
- Challenge players if they request assistance but pursue counterproductive strategies

SECONDARY FUNCTION - Website Assistant:
- Help users navigate the RiftRewind website
- Answer questions about features and functionality

CORE PRINCIPLES:
1. Keep answers short and precise - go straight to the point
2. Only help when asked - don't force advice on anyone
3. You are allowed to contradict a player if they're being counterproductive about improvement
4. Remember: You help players get better, not feel better

OFF-TOPIC QUESTIONS:
If someone asks about topics unrelated to League of Legends or the website, respond with:
"[Brief answer]. However, I am RiftRewind's personal AI coach. If you have any questions regarding League of Legends or how to improve, please ask. I won't respond to further off-topic questions."

Example:
Q: "How much is Bitcoin today?"
A: "Bitcoin is around $X. However, I am RiftRewind's personal AI coach. If you have any questions regarding League of Legends or how to improve, please ask. I won't respond to further off-topic questions."

RESPONSE STYLE:
- Direct and concise
- No corporate politeness - be real
- Use gaming terms when appropriate
- Challenge bad decisions respectfully
- Focus on actionable improvements"""


def create_chat():
    chat = ChatBedrock(
        model_id="eu.anthropic.claude-sonnet-4-5-20250929-v1:0",
        region_name=os.getenv('AWS_DEFAULT_REGION', 'eu-west-3'),
        model_kwargs={
            "temperature": 0.7,
            "max_tokens": 4092
        }
    )
    return chat

def chat_loop():
    print("Rift Rewind AI Chat")
    print("=" * 50)
    print("Type 'quit' to exit\n")
    # Create the chat model
    print("Connecting to AWS Bedrock...")
    chat = create_chat()
    print("Connected! Start chatting:\n")
    messages = [SystemMessage(content=SYSTEM_PROMPT)]

    while True:
        # Get user input
        user_input = input("You: ").strip()
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("\nGoodbye!")
            break
        if not user_input:
            continue

        try:
            # Add user message to history
            messages.append(HumanMessage(content=user_input))

            # Get AI response with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = chat.invoke(messages)
                    break
                except Exception as retry_error:
                    if "Too many connections" in str(retry_error) and attempt < max_retries - 1:
                        wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                        print(f"\nRate limited. Waiting {wait_time}s before retry...")
                        time.sleep(wait_time)
                    else:
                        raise

            # Add AI response to history
            messages.append(AIMessage(content=response.content))
            # Print response
            print(f"\nAI: {response.content}\n")

        except Exception as e:
            print(f"\nError: {e}\n")
            # Remove the failed user message
            if isinstance(messages[-1], HumanMessage):
                messages.pop()

if __name__ == "__main__":
    chat_loop()
