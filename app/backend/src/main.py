from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os
import sys
import asyncio
import traceback
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from API.models.player import Player
from API.analytics.zones.zone_analyzer import analyze_player_zones
from API.story.story_generator import generate_all_stories

# Check if we should use mock DB
USE_MOCK_DB = os.getenv('USE_MOCK_DB', 'false').lower() == 'true'

if USE_MOCK_DB:
    print("\n" + "="*60)
    print("🔧 MOCK DB MODE ENABLED - Zero AWS costs!")
    print("="*60 + "\n")
    from db.src.mock_db import (
        MockPlayerRepository as PlayerRepository,
        store_all_stories, get_all_stories, is_story_fresh,
        delete_all_stories, get_story
    )
    player_repo = PlayerRepository()
else:
    print("\n" + "="*60)
    print("☁️  REAL DB MODE - Using AWS DynamoDB")
    print("="*60 + "\n")
    from db.src.queries.story_queries import (
        get_all_stories, store_all_stories, is_story_fresh, delete_all_stories, get_story
    )
    from db.src.repositories.player_repository import PlayerRepository
    from db.src.db_handshake import get_dynamodb_reasources
    dynamodb = get_dynamodb_reasources()
    player_repo = PlayerRepository(dynamodb)

app = Flask(__name__)
CORS(app)

FRONTEND_FOLDER = '/app/frontend/src'
PUBLIC_FOLDER = '/app/frontend/public'


# Utility: Convert riot_id format (URL-safe to standard)
def parse_riot_id(riot_id_str):
    """Convert 'name-tag' to 'name#tag'"""
    return riot_id_str.replace('-', '#')


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
    return send_from_directory(FRONTEND_FOLDER, 'index.html')


@app.route('/public/<path:filename>')
def static_files(filename):
    return send_from_directory(PUBLIC_FOLDER, filename)


# ============================================================================
# SHARED ANALYSIS LOGIC
# ============================================================================

def _perform_analysis(game_name, tag_line, platform='euw1', match_count=30, force_refresh=False):
    """
    Shared analysis logic for both /api/analyze and /api/refresh.

    Args:
        game_name: Player's game name
        tag_line: Player's tag line
        platform: Platform/region (default: euw1)
        match_count: Number of matches to analyze (default: 30)
        force_refresh: Skip cache check and force fresh analysis

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
                    # Check if stories are fresh
                    if is_story_fresh(puuid, 'intro', max_age_seconds=604800):  # 7 days
                        print(f"Using cached stories for {riot_id}")
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
                                'generated_at': cached_stories[0].get('generated_at') if cached_stories else int(time.time())
                            }
                        }, None, 200)
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

                # Generate stories
                stories = generate_all_stories(zone_stats)

                # Store in DB
                if player.puuid:
                    stored = store_all_stories(player.puuid, stories)
                    print(f"Stored {len(stored)} stories for {riot_id}")

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
                        'cached': False
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
    """
    Main endpoint: Analyze player and generate zone stories.

    Request:
        {
            "gameName": "theoppstopper",
            "tagLine": "bigra",
            "platform": "euw1",
            "matchCount": 30  // optional, default 30
        }

    Response:
        {
            "player": {...},
            "zones": {...},
            "metadata": {...}
        }
    """
    try:
        data = request.get_json()

        # Validate input
        game_name = data.get('gameName')
        tag_line = data.get('tagLine')
        platform = data.get('platform', 'euw1')
        match_count = data.get('matchCount', 30)

        if not game_name or not tag_line:
            return jsonify({'error': 'gameName and tagLine are required'}), 400

        # Perform analysis
        result, error, status_code = _perform_analysis(
            game_name, tag_line, platform, match_count, force_refresh=False
        )

        if error:
            return jsonify({'error': error}), status_code

        return jsonify(result), status_code

    except Exception as e:
        print(f"Error in /api/analyze: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/zones/<riot_id>', methods=['GET'])
def get_zones(riot_id):
    """
    Get all cached zones for a player.

    Example: GET /api/zones/theoppstopper-bigra

    Response:
        {
            "player": {...},
            "zones": {...},
            "metadata": {...}
        }
    """
    try:
        # Parse riot_id
        riot_id_parsed = parse_riot_id(riot_id)

        # Get player from DB
        player = player_repo.get_by_riot_id(riot_id_parsed)
        if not player:
            return jsonify({'error': f'Player {riot_id_parsed} not found in database'}), 404

        # Get stories
        stories = get_all_stories(player.puuid)

        if not stories:
            return jsonify({
                'error': f'No stories found for {riot_id_parsed}. Run /api/analyze first.'
            }), 404

        # Format response
        zones = {}
        for story in stories:
            zones[story['zone_id']] = {
                'zone_name': story['zone_name'],
                'story': story['story_text'],
                'stats': story.get('stats', {})
            }

        return jsonify({
            'player': {
                'puuid': player.puuid,
                'riot_id': riot_id_parsed
            },
            'zones': zones,
            'metadata': {
                'cached': True,
                'generated_at': stories[0].get('generated_at') if stories else int(time.time())
            }
        }), 200

    except Exception as e:
        print(f"Error in /api/zones: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/zone/<riot_id>/<zone_id>', methods=['GET'])
def get_zone(riot_id, zone_id):
    """
    Get specific zone story for a player.

    Example: GET /api/zone/theoppstopper-bigra/baron_pit

    Response:
        {
            "zone_id": "baron_pit",
            "zone_name": "Baron Nashor",
            "story": "...",
            "stats": {...},
            "generated_at": 1730000000
        }
    """
    try:
        # Parse riot_id
        riot_id_parsed = parse_riot_id(riot_id)

        # Get player from DB
        player = player_repo.get_by_riot_id(riot_id_parsed)
        if not player:
            return jsonify({'error': f'Player {riot_id_parsed} not found'}), 404

        # Get specific story
        story = get_story(player.puuid, zone_id)

        if not story:
            return jsonify({'error': f'Zone {zone_id} not found for {riot_id_parsed}'}), 404

        return jsonify({
            'zone_id': story['zone_id'],
            'zone_name': story['zone_name'],
            'story': story['story_text'],
            'stats': story.get('stats', {}),
            'generated_at': story.get('generated_at')
        }), 200

    except Exception as e:
        print(f"Error in /api/zone: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/refresh/<riot_id>', methods=['POST'])
def refresh_player(riot_id):
    """
    Force re-analysis of player (delete cache and regenerate).

    Example: POST /api/refresh/theoppstopper-bigra

    Request (optional):
        {
            "matchCount": 30,
            "platform": "euw1"
        }

    Response: Same as /api/analyze
    """
    try:
        # Parse riot_id from URL
        riot_id_parsed = parse_riot_id(riot_id)
        game_name, tag_line = riot_id_parsed.split('#')

        # Get optional parameters (silent=True allows missing Content-Type)
        data = request.get_json(silent=True) or {}
        match_count = data.get('matchCount', 30)
        platform = data.get('platform', 'euw1')

        # Delete old cached stories first
        player = player_repo.get_by_riot_id(riot_id_parsed)
        if player:
            deleted_count = delete_all_stories(player.puuid)
            print(f"Deleted {deleted_count} old stories for {riot_id_parsed}")

        # Run fresh analysis with force_refresh=True
        result, error, status_code = _perform_analysis(
            game_name, tag_line, platform, match_count, force_refresh=True
        )

        if error:
            return jsonify({'error': error}), status_code

        return jsonify(result), status_code

    except Exception as e:
        print(f"Error in /api/refresh: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)
