# Getting Started

**How to Run and Test RiftRewind Locally**

## Overview

RiftRewind is primarily deployed on AWS Elastic Beanstalk for production use. For local development and testing, we use a CLI-based approach for individual component testing and manual database operations.

## Prerequisites

**Required:**
- Python 3.12+
- Docker and Docker Compose
- Git
- SQLite3
- AWS Account (for DynamoDB and Bedrock access)
- Riot Games API Key

**Optional:**
- Virtual environment tool (venv)

## Environment Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd G-PRO-500-TLS-5-1-professionalwork-23
```

### 2. Environment Variables

Create a `.env` file in the root directory:

```bash
# AWS Configuration
AWS_REGION=eu-west-3
AWS_DEFAULT_REGION=eu-west-3
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key

# Riot API
RIOT_API_KEY=your_riot_api_key

# Testing Flags
USE_MOCK_DB=false      # Set to true to avoid AWS costs during testing
USE_MOCK_AI=false      # Set to true to skip AI calls
```

### 3. Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python packages
pip install -r requirements.txt
```

### 4. Database Setup

**SQLite (Static Game Data):**

The SQLite database (`app/data/league_data.db`) should already be included in the repository with pre-populated League of Legends data.

If you need to rebuild it:
```bash
cd app/cli
python setup_league_data.py  # Manual sync with Riot Data Dragon
```

**DynamoDB (Dynamic Player Data):**

Initialize DynamoDB tables:
```bash
cd db
python setup_new_tables.py
```

This creates all required tables: Players, MatchHistory, Conversations, Sessions, MapStories, PlayerTitles

## Running Locally

### Option 1: Docker Compose (Recommended)

```bash
docker-compose up --build
```

Access the application at: `http://localhost`

### Option 2: Flask Development Server

```bash
export FLASK_APP=app/backend/src/main.py
export FLASK_RUN_HOST=0.0.0.0
flask run --port=5000
```

Access the application at: `http://localhost:5000`

### Option 3: Docker Only

```bash
docker build -t riftrewind .
docker run -p 80:5000 --env-file .env riftrewind
```

## CLI Testing Tools

RiftRewind includes CLI scripts for testing individual components without running the full web application.

### Testing the API Pipeline

**Location:** `/app/cli/` and root `main.py`

**Purpose:** Test Riot API integration, data processing, and player analysis

**Example Usage:**

```bash
# Run the main test script
python main.py
```

This script:
1. Fetches player data from Riot API
2. Loads recent matches
3. Processes match timelines
4. Calculates aggregated statistics
5. Exports results to JSON

**Customization:**

Edit `main.py` to test different players:

```python
import asyncio
from API.models.player import Player

async def main():
    async with Player("summoner_name", "tag", platform="euw1") as player:
        await player.load_profile()
        await player.load_recent_matches(10)
        await player.load_match_timelines()
        player.process_matches()
        player.export_to_json("player_data.json")

asyncio.run(main())
```

### Testing AI Chat

**Location:** `/app/backend/src/ai_chat.py`

**Purpose:** Test Claude integration and conversation flow

```bash
cd app/backend/src
python ai_chat.py
```

Interactive chat session opens in terminal:
```
Rift Rewind AI Chat
==================================================
Type 'quit' to exit

Connecting to AWS Bedrock...
Connected! Start chatting:

You: How do I play Yasuo?
AI: [Claude's response with tool calls]
```

### Manual Database Operations

**SQLite Queries:**

```bash
sqlite3 app/data/league_data.db

# Example queries
SELECT * FROM champions WHERE primary_role = 'Marksman' LIMIT 5;
SELECT * FROM items WHERE name LIKE '%sword%';
SELECT * FROM recommended_builds WHERE champion_id = 'Jinx';
```

**DynamoDB Operations:**

Use AWS CLI or Python scripts:

```bash
# List tables
aws dynamodb list-tables --region eu-west-3

# Query player data
aws dynamodb get-item \
    --table-name Players \
    --key '{"puuid": {"S": "player_puuid_here"}}' \
    --region eu-west-3
```

Or via Python:

