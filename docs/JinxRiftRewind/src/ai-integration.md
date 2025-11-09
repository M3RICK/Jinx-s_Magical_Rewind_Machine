# AI Integration

**How RiftRewind Leverages AI for Personalized Coaching and Content Generation**

## Overview

RiftRewind uses Claude Sonnet 4.5 via AWS Bedrock for three core AI features:
1. **Personalized Coaching** - Interactive AI chat with conversation memory
2. **Zone Story Generation** - Map-based feedback narratives
3. **Player Card Content** - Custom titles and descriptions

All AI functionality is powered by Anthropic's Claude Sonnet 4.5, accessed through AWS Bedrock for serverless, scalable inference.

## AI Model: Claude Sonnet 4.5

**Model ID:** `eu.anthropic.claude-sonnet-4-5-20250929-v1:0`

**Key Capabilities:**
- **Long Context Window** - Handles entire conversation histories
- **Tool Calling** - Executes functions to query game data
- **Natural Language** - Conversational and engaging responses
- **Personalization** - Adapts to player skill level and preferences
- **Mode Awareness** - Switches between professional and roast tones

**Inference:** AWS Bedrock (no self-hosting required)

**Region:** EU-West-3 (configurable via environment variable)

## Architecture

### LangChain Integration

RiftRewind uses LangChain as the AI application framework:

**Libraries:**
- `langchain-aws` - AWS Bedrock integration
- `langchain-core` - Message abstractions and tool calling

**Benefits:**
- Standardized message format (System, Human, AI, Tool)
- Tool calling abstraction
- Easy model swapping if needed
- Streaming support (future)

### Connection Setup

```python
from langchain_aws import ChatBedrock

def create_chat():
    chat = ChatBedrock(
        model_id="eu.anthropic.claude-sonnet-4-5-20250929-v1:0",
        region_name=os.getenv('AWS_DEFAULT_REGION', 'eu-west-3'),
        model_kwargs={
            "temperature": 0.7,      # Balance creativity and consistency
            "max_tokens": 4092       # Max response length
        }
    )
    return chat
```

**Temperature:** 0.7 provides a balance between creative responses and consistent advice

**Max Tokens:** 4092 allows for detailed explanations without cutting off

## Feature 1: AI Coaching Chat

### System Prompt

The AI coach is guided by a detailed system prompt (ai_chat.py:22-57):

**Key Instructions:**
- Primary role: League of Legends coach
- Secondary role: Website assistant
- Keep answers short and precise
- Only help when asked (no unsolicited advice)
- Allowed to contradict counterproductive strategies
- Remember each player and their preferences
- Handle off-topic questions with redirection

**Tone Guidelines:**
- Direct and concise
- No corporate politeness
- Use gaming terminology
- Challenge bad decisions respectfully
- Focus on actionable improvements

### Tool Calling System

Claude can invoke functions to query game data and player statistics:

**Available Tools (league_tools.py):**

```python
TOOL_DEFINITIONS = [
    {
        "name": "search_champions",
        "description": "Search for League champions by name or role",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Champion name"},
                "role": {"type": "string", "description": "Role (Marksman, Fighter, etc.)"}
            }
        }
    },
    {
        "name": "get_champion_details",
        "description": "Get detailed information about a specific champion",
        "input_schema": {
            "type": "object",
            "properties": {
                "champion_name": {"type": "string"}
            },
            "required": ["champion_name"]
        }
    },
    {
        "name": "search_items",
        "description": "Search for items by name or tags",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "tags": {"type": "array", "items": {"type": "string"}}
            }
        }
    },
    {
        "name": "get_recommended_build",
        "description": "Get optimal item and rune build for champion/role",
        "input_schema": {
            "type": "object",
            "properties": {
                "champion": {"type": "string"},
                "role": {"type": "string"}
            },
            "required": ["champion"]
        }
    },
    {
        "name": "get_champion_counters",
        "description": "Get matchup information and counters",
        "input_schema": {
            "type": "object",
            "properties": {
                "champion": {"type": "string"},
                "lane": {"type": "string"}
            },
            "required": ["champion"]
        }
    },
    {
        "name": "get_player_match_history",
        "description": "Get recent match history for current player",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "default": 20}
            }
        }
    }
]
```

### Tool Execution Flow

