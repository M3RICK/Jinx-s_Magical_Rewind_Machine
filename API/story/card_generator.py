"""
Generate personalized titles and stories for player cards using AI.
"""

from .bedrock_client import create_bedrock_client
from langchain_core.messages import SystemMessage, HumanMessage
import time
import os
import json

USE_MOCK = os.getenv('USE_MOCK_AI', 'false').lower() == 'true'


CARD_SYSTEM_PROMPT = """You are a creative storyteller for League of Legends player cards.

YOUR ROLE:
- Generate epic, personalized titles and short stories for player cards
- Make the content memorable, engaging, and unique to each player
- Use player statistics to craft a narrative that reflects their playstyle

OUTPUT FORMAT:
You must respond ONLY with valid JSON in this exact format:
{
  "title": "An epic 2-4 word title",
  "story": "A compelling 1-2 sentence story (max 150 characters)"
}

STYLE GUIDELINES:
- Titles should be epic, dramatic, or humorous based on stats
- Stories should be concise but impactful
- Reference the player's champion, playstyle, or rank when possible
- Use second person perspective ("You", "Your") in the story
- Keep it punchy and memorable

EXAMPLES:
For a high KDA assassin player:
{
  "title": "Shadow Reaper",
  "story": "You strike from the shadows, leaving chaos in your wake. Death follows your every move."
}

For a support main with high assists:
{
  "title": "Guardian Angel",
  "story": "Your allies thrive under your protection, turning desperate fights into glorious victories."
}

For a feeding player (roast mode):
{
  "title": "The Donation King",
  "story": "You're more generous than a charity stream, giving the enemy team free gold all game long."
}"""


def generate_card_content(player_stats, story_mode='coach'):
    """
    Generate personalized title and story for a player card.

    Args:
        player_stats: Dictionary containing:
            - champion_played: Most played champion
            - games_played: Number of games
            - kda: Kill/Death/Assist ratio
            - rank: Current rank
            - winrate: Win percentage (optional)
        story_mode: 'coach' for epic/motivational or 'roast' for humorous/savage

    Returns:
        Dictionary with 'title' and 'story' or None if generation fails
    """
    if USE_MOCK:
        print(f"[MOCK MODE] Using mock card content in {story_mode.upper()} mode")
        return {
            'title': 'The Challenger',
            'story': 'A legend in the making, conquering the Rift one game at a time.'
        }

    # Build the prompt
    champion = player_stats.get('champion_played', 'Unknown')
    games = player_stats.get('games_played', 0)
    kda = player_stats.get('kda', 0.0)
    rank = player_stats.get('rank', 'Unranked')
    winrate = player_stats.get('winrate', 50.0)

    tone = "epic and motivational" if story_mode == 'coach' else "humorous and savage, roasting the player"

    prompt = f"""Generate a personalized title and story for this League of Legends player's card.

PLAYER STATS:
- Most Played Champion: {champion}
- Games Played: {games}
- KDA Ratio: {kda:.2f}
- Rank: {rank}
- Winrate: {winrate:.1f}%

TONE: {tone}

Generate a title and story that captures this player's essence. The title should be epic and memorable. The story should be concise (max 150 characters) and impactful.

Remember to respond ONLY with valid JSON in the format specified in the system prompt."""

    try:
        chat = create_bedrock_client()

        messages = [
            SystemMessage(content=CARD_SYSTEM_PROMPT),
            HumanMessage(content=prompt)
        ]

        # Retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = chat.invoke(messages)
                result_text = response.content.strip()

                # Parse JSON response
                import json

                # Clean up response if it contains markdown code blocks
                if '```json' in result_text:
                    result_text = result_text.split('```json')[1].split('```')[0].strip()
                elif '```' in result_text:
                    result_text = result_text.split('```')[1].split('```')[0].strip()

                result = json.loads(result_text)

                # Validate response format
                if 'title' in result and 'story' in result:
                    # Ensure story is not too long (max 150 chars)
                    if len(result['story']) > 150:
                        result['story'] = result['story'][:147] + '...'

                    print(f"Generated card content: '{result['title']}' in {story_mode.upper()} mode")
                    return result
                else:
                    print(f"Invalid response format: {result}")
                    return None

            except json.JSONDecodeError as e:
                print(f"JSON parsing error: {e}")
                print(f"Raw response: {result_text}")
                # Fallback to defaults if JSON parsing fails
                return None

            except Exception as retry_error:
                if "Too many connections" in str(retry_error) and attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"Rate limited. Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    print(f"Error generating card content: {retry_error}")
                    return None

        return None

    except Exception as e:
        print(f"Error in generate_card_content: {e}")
        return None


def generate_card_content_with_fallback(player_stats, story_mode='coach'):
    """
    Generate card content with AI, falling back to defaults if it fails.

    This ensures we always return something, even if AI generation fails.
    """
    result = generate_card_content(player_stats, story_mode)

    if result:
        return result

    # Fallback to default based on stats
    print("AI generation failed, using fallback content")

    kda = player_stats.get('kda', 0.0)
    rank = player_stats.get('rank', 'Unranked')

    if story_mode == 'roast':
        if kda < 2.0:
            return {
                'title': 'The Feeder',
                'story': 'Turning losses into an art form, one death at a time.'
            }
        else:
            return {
                'title': 'The Try-Hard',
                'story': 'Sweating harder than a challenger in promos.'
            }
    else:
        if 'Challenger' in rank or 'Grandmaster' in rank or 'Master' in rank:
            return {
                'title': 'The Elite',
                'story': 'Among the best, conquering the Rift with skill and determination.'
            }
        elif kda >= 3.0:
            return {
                'title': 'The Dominator',
                'story': 'Your enemies fear your name. Victory is your only destination.'
            }
        else:
            return {
                'title': 'The Competitor',
                'story': 'Every game is a new chapter in your legend. Keep climbing.'
            }
