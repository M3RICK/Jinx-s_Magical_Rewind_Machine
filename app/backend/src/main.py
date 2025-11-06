from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os
import sys
import asyncio
import traceback
import time
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from API.models.player import Player
from API.analytics.zones.zone_analyzer import analyze_player_zones
from API.story.story_generator import generate_all_stories
from .utils.input_validator import (
    validate_game_name, validate_tag_line, validate_platform,
    validate_match_count, validate_story_mode, validate_riot_id,
    validate_zone_id, sanitize_string
)

# Check if we should use mock DB
USE_MOCK_DB = os.getenv('USE_MOCK_DB', 'false').lower() == 'true'

if USE_MOCK_DB:
    print("\n" + "="*60)
    print("🔧 MOCK DB MODE ENABLED - Zero AWS costs!")
    print("="*60 + "\n")
    from testing.mocks.mock_db import (
        MockPlayerRepository as PlayerRepository,
        store_all_stories, get_all_stories, is_story_fresh,
        delete_all_stories, get_story, check_story_mode
    )
    player_repo = PlayerRepository()
else:
    print("\n" + "="*60)
    print("☁️  REAL DB MODE - Using AWS DynamoDB")
    print("="*60 + "\n")
    from db.src.queries.story_queries import (
        get_all_stories, store_all_stories, is_story_fresh, delete_all_stories, get_story, check_story_mode
    )
    from db.src.repositories.player_repository import PlayerRepository
    from db.src.db_handshake import get_dynamodb_reasources
    dynamodb = get_dynamodb_reasources()
    player_repo = PlayerRepository(dynamodb)

app = Flask(__name__)

ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', 'http://localhost:3000,http://localhost:5000').split(',')
CORS(app, resources={
    r"/api/*": {
        "origins": ALLOWED_ORIGINS,
        "methods": ["GET", "POST"],
        "allow_headers": ["Content-Type"],
        "max_age": 3600
    }
})

# Serve everything from public folder (HTML, CSS, JS, assets)
PUBLIC_FOLDER = os.path.join(os.path.dirname(__file__), '../../frontend/public')

VALID_PLATFORMS = [
    'euw1', 'eun1', 'na1', 'kr', 'br1', 'la1', 'la2', 'oc1',
    'tr1', 'ru', 'jp1', 'ph2', 'sg2', 'th2', 'tw2', 'vn2'
]
MIN_MATCH_COUNT = 5
MAX_MATCH_COUNT = 50
MAX_REQUEST_SIZE = 1024 * 10


# Utility: Convert riot_id format (URL-safe to standard)
def parse_riot_id(riot_id_str):
    result = riot_id_str.replace('-', '#')
    if '#' not in result:
        raise ValueError(f"Invalid riot_id format: {riot_id_str}")
    return result


# Utility: Format riot_id (standard to URL-safe)
def format_riot_id(riot_id_str):
    """Convert 'name#tag' to 'name-tag'"""
    return riot_id_str.replace('#', '-')


