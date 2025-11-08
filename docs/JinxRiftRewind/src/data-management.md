# Data Management

**How RiftRewind Stores, Processes, and Manages Player and Game Data**

## Static Data: SQLite Database

### Purpose and Scope

The SQLite database (`league_data.db`) stores all static League of Legends game information that changes infrequently (every 2 weeks with patches).

**Location:** `/app/data/league_data.db`

**Size:** Approximately 50-100 MB (entire League dataset)

**Access Pattern:** Read-only during runtime, write-only during patch updates

### Database Schema

#### Champions Table

Stores comprehensive champion information:

```sql
CREATE TABLE champions (
    champion_id TEXT PRIMARY KEY,      -- "Jinx", "MasterYi"
    champion_key INTEGER UNIQUE,       -- Numeric Riot API ID
    name TEXT NOT NULL,                -- Display name
    title TEXT,                        -- "The Loose Cannon"
    primary_role TEXT,                 -- "Marksman", "Fighter"
    secondary_role TEXT,
    tags TEXT,                         -- JSON array of roles
    difficulty INTEGER,                -- 1-10 scale
    hp REAL,
    hp_per_level REAL,
    mp REAL,
    mp_per_level REAL,
    armor REAL,
    armor_per_level REAL,
    attack_damage REAL,
    attack_damage_per_level REAL,
    attack_speed REAL,
    attack_speed_per_level REAL,
    move_speed REAL,
    -- Abilities stored as JSON text
    passive_ability TEXT,
    q_ability TEXT,
    w_ability TEXT,
    e_ability TEXT,
    r_ability TEXT
);
```

**Indexes:**
- Primary key on `champion_id`
- Unique index on `champion_key`
- Index on `primary_role` for role-based queries

#### Items Table

```sql
CREATE TABLE items (
    item_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    gold_total INTEGER,
    gold_base INTEGER,
    gold_sell INTEGER,
    stats TEXT,                -- JSON object
    tags TEXT,                 -- ["Damage", "CriticalStrike"]
    builds_from TEXT,          -- JSON array of item IDs
    builds_into TEXT           -- JSON array of item IDs
);
```

#### Runes Table

```sql
CREATE TABLE runes (
    rune_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    rune_tree TEXT,            -- "Precision", "Domination"
    tier INTEGER,              -- 0-3 (Keystone to minor)
    slot INTEGER,              -- Position in tree
    description TEXT,
    short_description TEXT
);
```

#### Recommended Builds Table

Pre-computed optimal builds per champion:

```sql
CREATE TABLE recommended_builds (
    build_id INTEGER PRIMARY KEY AUTOINCREMENT,
    champion_id TEXT,
    role TEXT,                 -- "ADC", "Top", "Mid"
    item_build TEXT,           -- JSON array of item IDs in order
    rune_build TEXT,           -- JSON object with rune selections
    skill_order TEXT,          -- "Q>E>W" or similar
    win_rate REAL,             -- Historical win rate
    sample_size INTEGER,       -- Games analyzed
    patch_version TEXT,
    FOREIGN KEY (champion_id) REFERENCES champions(champion_id)
);
```

#### Champion Counters Table

Matchup data:

```sql
CREATE TABLE champion_counters (
    matchup_id INTEGER PRIMARY KEY AUTOINCREMENT,
    champion_id TEXT,          -- Champion being played
    counter_id TEXT,           -- Enemy champion
    lane TEXT,                 -- "top", "mid", "bot"
    win_rate_against REAL,     -- Your win rate vs counter
    difficulty TEXT,           -- "Easy", "Medium", "Hard"
    tips TEXT,                 -- Matchup advice
    FOREIGN KEY (champion_id) REFERENCES champions(champion_id),
    FOREIGN KEY (counter_id) REFERENCES champions(champion_id)
);
```

### Data Update Process

**Frequency:** Every 2 weeks (aligned with League patch cycle)

**Process:**
1. Fetch latest Data Dragon from Riot
2. Parse JSON files for champions, items, runes
3. Transform into normalized SQL tables
4. Replace existing database or update changed rows
5. Run integrity checks
6. Deploy updated database with Docker image

**Automation:** Currently manual, planned for GitHub Actions automation