```python
from db.src.repositories.player_repository import PlayerRepository
from db.src.db_handshake import get_dynamodb_resources

dynamodb = get_dynamodb_resources()
player_repo = PlayerRepository(dynamodb)

player = player_repo.get_player("puuid_here")
print(player)
```

### Manual Database Sync

**Riot Data Dragon Sync (SQLite):**

Update League static data every 2 weeks:

```bash
cd app/cli
python sync_data_dragon.py --patch 14.23
```

**Note:** This is currently a **manual, unoptimized process**. Planned automation via GitHub Actions.

## Testing Workflow

### 1. Test Individual Components

**Test Riot API Integration:**
```bash
python main.py  # Test player data fetch
```

**Test Zone Analysis:**
```bash
cd API/analytics/zones
python test_zone_analyzer.py
```

**Test AI Story Generation:**
```bash
cd API/story
python test_story_generator.py
```

### 2. Test Full Pipeline

1. Run Flask server locally
2. Open browser to `http://localhost:5000`
3. Enter test summoner credentials
4. Verify:
   - Player authentication
   - Match history loading
   - Interactive map functionality
   - AI coaching chat
   - Player card generation

### 3. Verify Database State

After testing, check that data was properly stored:

```bash
# Check DynamoDB
python -c "from db.src.repositories.player_repository import *; \
           from db.src.db_handshake import get_dynamodb_resources; \
           repo = PlayerRepository(get_dynamodb_resources()); \
           print(repo.get_player('test_puuid'))"
```

## Common Issues and Solutions

### Issue: AWS Credentials Not Found

**Solution:**
```bash
# Verify credentials
aws configure list

# Or set manually in .env file
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
```

### Issue: Riot API Rate Limiting

**Solution:**
- The Pulsefire library handles rate limiting automatically
- If you hit limits, wait 2 minutes or use `USE_MOCK_DB=true` for testing

### Issue: DynamoDB Table Not Found

**Solution:**
```bash
# Recreate tables
cd db
python setup_new_tables.py
```

### Issue: SQLite Database Missing

**Solution:**
- Ensure `app/data/league_data.db` exists
- If missing, run data sync script or copy from backup

### Issue: Docker Container Won't Start

**Solution:**
```bash
# Check logs
docker-compose logs

# Rebuild without cache
docker-compose build --no-cache
docker-compose up
```

## Development Tips

### Mock Mode for Cost Savings

During development, enable mock mode to avoid AWS costs:

```bash
# In .env
USE_MOCK_DB=true
USE_MOCK_AI=true
```

This uses local fallback data instead of calling DynamoDB and Bedrock.

### Hot Reload

Flask development server supports hot reload:
```bash
export FLASK_DEBUG=1
flask run
```

Changes to Python files will automatically restart the server.

### Testing Without Frontend

Use the API endpoints directly:

```bash
# Test authentication
curl -X POST http://localhost:5000/api/authenticate \
  -H "Content-Type: application/json" \
  -d '{"game_name": "test", "tag_line": "EUW", "platform": "euw1"}'

# Test health check
curl http://localhost:5000/health
```

## Deployment Notes

**For Production:**

The application is deployed via AWS Elastic Beanstalk using Docker.

See: `Dockerfile` and `Dockerrun.aws.json` for deployment configuration.

Deployment is currently manual:
```bash
eb deploy
```

Planned: GitHub Actions CI/CD pipeline for automated deployment.

## Limitations

**Current Testing Approach:**

The CLI-based testing workflow is **very unoptimized** and primarily used for:
- Individual component testing
- Manual database synchronization
- Debugging specific pipeline issues
- Ad-hoc data verification

**No Comprehensive Testing Framework:**
- No unit tests
- No integration tests
- No E2E tests
- No automated test suite

**Manual Operations:**
- Database sync is completely manual
- Data validation requires manual verification
- No automated health checks or monitoring

**Planned Improvements:**
- Add pytest test suite
- Automate Data Dragon sync via GitHub Actions
- Implement proper CI/CD pipeline
- Create staging environment
- Add comprehensive monitoring and alerting

## Next Steps

Once you have the application running locally:
1. Test with your own summoner account
2. Explore the interactive map
3. Chat with the AI coach
4. Generate a player card
5. Check DynamoDB to see stored data

For more details on specific features, see the Feature Documentation sections.