```
1. User asks: "How do I build Jinx?"
2. Claude decides to call get_recommended_build tool
3. Backend receives tool call request:
   {
     "name": "get_recommended_build",
     "input": {"champion": "Jinx", "role": "ADC"}
   }
4. execute_tool() function queries SQLite database
5. Returns build data:
   {
     "items": ["Berserker's Greaves", "Kraken Slayer", ...],
     "runes": {"primary": "Precision", "keystone": "Lethal Tempo"},
     "skill_order": "Q>W>E"
   }
6. Tool result sent back to Claude via ToolMessage
7. Claude formats response with build information
8. User receives natural language response with build details
```

### Conversation Memory

**Storage:** DynamoDB Conversations table

**Retrieval:** On session start, load all previous messages

**Message Format:**
```python
messages = [
    SystemMessage(content=SYSTEM_PROMPT),
    HumanMessage(content="How do I play Yasuo?"),
    AIMessage(content="Yasuo is a high-skill..."),
    ToolMessage(
        tool_call_id="call_123",
        content="Champion details: {...}"
    ),
    AIMessage(content="Based on the data...")
]
```

**Benefits:**
- Claude remembers previous advice given
- Can reference past conversations
- Builds relationship over time
- Doesn't repeat information
- Tracks player progress

### Error Handling and Retry Logic

**Rate Limiting:** Exponential backoff for AWS Bedrock rate limits

```python
max_retries = 3
for attempt in range(max_retries):
    try:
        response = chat.invoke(messages)
        break
    except Exception as retry_error:
        if "Too many connections" in str(retry_error):
            wait_time = 2 ** attempt  # 1s, 2s, 4s
            time.sleep(wait_time)
```

**Conversation Persistence:** Messages saved to DynamoDB after each exchange

**Failure Recovery:** If AI call fails, user message is removed from history

## Feature 2: Zone Story Generation

### Purpose

Generate personalized feedback for each map zone based on player performance.

**Zones:**
- Top Lane
- Mid Lane
- Bottom Lane
- Jungle
- Dragon Pit
- Baron Nashor
- River

### Input Data

**Player Statistics (from zone_analyzer.py):**
```python
zone_stats = {
    "zone_id": "top_lane",
    "games_played": 15,
    "win_rate": 0.53,
    "kills": 42,
    "deaths": 38,
    "assists": 51,
    "avg_cs_at_10": 72,
    "avg_damage_dealt": 18500,
    "most_played_champions": ["Darius", "Garen", "Sett"]
}
```

### Story Generation Prompt

```python
prompt = f"""Generate a {mode} mode coaching story for {zone_name}.

Player Stats:
- Win Rate: {stats['win_rate']*100:.1f}%
- KDA: {stats['kda']}
- Average CS@10: {stats['cs_10']}
- Most Played: {stats['champions']}

{mode} Mode Guidelines:
{'Coach Mode: Professional, constructive, encouraging'
 if mode == 'coach' else
 'Roast Mode: Brutal honesty with humor, still educational'}

Provide 2-3 concise paragraphs focusing on:
1. Notable strengths
2. Key weaknesses
3. Actionable advice for improvement"""
```

**Response:** Natural language narrative tailored to player's performance

### Caching Strategy

**Cache Location:** DynamoDB MapStories table

**Cache Key:** `puuid + zone_id + mode`

**TTL:** 24 hours

**Invalidation:** Regenerate when new matches are added

**Cost Savings:** Reduces AI API calls by ~90% for returning users

## Feature 3: Player Card Generation

### Purpose

Create custom titles and descriptions for shareable player cards.

### Input Data

```python
player_data = {
    "summoner_name": "sad and bad",
    "level": 150,
    "rank": "PLATINUM II",
    "most_played_champion": "Jinx",
    "playstyle_stats": {
        "aggression": 0.73,     # High early game aggression
        "teamfight": 0.82,      # Strong in teamfights
        "objective": 0.65,      # Moderate objective focus
        "solo": 0.41           # Prefers team play
    },
    "mode": "coach"  # or "roast"
}
```

### Title and Description Prompt

```python
prompt = f"""Generate a player title and description for {summoner_name}.

Stats:
- Main Champion: {champion}
- Rank: {rank}
- Playstyle: {get_playstyle_summary(stats)}

Create:
1. A title (3-5 words, dramatic and fitting)
2. A description (2-3 sentences, capturing their playstyle)

{mode} mode tone: {'Professional and empowering'
                   if mode == 'coach' else
                   'Sarcastic but entertaining'}"""
```