### Query Patterns

**AI Tool Queries (via league_tools.py):**

```python
# Search champions by name or role
search_champions(query="Jinx", role="Marksman")

# Get champion details
get_champion_details(champion_name="Jinx")

# Search items by name or tags
search_items(query="sword", tags=["Damage"])

# Get recommended build
get_recommended_build(champion="Jinx", role="ADC")

# Get champion counters
get_champion_counters(champion="Yasuo", lane="mid")
```

**Performance:** Average query time < 10ms (in-memory SQLite)

## Dynamic Data: AWS DynamoDB

### Purpose and Scope

DynamoDB stores all player-specific, session-specific, and generated content that changes frequently.

**Region:** Configured via environment variable (default: eu-west-3)

**Billing Mode:** On-demand (pay per request)

### Table Schemas

#### Players Table

Primary player profile data:

```
Partition Key: puuid (String)

Attributes:
- puuid: Player Universal Unique ID (from Riot API)
- riot_id: "name#tag" format
- region: "euw1", "na1", etc.
- summoner_level: Integer
- profile_icon_id: Integer
- current_rank: "GOLD II", "PLATINUM I"
- main_role: "ADC", "Support", etc.
- main_champions: JSON array of champion IDs
- total_games: Integer
- win_rate: Float (0.0-1.0)
- last_updated: ISO timestamp
- created_at: ISO timestamp

Global Secondary Index:
- RiotIdIndex: Allows lookup by riot_id
```

#### MatchHistory Table

Individual match records per player:

```
Partition Key: puuid (String)
Sort Key: match_id (String)

Attributes:
- puuid: Player UUID
- match_id: "EUW1_123456789"
- timestamp: Unix timestamp (Number)
- champion_id: String
- champion_name: String
- role: "ADC", "JUNGLE", etc.
- kills: Integer
- deaths: Integer
- assists: Integer
- cs: Integer
- gold_earned: Integer
- damage_dealt: Integer
- damage_taken: Integer
- vision_score: Integer
- win: Boolean
- game_duration: Integer (seconds)
- items: JSON array
- summoner_spells: JSON array
- runes: JSON object
- kda: Float (calculated)

Local Secondary Index:
- TimestampIndex: Sort by timestamp for recent matches query
```

**Storage Limit:** Last 20 matches per player (hackathon scope)

**Future:** Expandable to 100+ matches for premium users

#### Conversations Table

AI coaching chat history:

```
Partition Key: puuid (String)
Sort Key: conversation_id (String)

Attributes:
- puuid: Player UUID
- conversation_id: ISO timestamp or UUID
- messages: JSON array of message objects
  [
    {"role": "user", "content": "How do I play Yasuo?"},
    {"role": "assistant", "content": "..."},
    {"role": "tool", "tool_call_id": "...", "content": "..."}
  ]
- session_start: ISO timestamp
- last_message_at: ISO timestamp
- message_count: Integer
- token_count: Integer (for tracking)
```

#### Sessions Table

Authentication session management:

```
Partition Key: session_token (String)

Attributes:
- session_token: UUID v4
- puuid: Player UUID
- created_at: ISO timestamp
- expires_at: ISO timestamp
- last_accessed: ISO timestamp
- ip_address: String (optional, for security)
```

#### MapStories Table

Cached AI-generated zone feedback:

```
Partition Key: puuid (String)
Sort Key: zone_id (String)

Attributes:
- puuid: Player UUID
- zone_id: "top_lane", "dragon", "baron", etc.
- story_mode: "coach" or "roast"
- story_content: Text (AI-generated narrative)
- zone_stats: JSON object with performance metrics
- generated_at: ISO timestamp
- match_ids_analyzed: JSON array (for cache invalidation)
```

**Invalidation:** New matches trigger regeneration

#### PlayerTitles Table

Generated player titles and descriptions:

```
Partition Key: puuid (String)
Sort Key: version (String)

Attributes:
- puuid: Player UUID
- version: ISO timestamp or "latest"
- title: "The Aggressive Playmaker"
- description: AI-generated playstyle description
- most_played_champion: String
- champion_image_url: String
- generated_at: ISO timestamp
- mode: "coach" or "roast"
```