# Utility: Run async function in sync context
def run_async(coro):
    """Run async coroutine in sync Flask context"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@app.route('/')
def index():
    return send_from_directory(PUBLIC_FOLDER, 'index.html')


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'version': '1.0.0',
        'database': 'mock' if USE_MOCK_DB else 'dynamodb',
        'ai': 'mock' if os.getenv('USE_MOCK_AI', 'false').lower() == 'true' else 'bedrock'
    }), 200


# ============================================================================
# SHARED ANALYSIS LOGIC
# ============================================================================

def _perform_analysis(game_name, tag_line, platform='euw1', match_count=30, force_refresh=False, story_mode='coach'):
    """
    Shared analysis logic for both /api/analyze and /api/refresh.

    Args:
        game_name: Player's game name
        tag_line: Player's tag line
        platform: Platform/region (default: euw1)
        match_count: Number of matches to analyze (default: 30)
        force_refresh: Skip cache check and force fresh analysis
        story_mode: 'coach' for helpful advice or 'roast' for savage humor (default: coach)

    Returns:
        tuple: (response_data, error_message, status_code)
    """
    try:
        riot_id = f"{game_name}#{tag_line}"

        # Check if player has cached stories (skip if force_refresh)
        if not force_refresh:
            try:
                existing_player = player_repo.get_by_riot_id(riot_id)
                if existing_player:
                    puuid = existing_player.puuid

                    # Check if stories are fresh (within 7 days)
                    if is_story_fresh(puuid, 'intro', max_age_seconds=604800):
                        # Check if cached mode matches requested mode
                        if check_story_mode(puuid, story_mode):
                            mode_emoji = "🎓" if story_mode == 'coach' else "🔥"
                            print(f"✅ Using cached stories for {riot_id} ({mode_emoji} {story_mode.upper()} mode)")

                            cached_stories = get_all_stories(puuid)

                            # Format response
                            zones = {}
                            for story in cached_stories:
                                zones[story['zone_id']] = {
                                    'zone_name': story['zone_name'],
                                    'story': story['story_text'],
                                    'stats': story.get('stats', {})
                                }

                            return ({
                                'player': {
                                    'puuid': puuid,
                                    'riot_id': riot_id,
                                },
                                'zones': zones,
                                'metadata': {
                                    'cached': True,
                                    'story_mode': story_mode,
                                    'generated_at': cached_stories[0].get('generated_at') if cached_stories else int(time.time())
                                }
                            }, None, 200)
                        else:
                            # Mode mismatch - delete old cache and regenerate
                            cached_stories = get_all_stories(puuid)
                            if cached_stories:
                                old_mode = cached_stories[0].get('story_mode', 'coach')
                                print(f"🔄 Mode mismatch: Cache is {old_mode.upper()}, requested {story_mode.upper()}")
                                print(f"🗑️  Deleting old {old_mode} stories and regenerating in {story_mode} mode...")
                                delete_all_stories(puuid)
            except Exception as e:
                print(f"Error checking cache: {e}")
                # Continue with fresh analysis if cache check fails

        # Fresh analysis needed
        print(f"Analyzing player: {riot_id} with {match_count} matches")

        async def analyze():
            async with Player(game_name, tag_line, platform=platform) as player:
                # Load profile
                success = await player.load_profile()
                if not success:
                    return None, "Failed to load player profile"

                # Load matches
                await player.load_recent_matches(count=match_count)

                if not player.processed_stats:
                    return None, "No match data found"

                # Load timelines (required for zone analysis)
                await player.load_match_timelines()

                # Process matches
                player.process_matches()

                # Analyze zones
                zone_stats = analyze_player_zones(player.processed_stats)

                # Generate stories with specified mode
                stories = generate_all_stories(zone_stats, story_mode=story_mode)

                # Store in DB with story mode
                if player.puuid:
                    stored = store_all_stories(player.puuid, stories, story_mode=story_mode)
                    print(f"Stored {len(stored)} stories for {riot_id} in {story_mode.upper()} mode")

                return {
                    'player': {
                        'puuid': player.puuid,
                        'riot_id': riot_id,
                        'summoner_name': player.summoner_info.get('name') if player.summoner_info else None,
                        'level': player.summoner_info.get('summonerLevel') if player.summoner_info else None,
                        'rank': player.rank_info[0] if player.rank_info else None
                    },
                    'zones': stories,
                    'metadata': {
                        'matches_analyzed': len(player.processed_stats),
                        'generated_at': int(time.time()),
                        'cached': False,
                        'story_mode': story_mode
                    }
                }, None

        result, error = run_async(analyze())

        if error:
            return (None, error, 404)

        return (result, None, 200)

    except Exception as e:
        print(f"Error in _perform_analysis: {e}")
        traceback.print_exc()
        return (None, str(e), 500)


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/api/analyze', methods=['POST'])
def analyze_player():
    try:
        if request.content_length and request.content_length > MAX_REQUEST_SIZE:
            return jsonify({'error': 'Request too large'}), 413

        data = request.get_json(silent=True)
        if not data:
            return jsonify({'error': 'Invalid JSON or missing Content-Type header'}), 400

        game_name = data.get('gameName')
        tag_line = data.get('tagLine')
        platform = data.get('platform', 'euw1')
        match_count = data.get('matchCount', 30)
        story_mode = data.get('storyMode', 'coach')

        is_valid, error = validate_game_name(game_name)
        if not is_valid:
            return jsonify({'error': error}), 400

        is_valid, error = validate_tag_line(tag_line)
        if not is_valid:
            return jsonify({'error': error}), 400

        is_valid, error = validate_platform(platform, VALID_PLATFORMS)
        if not is_valid:
            return jsonify({'error': error}), 400

        is_valid, error, match_count = validate_match_count(match_count, MIN_MATCH_COUNT, MAX_MATCH_COUNT)
        if not is_valid:
            return jsonify({'error': error}), 400

        is_valid, error = validate_story_mode(story_mode)
        if not is_valid:
            return jsonify({'error': error}), 400
        if not story_mode:
            story_mode = 'coach'

        game_name = sanitize_string(game_name, 16)
        tag_line = sanitize_string(tag_line, 5)

        print(f"📖 Story mode: {story_mode.upper()}")

        result, error, status_code = _perform_analysis(
            game_name, tag_line, platform, match_count,
            force_refresh=False, story_mode=story_mode
        )

        if error:
            return jsonify({'error': error}), status_code

        return jsonify(result), status_code

    except Exception as e:
        print(f"Error in /api/analyze: {e}")
        traceback.print_exc()
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/zones/<riot_id>', methods=['GET'])
def get_zones(riot_id):
    try:
        is_valid, error = validate_riot_id(riot_id)
        if not is_valid:
            return jsonify({'error': error}), 400

        riot_id_parsed = parse_riot_id(riot_id)
        player = player_repo.get_by_riot_id(riot_id_parsed)
        if not player:
            return jsonify({'error': f'Player not found'}), 404

        stories = get_all_stories(player.puuid)

        if not stories:
            return jsonify({'error': f'No stories found. Run /api/analyze first.'}), 404

        zones = {}
        for story in stories:
            zones[story['zone_id']] = {
                'zone_name': story['zone_name'],
                'story': story['story_text'],
                'stats': story.get('stats', {})
            }

        story_mode = stories[0].get('story_mode', 'coach') if stories else 'coach'

        return jsonify({
            'player': {
                'puuid': player.puuid,
                'riot_id': riot_id_parsed
            },
            'zones': zones,
            'metadata': {
                'cached': True,
                'story_mode': story_mode,
                'generated_at': stories[0].get('generated_at') if stories else int(time.time())
            }
        }), 200

    except Exception as e:
        print(f"Error in /api/zones: {e}")
        traceback.print_exc()
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/zone/<riot_id>/<zone_id>', methods=['GET'])
def get_zone(riot_id, zone_id):
    try:
        is_valid, error = validate_riot_id(riot_id)
        if not is_valid:
            return jsonify({'error': error}), 400

        is_valid, error = validate_zone_id(zone_id)
        if not is_valid:
            return jsonify({'error': error}), 400

        riot_id_parsed = parse_riot_id(riot_id)
        player = player_repo.get_by_riot_id(riot_id_parsed)
        if not player:
            return jsonify({'error': 'Player not found'}), 404

        story = get_story(player.puuid, zone_id)

        if not story:
            return jsonify({'error': 'Zone not found'}), 404

        return jsonify({
            'zone_id': story['zone_id'],
            'zone_name': story['zone_name'],
            'story': story['story_text'],
            'story_mode': story.get('story_mode', 'coach'),
            'stats': story.get('stats', {}),
            'generated_at': story.get('generated_at')
        }), 200

    except Exception as e:
        print(f"Error in /api/zone: {e}")
        traceback.print_exc()
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/refresh/<riot_id>', methods=['POST'])
def refresh_player(riot_id):
    try:
        if request.content_length and request.content_length > MAX_REQUEST_SIZE:
            return jsonify({'error': 'Request too large'}), 413

        is_valid, error = validate_riot_id(riot_id)
        if not is_valid:
            return jsonify({'error': error}), 400

        riot_id_parsed = parse_riot_id(riot_id)
        parts = riot_id_parsed.split('#')
        if len(parts) != 2:
            return jsonify({'error': 'Invalid riot_id format'}), 400
        game_name, tag_line = parts

        data = request.get_json(silent=True) or {}
        match_count = data.get('matchCount', 30)
        platform = data.get('platform', 'euw1')
        story_mode = data.get('storyMode', 'coach')

        is_valid, error = validate_platform(platform, VALID_PLATFORMS)
        if not is_valid:
            return jsonify({'error': error}), 400

        is_valid, error, match_count = validate_match_count(match_count, MIN_MATCH_COUNT, MAX_MATCH_COUNT)
        if not is_valid:
            return jsonify({'error': error}), 400

        is_valid, error = validate_story_mode(story_mode)
        if not is_valid:
            return jsonify({'error': error}), 400
        if not story_mode:
            story_mode = 'coach'

        print(f"📖 Refresh with story mode: {story_mode.upper()}")

        player = player_repo.get_by_riot_id(riot_id_parsed)
        if player:
            deleted_count = delete_all_stories(player.puuid)
            print(f"Deleted {deleted_count} old stories")

        result, error, status_code = _perform_analysis(
            game_name, tag_line, platform, match_count,
            force_refresh=True, story_mode=story_mode
        )

        if error:
            return jsonify({'error': error}), status_code

        return jsonify(result), status_code

    except Exception as e:
        print(f"Error in /api/refresh: {e}")
        traceback.print_exc()
        return jsonify({'error': 'Internal server error'}), 500


# ============================================================================
# STATIC FILE SERVING (Must be last to not override API routes)
# ============================================================================

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files from public folder (HTML, CSS, JS, images, etc.)"""
    # Only serve files that don't start with 'api'
    if filename.startswith('api'):
        return jsonify({'error': 'Not found'}), 404
    return send_from_directory(PUBLIC_FOLDER, filename)


if __name__ == '__main__':
    app.run(debug=True, port=5000)