**Example Output (Coach Mode):**
```json
{
    "title": "The Calculated Marksman",
    "description": "A patient ADC who excels in teamfights and knows when to scale. Focuses on farm and smart positioning over risky plays."
}
```

**Example Output (Roast Mode):**
```json
{
    "title": "The 'I'll Scale' Excuse Master",
    "description": "Farms all game then wonders why the team is down 3 turrets. At least you'll be relevant at 30 minutes... if we make it that far."
}
```

### Integration with Image Generation

**Flow:**
1. AI generates title + description
2. Pillow renders card with champion background
3. Overlays text with custom fonts
4. Encodes as base64 PNG
5. Sends to frontend for display

## Performance Optimizations

### Token Usage Optimization

**Concise Prompts:** Focus on essential context only

**Structured Output:** Request specific formats to reduce tokens

**Context Pruning:** Summarize very old conversations (planned)

### Caching

**Story Caching:** 24h TTL reduces repeat generation

**Player Card Caching:** Store in PlayerTitles table

**Conversation Windowing:** Keep last N messages only (planned)

### Parallel Processing

**Batch Zone Stories:** Generate all zones in parallel (planned)

**Async Calls:** Use asyncio for concurrent requests (planned)

## Cost Management

**Estimated Costs:**
- **Claude API:** $50-100/month for 100 daily active users
- **Per Request:** ~$0.01-0.03 per chat exchange
- **Story Generation:** ~$0.05-0.10 per map (8 zones)
- **Player Cards:** ~$0.02 per generation

**Cost Reduction Strategies:**
- Aggressive caching (24h for stories)
- Efficient prompts (fewer tokens)
- Tool calling reduces back-and-forth
- Batch operations where possible

## Future Enhancements

### RAG Implementation (Planned)

**Goal:** Improve coaching quality with knowledge retrieval

**Components:**
```python
# 1. Vector Database
vector_db = FAISSVectorStore()  # or AWS OpenSearch

# 2. Embedding Model
embeddings = BedrockEmbeddings(model_id="amazon.titan-embed-text-v1")

# 3. Knowledge Base
knowledge = [
    "Advanced wave management techniques",
    "Jungle pathing optimization",
    "Team composition strategies",
    # ... coaching content
]

# 4. Retrieval
relevant_docs = vector_db.similarity_search(query, k=3)

# 5. Enhanced Prompt
prompt = f"""Context: {relevant_docs}
User Question: {query}
Previous Conversation: {history}"""
```

**Benefits:**
- Access to curated coaching knowledge
- More consistent advice
- Reference specific strategies
- Reduce hallucinations

### Streaming Responses (Future)

**LangChain Streaming:** Token-by-token response delivery

**WebSockets:** Real-time frontend updates

**Better UX:** Users see responses as they're generated

### Fine-Tuning (Future)

**Custom Model:** Train on League coaching conversations

**Domain Expertise:** Deeper game knowledge

**Personalization:** Per-player fine-tuning (advanced)

## Security and Privacy

**Prompt Injection Prevention:**
- System prompt clearly defines boundaries
- User input sanitization
- Role-based message separation

**Data Privacy:**
- Conversations stored per-player only
- No cross-player data sharing
- PUUID-based isolation

**Rate Limiting:**
- Per-session request limits
- Exponential backoff for retries
- Prevent abuse and cost overruns

## Monitoring and Debugging

**Logging:**
- All AI requests logged with timestamps
- Token usage tracked
- Error rates monitored

**Metrics to Track:**
- Average response time
- Token usage per request
- Cache hit rates
- User satisfaction (feedback system planned)

**Cost Tracking:**
- Daily AI API spend
- Per-feature cost breakdown
- Optimization opportunities

## Why Claude Sonnet 4.5?

**Advantages:**
- **Tool Calling** - Native function execution support
- **Long Context** - Handles full conversation history
- **Quality** - High-quality coaching responses
- **Personality** - Can adapt tone (coach vs roast mode)
- **AWS Integration** - Seamless Bedrock access

**Alternatives Considered:**
- **GPT-4** - Requires OpenAI API, similar cost
- **Claude 3 Opus** - More expensive, not needed for this use case
- **Claude 3.5 Haiku** - Cheaper but less capable for coaching

**Decision:** Sonnet 4.5 offers the best balance of quality, cost, and features for RiftRewind's needs.
