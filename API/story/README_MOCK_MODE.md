# Mock AI Mode for Testing

## Purpose
Use mock AI responses instead of AWS Bedrock to save tokens during development and testing.

## How to Enable

### Option 1: Environment Variable (Recommended)
Add to your `.env` file:
```
USE_MOCK_AI=true
```

### Option 2: Temporary Testing
```bash
export USE_MOCK_AI=true
python main.py
```

## How to Disable (Use Real AI)
Set in `.env`:
```
USE_MOCK_AI=false
```

Or remove the variable entirely (defaults to false).

## What This Does
- **Mock Mode ON**: Returns pre-written stories instantly, no AWS calls, no token usage
- **Mock Mode OFF**: Uses AWS Bedrock with Claude Sonnet 4.5, consumes tokens

## Mock Story Zones
The mock client has pre-written stories for:
- `baron_pit` - Baron Nashor area
- `dragon_pit` - Dragon area
- `top_lane` - Top lane stories
- `mid_lane` - Mid lane stories
- `bot_lane` - Bot lane stories
- `jungle` - Jungle stories
- `default` - Generic fallback stories

## Example Usage
```python
from API.story.bedrock_client import generate_story

# Will use mock or real AI based on USE_MOCK_AI env variable
story = generate_story(
    prompt="Generate story about Baron performance",
    zone_id="baron_pit"
)
```

## Adding More Mock Stories
Edit `API/story/mock_client.py` and add stories to the `MOCK_STORIES` dictionary.

## Testing Tips
1. Use mock mode for frontend development
2. Use mock mode for rapid iteration on UI
3. Use real AI only when testing actual AI output quality
4. Switch to real AI for demo/production
