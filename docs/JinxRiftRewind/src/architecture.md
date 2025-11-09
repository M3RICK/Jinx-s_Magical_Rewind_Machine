# Architecture Overview

**System Design and Component Interaction**

## High-Level Architecture

RiftRewind follows a three-tier architecture with a Python/Flask backend, static HTML/JS frontend, and dual-database system for static and dynamic data.

```
┌─────────────────────────────────────────────────────────────┐
│                         User Browser                        │
│                  (HTML/CSS/JavaScript)                      │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP/REST API
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                     Flask Application                       │
│                      (Python 3.12)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐      │
│  │ API Routes   │  │  AI Chat     │  │ Image Gen     │      │
│  │ main.py      │  │  ai_chat.py  │  │ image_creation│      │
│  └──────────────┘  └──────────────┘  └───────────────┘      │
└──────┬───────────────────┬─────────────────┬────────────────┘
       │                   │                 │
       │                   │                 │
┌──────▼────────┐  ┌───────▼─────────┐  ┌────▼─────────────┐
│  Riot API     │  │   AWS Services  │  │  SQLite DB       │
│  (Pulsefire)  │  │   DynamoDB      │  │  (Static Data)   │
│               │  │   Bedrock AI    │  │  league_data.db  │
└───────────────┘  └─────────────────┘  └──────────────────┘
```

## Core Components

### 1. Frontend Layer

**Technology:** Vanilla HTML, CSS, JavaScript
**Location:** `/app/frontend/public/`

The frontend consists of three main pages:

- **index.html** - Landing page with summoner authentication and mode selection
- **interactive_map.html** - Interactive Summoner's Rift map with zone-based feedback
- **coaching_session.html** - AI coaching chat interface with match history sidebar

All frontend assets are served statically by Flask from the public folder.

### 2. Backend API Layer

**Technology:** Python 3.12 + Flask
**Location:** `/app/backend/src/`

The Flask application handles all server-side logic:

**Main API Server (main.py:39)**
- Flask app initialization and routing
- Request validation and sanitization
- Async operations wrapper for Python's asyncio
- Static file serving

**Key Endpoints:**
- `/api/authenticate` - Player authentication via Riot ID
- `/api/generate_map` - Generate zone analysis and stories
- `/api/coach` - AI coaching chat with conversation memory
- `/api/player_card` - Generate shareable player cards
- `/api/profile` - Fetch player profile and match history
- `/health` - Health check endpoint

**AI Integration (ai_chat.py)**
- Claude Sonnet 4.5 integration via AWS Bedrock
- Conversation history management
- Tool calling for League data queries
- Player-specific context loading

**Image Generation (image_creation.py)**
- Pillow-based card generation
- Custom font rendering (Teko font family)
- Champion art composition
- Base64 encoding for web delivery

**League Tools (league_tools.py:14)**
- SQLite query interface for champions, items, runes
- Tool definitions for AI function calling
- Player match history access

### 3. Data Processing Layer

**Location:** `/API/`

This module handles Riot API integration and data analysis:

**Player Model (API/models/player.py)**
- Riot API calls via Pulsefire library
- Match history loading (up to 20 matches)
- Timeline data processing
- Statistics aggregation

**Zone Analysis (API/analytics/zones/)**
- Map zone performance breakdown
- Per-zone statistics calculation
- Heatmap data generation

**Story Generation (API/story/)**
- AI-powered narrative generation for zones
- Card content generation with fallback
- Mode-aware storytelling (Coach vs Roast)

### 4. Database Layer

**Location:** `/db/src/`

RiftRewind uses a dual-database approach:

**SQLite (league_data.db:14)**
- **Purpose:** Static League of Legends game data
- **Update Frequency:** Bi-weekly (aligned with patches)
- **Tables:**
  - `champions` - All champion data (stats, abilities, roles)
  - `items` - Item stats and build paths
  - `runes` - Rune configurations
  - `recommended_builds` - Meta builds per champion
  - `champion_counters` - Matchup data

**AWS DynamoDB**
- **Purpose:** Dynamic player data and user state
- **Tables:**
  - `Players` - Player profiles (PUUID, rank, main champions)
  - `MatchHistory` - Last 20 matches per player
  - `Conversations` - AI chat history per player
  - `Sessions` - Authentication session tokens
  - `MapStories` - Generated zone stories (cached)
  - `PlayerTitles` - Generated player titles and cards