### Data Access Patterns

**Repository Pattern (db/src/repositories/):**

All DynamoDB access goes through repository classes:

```python
# Player operations
player_repo.get_player(puuid)
player_repo.create_player(player_data)
player_repo.update_player(puuid, updates)

# Session operations
session_repo.create_session(session_token, puuid)
session_repo.get_session(session_token)
session_repo.validate_session(session_token)

# Conversation operations
conversation_repo.get_conversations(puuid)
conversation_repo.append_message(puuid, conversation_id, message)
conversation_repo.create_conversation(puuid)
```

**Benefits:**
- Centralized data access logic
- Easier testing and mocking
- Consistent error handling
- Type safety

### Data Consistency

**Player Data:**
- Fetched from Riot API on authentication
- Updated on each map generation
- Stale data acceptable (not real-time critical)

**Match History:**
- Loaded from Riot API if missing
- Stored in DynamoDB for faster subsequent access
- Cached for 1 hour

**Conversation History:**
- Strongly consistent reads (ACID-like behavior)
- Ensures chat context is never lost

**Stories:**
- Eventually consistent (acceptable for caching)
- Regenerated if matches change

## Data Flow Pipeline

### Player Authentication Flow

```
1. User submits riot_id + region
2. Backend queries Riot API for PUUID
3. Check if player exists in Players table
4. If not, create new player record
5. If yes, check if data is stale (> 1 hour)
6. If stale, fetch updated profile from Riot API
7. Update Players table
8. Fetch last 20 matches from Riot API
9. Store/update in MatchHistory table
10. Generate session token
11. Store in Sessions table
12. Return session to frontend
```

### Zone Story Generation Flow

```
1. Receive session token from frontend
2. Validate session, get puuid
3. Query MapStories for existing stories
4. Check story freshness (< 24h) and mode match
5. If fresh, return cached stories
6. If stale/missing:
   a. Query MatchHistory for last 20 matches
   b. Process match data through zone analyzer
   c. Calculate per-zone statistics
   d. Send to Claude Bedrock with prompt
   e. Receive AI-generated stories
   f. Store in MapStories table
   g. Return to frontend
```

### AI Coaching Data Flow

```
1. Validate session, get puuid
2. Query Conversations table for history
3. Load SQLite league data into tool context
4. Send user message + history to Claude
5. Claude may invoke tools:
   - search_champions(query)
   - get_champion_details(name)
   - get_recommended_build(champion, role)
   - get_player_match_history(puuid)
6. Execute tools against SQLite/DynamoDB
7. Return tool results to Claude
8. Claude generates response
9. Append user message + assistant response to Conversations
10. Update last_message_at timestamp
11. Return response to frontend
```

## Data Privacy and Retention

**Player Data:**
- Only public Riot API data stored
- No passwords or personal information
- PUUID is public identifier

**Conversations:**
- Stored per-player for personalization
- Not shared across players
- TTL: 30 days of inactivity (planned)

**Sessions:**
- Ephemeral (24h expiry)
- No sensitive data stored

**GDPR Considerations:**
- Players can request data deletion (not yet implemented)
- All data tied to PUUID (deletable)

## Backup and Recovery

**SQLite:**
- Static data, easily reproducible
- Backed up in Git repository
- Can regenerate from Riot Data Dragon

**DynamoDB:**
- AWS automatic backups (point-in-time recovery)
- On-demand backups planned
- Critical data: Conversations (irreplaceable)
- Non-critical: MapStories (regenerable)

## Cost Optimization

**SQLite:**
- Zero cost (local file)
- No network latency

**DynamoDB:**
- On-demand pricing
- Story caching reduces writes
- Batch operations where possible
- No idle charges (pay per request)

**Estimated Costs (100 daily active users):**
- DynamoDB: $5-10/month
- Bedrock: $50-100/month (main cost)
- Elastic Beanstalk: $15-30/month

## Future Improvements

**Planned:**
- Automated SQLite updates via CI/CD
- DynamoDB TTL for old conversations
- Match history expansion (20 → 100+ matches)
- Redis caching layer for hot data
- Data export API for users
- Analytics dashboard (aggregate stats)
