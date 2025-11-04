import os
import time
import json
from dotenv import load_dotenv
from langchain_aws import ChatBedrock
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage

# Import our League of Legends tools
from league_tools import TOOL_DEFINITIONS, execute_tool

# TODO: RAG Implementation
# 1. Add vector DB client (AWS OpenSearch / FAISS)
# 2. Add embedding model (Bedrock Titan Embeddings)
# 3. Add retrieval functions (semantic search for past conversations & coaching knowledge)

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

TOOLS AVAILABLE:
You have access to a League of Legends database with:
- Champion stats, abilities, and full details (FULLY IMPLEMENTED)
- All items and their stats (FULLY IMPLEMENTED)
- Rune details and trees (FULLY IMPLEMENTED)
- Recommended builds - items + runes for champion/role (NOT YET FULLY IMPLEMENTED - data may be incomplete)
- Champion counters and matchup info (NOT YET FULLY IMPLEMENTED - data may be incomplete)

When asked about builds or counters, you can try using the tools, but if the data is missing or incomplete,
provide your best general advice based on champion/item knowledge and mention the feature is still being built.

CORE PRINCIPLES:
1. Keep answers short and precise - go straight to the point
2. Only help when asked - don't force advice on anyone
3. You are allowed to contradict a player if they're being counterproductive about improvement
4. Remember: You help players get better, not feel better
5. Use your tools to provide accurate, data-backed advice

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
    # Bind the League of Legends tools to the chat model
    chat_with_tools = chat.bind(tools=TOOL_DEFINITIONS)
    return chat_with_tools

def chat_loop():
    print("Rift Rewind AI Chat")
    print("=" * 50)
    print("Type 'quit' to exit\n")
    # Create the chat model
    print("Connecting to AWS Bedrock...")
    chat = create_chat()
    print("Connected! Start chatting:\n")
    # Our "memory" is just a list of messages
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

            # TODO: RAG - Retrieve relevant context before invoking Claude
            # 1. Embed user_input query
            # 2. Search vector DB for similar past conversations/coaching tips
            # 3. Inject top-k relevant contexts into messages (as SystemMessage or HumanMessage)

            # Tool use loop - continue until we get a final response
            while True:
                # Get AI response with retry logic
                max_retries = 5
                for attempt in range(max_retries):
                    try:
                        response = chat.invoke(messages)
                        break
                    except Exception as retry_error:
                        error_str = str(retry_error)
                        # Check for rate limiting / throttling errors
                        is_rate_limit = any(keyword in error_str for keyword in [
                            "Too many requests",
                            "Too many connections",
                            "ThrottlingException",
                            "throttling"
                        ])
                        if is_rate_limit and attempt < max_retries - 1:
                            wait_time = (2 ** attempt) * 2
                            print(f"\nRate limited. Waiting {wait_time}s before retry...")
                            time.sleep(wait_time)
                        else:
                            raise

                # Add AI response to history
                messages.append(response)

                # Check if Claude wants to use tools
                if hasattr(response, 'tool_calls') and response.tool_calls:
                    # Claude is requesting tool use
                    num_tools = len(response.tool_calls)
                    for tool_call in response.tool_calls:
                        tool_name = tool_call['name']
                        tool_input = tool_call['args']
                        tool_use_id = tool_call['id']
                        print(f"[Tool Use: {tool_name}({json.dumps(tool_input)})]")
                        # Execute the tool
                        tool_result = execute_tool(tool_name, tool_input)
                        # Add tool result to messages
                        messages.append(ToolMessage(
                            content=json.dumps(tool_result, indent=2),
                            tool_call_id=tool_use_id
                        ))
                    # If Claude used many tools, add a small delay to avoid rate limiting
                    if num_tools > 3:
                        print(f"[Executed {num_tools} tools, brief pause to avoid rate limits...]")
                        time.sleep(1)
                    # Continue loop to get Claude's response after using tools
                    continue
                else:
                    # No more tool calls send response
                    print(f"\nAI: {response.content}\n")
                    break

        except Exception as e:
            print(f"\nError: {e}\n")
            # Remove the failed user message
            if isinstance(messages[-1], HumanMessage):
                messages.pop()

if __name__ == "__main__":
    chat_loop()