**Repository Pattern (db/src/repositories/)**
- `PlayerRepository` - Player CRUD operations
- `SessionRepository` - Session management
- `ConversationRepository` - Chat history persistence

## Data Flow

### User Authentication Flow

```
1. User enters summoner name#tag + region
2. Frontend → POST /api/authenticate
3. Backend → Riot API (via Pulsefire)
4. Fetch player PUUID and basic profile
5. Store/update player in DynamoDB Players table
6. Generate session token
7. Store session in DynamoDB Sessions table
8. Return session token to frontend
9. Frontend stores token for subsequent requests
```

### Interactive Map Flow

```
1. User navigates to map
2. Frontend → POST /api/generate_map (with session token)
3. Backend validates session
4. Check if stories exist in MapStories (DynamoDB)
5. If fresh (< 24h), return cached stories
6. If stale/missing:
   a. Fetch match history from DynamoDB
   b. Analyze zones using API/analytics
   c. Generate AI stories with Claude
   d. Cache in MapStories table
7. Return zone data + stories to frontend
8. Frontend renders clickable map zones
9. User clicks zone → display story
```

### AI Coaching Flow

```
1. User opens coaching interface
2. Frontend → GET /api/profile (load match history sidebar)
3. User sends message
4. Frontend → POST /api/coach
5. Backend:
   a. Load conversation history from DynamoDB
   b. Set player PUUID for tool context
   c. Send to Claude with:
      - System prompt
      - Conversation history
      - Tool definitions (SQLite queries)
      - Player context
   d. Claude may call tools (search champions, get builds, etc.)
   e. Execute tools against SQLite DB
   f. Return results to Claude
   g. Claude generates response
   h. Save conversation to DynamoDB
6. Return response to frontend
7. Display in chat interface
```

### Player Card Generation Flow

```
1. User completes map analysis
2. Frontend → POST /api/player_card
3. Backend:
   a. Fetch player data from DynamoDB
   b. Get most-played champion
   c. Generate title + description via AI
   d. Render card with Pillow:
      - Champion background
      - Player name + rank + level
      - Generated title
      - Description text
   e. Encode as base64 PNG
4. Return image data to frontend
5. Frontend displays card for sharing
```

## Deployment Architecture

### Docker Containerization

**Dockerfile Configuration:**
- Base image: Python 3.12-slim
- System dependencies: gcc, curl, fontconfig, freetype
- Custom fonts: Teko font family copied to container
- Application structure: API, db, app folders
- Port: 5000 (Flask)
- Health check: HTTP GET /health every 30s

### AWS Elastic Beanstalk

**Deployment:**
- Docker single-container environment
- Environment variables:
  - `AWS_REGION` - AWS region for DynamoDB/Bedrock
  - `RIOT_API_KEY` - Riot Games API authentication
  - `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` - AWS credentials
- Port mapping: 80 (external) → 5000 (Flask)
- Auto-scaling: Elastic Beanstalk managed
- Health monitoring: Based on /health endpoint

**Future Considerations:**
- Custom domain via AWS Route 53 (planned)
- CloudFront CDN for static assets (potential)
- Multi-container setup for scaling (future)

## Security Considerations

**Input Validation:**
- All user inputs sanitized (app/backend/src/utils/input_validator.py)
- Riot ID format validation
- Platform whitelist enforcement
- Request size limits (10KB max)

**Authentication:**
- Session token-based auth
- PUUID-based player identification
- No password storage required (Riot API validation)

**API Rate Limiting:**
- Riot API rate limits respected via Pulsefire
- Story caching reduces AI API calls

## Performance Optimizations

**Caching Strategy:**
- Zone stories cached in DynamoDB (24h TTL)
- Static League data in SQLite (no network calls)
- Match history stored locally (reduces Riot API calls)

**Async Operations:**
- Pulsefire uses aiohttp for async Riot API calls
- Flask wraps async calls in event loop

**Database Indexing:**
- DynamoDB: Global/Local secondary indexes for fast queries
- SQLite: Primary keys on champion_id, item_id, etc.

## Scalability

Current architecture supports:
- Multiple concurrent users (Flask + Elastic Beanstalk)
- DynamoDB auto-scaling for storage
- Stateless backend (sessions in DB, not memory)

Future scaling paths:
- Add Redis for session caching
- Implement CDN for static assets
- Separate AI service (microservices approach)
- Add load balancer for multi-instance deployment
