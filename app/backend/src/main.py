from flask import Flask, jsonify, request, send_from_directory
import base64
import os
import sys
import asyncio
import traceback
import time
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from app.backend.src.image_creation import RewindExportProfil, RewindCardGeneration
from API.models.player import Player
from API.analytics.zones.zone_analyzer import analyze_player_zones
from API.story.story_generator import generate_all_stories
from API.story.card_generator import generate_card_content_with_fallback
from app.backend.src.utils.input_validator import (
    validate_game_name, validate_tag_line, validate_platform,
    validate_match_count, validate_story_mode, validate_riot_id,
    validate_zone_id, sanitize_string
)

# Import AI chat functionality (for /api/coach endpoint)
from app.backend.src.ai_chat import create_chat, SYSTEM_PROMPT
from league_tools import TOOL_DEFINITIONS, execute_tool, set_player_puuid
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
import json

# Using AWS DynamoDB for production
from db.src.queries.story_queries import (
    get_all_stories, store_all_stories, is_story_fresh, delete_all_stories, get_story, check_story_mode, store_story
)
from db.src.repositories.player_repository import PlayerRepository
from db.src.repositories.session_repository import SessionRepository
from db.src.repositories.conversation_repository import ConversationRepository
from db.src.db_handshake import get_dynamodb_resources
dynamodb = get_dynamodb_resources()
player_repo = PlayerRepository(dynamodb)
session_repo = SessionRepository(dynamodb)
conversation_repo = ConversationRepository(dynamodb)

app = Flask(__name__)

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
        'database': 'dynamodb',
        'ai': 'bedrock'
    }), 200


@app.route('/api/authenticate', methods=['POST'])
def authenticate_player():
    """
    Authentication endpoint - validates player on Riot API and creates/updates in DB

    Request:
    {
        "gameName": "sad and bad",
        "tagLine": "2093",
        "platform": "euw1"
    }

    Response:
    {
        "session_token": "uuid",
        "player": { "riot_id": "sad and bad#2093", "puuid": "...", ... }
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'Invalid JSON'}), 400

        game_name = data.get('gameName')
        tag_line = data.get('tagLine')
        platform = data.get('platform', 'euw1')

        if not game_name or not tag_line:
            return jsonify({'error': 'gameName and tagLine are required'}), 400

        riot_id = f"{game_name}#{tag_line}"

        print(f"\nAuthenticating player: {riot_id} on {platform}")

        # Use existing CLI logic to check/build player
        from app.cli.client_check import check_and_build_client

        # Map platform to region
        platform_to_region = {
            'na1': 'americas', 'br1': 'americas', 'la1': 'americas', 'la2': 'americas',
            'euw1': 'europe', 'eun1': 'europe', 'tr1': 'europe', 'ru': 'europe',
            'kr': 'asia', 'jp1': 'asia',
            'oc1': 'sea', 'ph2': 'sea', 'sg2': 'sea', 'th2': 'sea', 'tw2': 'sea', 'vn2': 'sea'
        }
        region = platform_to_region.get(platform, 'europe')

        # Get PUUID from Riot API first
        from API.Core import Core
        from API.riot.account import RiotAccountAPI

        async def fetch_puuid():
            async with Core() as core:
                account_api = RiotAccountAPI(core)
                return await account_api.get_puuid(game_name, tag_line, region)

        puuid = asyncio.run(fetch_puuid())

        if not puuid:
            return jsonify({'error': f'Player {riot_id} not found on Riot servers'}), 404

        print(f"Found player: {riot_id} (PUUID: {puuid[:16]}...)")

        # Check and build client (creates/updates player, fetches matches, creates session)
        success, player, session_token = check_and_build_client(puuid, riot_id, region, platform)

        if not success:
            return jsonify({'error': 'Failed to build player profile'}), 500

        return jsonify({
            'session_token': session_token,
            'player': {
                'riot_id': riot_id,
                'puuid': puuid,
                'gameName': game_name,
                'tagLine': tag_line,
                'rank': player.current_rank if player else None,
                'winrate': player.winrate if player else None
            },
            'metadata': {
                'cached': False
            }
        }), 200

    except Exception as e:
        print(f"Error in /api/authenticate: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ============================================================================
# SHARED ANALYSIS LOGIC
# ============================================================================

def format_cached_response(puuid, riot_id, cached_stories, story_mode):
    """Format cached stories into API response"""
    zones = {}
    for story in cached_stories:
        zones[story['zone_id']] = {
            'zone_name': story['zone_name'],
            'story': story['story_text'],
            'stats': story.get('stats', {})
        }

    return {
        'player': {'puuid': puuid, 'riot_id': riot_id},
        'zones': zones,
        'metadata': {
            'cached': True,
            'story_mode': story_mode,
            'generated_at': cached_stories[0].get('generated_at') if cached_stories else int(time.time())
        }
    }

def check_cached_stories(riot_id, story_mode):
    """Check if player has fresh cached stories"""
    try:
        existing_player = player_repo.get_by_riot_id(riot_id)
        if not existing_player:
            return None

        puuid = existing_player.puuid

        if not is_story_fresh(puuid, 'intro', max_age_seconds=604800):
            return None

        if not check_story_mode(puuid, story_mode):
            cached_stories = get_all_stories(puuid)
            if cached_stories:
                old_mode = cached_stories[0].get('story_mode', 'coach')
                print(f"Mode mismatch: Cache is {old_mode.UPPER()}, requested {story_mode.upper()}")
                print(f"Deleting old {old_mode} stories and regenerating in {story_mode} mode...")
                delete_all_stories(puuid)
            return None

        print(f"Using cached stories for {riot_id} ({story_mode.upper()} mode)")
        cached_stories = get_all_stories(puuid)
        return format_cached_response(puuid, riot_id, cached_stories, story_mode)

    except Exception as e:
        print(f"Error checking cache: {e}")
        return None

def extract_rank_info(player):
    """Extract rank information from player data"""
    if not player.rank_info:
        return None

    for queue in player.rank_info:
        if queue.get('queueType') == 'RANKED_SOLO_5x5':
            from db.src.models.player import RankInfo
            return RankInfo(
                tier=queue.get('tier', 'Unranked'),
                division=queue.get('rank', ''),
                lp=queue.get('leaguePoints', 0)
            )
    return None

def save_player_to_database(player, riot_id, platform):
    """Save or update player in database"""
    from db.src.models.player import Player as DBPlayer

    rank_info = extract_rank_info(player)

    wins = sum(1 for m in player.processed_stats if m.get('win', False))
    total_matches = len(player.processed_stats)
    winrate = (wins / total_matches * 100) if total_matches > 0 else 0.0

    db_player = DBPlayer(
        puuid=player.puuid,
        riot_id=riot_id,
        region=platform,
        main_role=None,
        main_champions=[],
        winrate=winrate,
        current_rank=rank_info
    )

    existing_player = player_repo.get_by_puuid(player.puuid)
    if existing_player:
        player_repo.update(db_player)
        print(f"Updated player record for {riot_id}")
    else:
        player_repo.create(db_player)
        print(f"Created player record for {riot_id}")

def generate_and_store_stories(player, zone_stats, riot_id, story_mode):
    """Generate intro story and cache all zone stats"""
    from API.story.story_generator import generate_zone_story

    stories = {}
    if 'intro' in zone_stats:
        print(f"  [1/1] Generating intro zone only...")
        intro_story = generate_zone_story('intro', zone_stats['intro'], story_mode)
        if intro_story:
            stories['intro'] = {
                'zone_name': zone_stats['intro'].get('zone_name', 'intro'),
                'story': intro_story,
                'stats': zone_stats['intro']
            }
        print(f"Generated intro zone in {story_mode} mode (others will load on-demand)\n")

    if player.puuid and stories:
        stored = store_all_stories(player.puuid, stories, story_mode=story_mode)
        print(f"Stored {len(stored)} intro story for {riot_id} in {story_mode.upper()} mode")

    if player.puuid:
        stored_count = 0
        for zone_id, stats in zone_stats.items():
            if zone_id != 'intro' and stats and isinstance(stats, dict) and len(stats) > 0:
                store_story(player.puuid, zone_id, "", stats.get('zone_name', zone_id), stats, story_mode)
                stored_count += 1
                print(f"  Cached {zone_id}: {len(stats)} stat fields")
            elif zone_id != 'intro':
                print(f"  WARNING: Skipping {zone_id} - empty stats")
        print(f"Cached stats for {stored_count}/{len(zone_stats)-1} additional zones")

    return stories

def _perform_analysis(game_name, tag_line, platform='euw1', match_count=15, force_refresh=False, story_mode='coach'):
    """
    Shared analysis logic for both /api/analyze and /api/refresh.

    Args:
        game_name: Player's game name
        tag_line: Player's tag line
        platform: Platform/region (default: euw1)
        match_count: Number of matches to analyze (default: 15)
        force_refresh: Skip cache check and force fresh analysis
        story_mode: 'coach' for helpful advice or 'roast' for savage humor (default: coach)

    Returns:
        tuple: (response_data, error_message, status_code)
    """
    try:
        riot_id = f"{game_name}#{tag_line}"

        # Check cache first (skip if force_refresh)
        if not force_refresh:
            cached_response = check_cached_stories(riot_id, story_mode)
            if cached_response:
                return (cached_response, None, 200)

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

                # Save player to database
                save_player_to_database(player, riot_id, platform)

                # Analyze zones
                zone_stats = analyze_player_zones(player.processed_stats)

                print(f"\nZone Analysis Results: {len(zone_stats)} zones")
                for zid, zstats in zone_stats.items():
                    if isinstance(zstats, dict):
                        print(f"  {zid}: {len(zstats)} fields")
                    else:
                        print(f"  {zid}: INVALID TYPE - {type(zstats)}")

                # Generate and store stories
                stories = generate_and_store_stories(player, zone_stats, riot_id, story_mode)

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
        match_count = data.get('matchCount', 10)
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

        print(f"Story mode: {story_mode.upper()}")

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


@app.route('/api/generate-story/<path:riot_id>/<zone_id>', methods=['POST'])
def generate_zone_story_endpoint(riot_id, zone_id):
    """
    Generate a story for a specific zone on-demand.

    Request body (optional):
    {
        "storyMode": "coach" or "roast"
    }

    Response:
    {
        "zone_id": "baron_pit",
        "zone_name": "Baron Nashor",
        "story": "AI-generated story text",
        "stats": {...},
        "generated_at": timestamp
    }
    """
    try:
        print(f"\n{'='*60}")
        print(f"ROUTE HIT: /api/generate-story/{riot_id}/{zone_id}")
        print(f"  Raw riot_id: {repr(riot_id)}")
        print(f"  Raw zone_id: {repr(zone_id)}")
        print(f"{'='*60}\n")

        is_valid, error = validate_riot_id(riot_id)
        if not is_valid:
            print(f"Validation failed for riot_id: {error}")
            return jsonify({'error': error}), 400

        is_valid, error = validate_zone_id(zone_id)
        if not is_valid:
            print(f"Validation failed for zone_id: {error}")
            return jsonify({'error': error}), 400

        riot_id_parsed = parse_riot_id(riot_id)
        player = player_repo.get_by_riot_id(riot_id_parsed)
        if not player:
            return jsonify({'error': 'Player not found'}), 404

        data = request.get_json(silent=True) or {}
        story_mode = data.get('storyMode', 'coach')

        is_valid, error = validate_story_mode(story_mode)
        if not is_valid:
            return jsonify({'error': error}), 400
        if not story_mode:
            story_mode = 'coach'

        print(f"\n{'='*60}")
        print(f"Story Generation Request")
        print(f"  Riot ID: {riot_id} -> {riot_id_parsed}")
        print(f"  Zone: {zone_id}")
        print(f"  Mode: {story_mode}")
        print(f"  Player PUUID: {player.puuid}")
        print(f"{'='*60}\n")

        # First, check if we already have cached data for this zone
        existing_story = get_story(player.puuid, zone_id)

        if existing_story:
            print(f"  Found existing story entry for {zone_id}")
            print(f"  Story text length: {len(existing_story.get('story_text', ''))}")
            print(f"  Has stats: {bool(existing_story.get('stats'))}")
            print(f"  Cached mode: {existing_story.get('story_mode', 'unknown')}")

        if existing_story:
            cached_mode = existing_story.get('story_mode', 'coach')
            cached_story_text = existing_story.get('story_text', '').strip()
            zone_stats = existing_story.get('stats', {})

            # Case 1: Story exists and mode matches - return cached story
            if cached_story_text and cached_mode == story_mode:
                print(f"  Using fully cached story for {zone_id}")
                return jsonify({
                    'zone_id': zone_id,
                    'zone_name': existing_story.get('zone_name', zone_id),
                    'story': cached_story_text,
                    'stats': zone_stats,
                    'story_mode': story_mode,
                    'generated_at': existing_story.get('generated_at')
                }), 200

            # Case 2: Stats cached but no story yet OR mode mismatch - generate story quickly
            # Verify stats are valid (not just an empty dict)
            if zone_stats and isinstance(zone_stats, dict) and len(zone_stats) > 2:  # More than just zone_id and zone_name
                print(f"  Generating story using cached stats (fast: ~1-2s)")
                print(f"  Stats keys: {list(zone_stats.keys())}")
                from API.story.story_generator import generate_zone_story
                story_text = generate_zone_story(zone_id, zone_stats, story_mode)

                if story_text:
                    # Store the generated story
                    store_story(
                        player.puuid,
                        zone_id,
                        story_text,
                        zone_stats.get('zone_name', zone_id),
                        zone_stats,
                        story_mode
                    )

                    return jsonify({
                        'zone_id': zone_id,
                        'zone_name': zone_stats.get('zone_name', zone_id),
                        'story': story_text,
                        'stats': zone_stats,
                        'story_mode': story_mode,
                        'generated_at': int(time.time())
                    }), 200
                else:
                    # AI generation failed - return error
                    print(f"  ERROR: AI failed to generate story for {zone_id}")
                    return jsonify({
                        'error': f'AI story generation failed for zone {zone_id}. Please try again.',
                        'zone_id': zone_id
                    }), 500
            else:
                # Stats are empty or invalid - fall through to fetch from API
                print(f"  WARNING: Stats are empty or invalid for {zone_id}, will fetch from Riot API")

        # No cached story or stats - need to fetch from Riot API (slow path)
        print(f"  No cached data - fetching from Riot API (this may take 30-60s)...")

        async def generate_story_for_zone():
            parts = riot_id_parsed.split('#')
            if len(parts) != 2:
                return None, "Invalid riot_id format"

            game_name, tag_line = parts
            platform = player.platform if hasattr(player, 'platform') else 'euw1'

            async with Player(game_name, tag_line, platform=platform) as player_obj:
                # Load profile and matches
                success = await player_obj.load_profile()
                if not success:
                    return None, "Failed to load player profile"

                await player_obj.load_recent_matches(count=15)

                if not player_obj.processed_stats:
                    return None, "No match data found"

                await player_obj.load_match_timelines()
                player_obj.process_matches()

                # Extract stats for this specific zone
                from API.analytics.zones.zone_analyzer import extract_zone_stats
                zone_stats = extract_zone_stats(player_obj.processed_stats, zone_id)

                if not zone_stats or not isinstance(zone_stats, dict) or len(zone_stats) <= 2:
                    print(f"  ERROR: No valid stats extracted for {zone_id}")
                    print(f"  Stats: {zone_stats}")
                    return None, f"No statistics available for zone {zone_id}. This zone may not have enough data from your recent matches."

                # Generate story
                from API.story.story_generator import generate_zone_story
                story_text = generate_zone_story(zone_id, zone_stats, story_mode)

                if not story_text:
                    return None, "Failed to generate story"

                # Store for future use
                store_story(
                    player_obj.puuid,
                    zone_id,
                    story_text,
                    zone_stats.get('zone_name', zone_id),
                    zone_stats,
                    story_mode
                )

                return {
                    'zone_id': zone_id,
                    'zone_name': zone_stats.get('zone_name', zone_id),
                    'story': story_text,
                    'stats': zone_stats,
                    'story_mode': story_mode,
                    'generated_at': int(time.time())
                }, None

        result, error = run_async(generate_story_for_zone())

        if error:
            return jsonify({'error': error}), 500

        return jsonify(result), 200

    except Exception as e:
        error_details = {
            'error': 'Failed to generate story',
            'details': str(e),
            'type': type(e).__name__
        }
        print(f"Error in /api/generate-story: {e}")
        traceback.print_exc()
        return jsonify(error_details), 500


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
        match_count = data.get('matchCount', 15)
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

        print(f"Refresh with story mode: {story_mode.upper()}")

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

@app.route('/api/generate-card/<riot_id>', methods=['GET'])
def generate_card(riot_id):
    """Generate player card image by fetching fresh data from Riot API"""
    try:
        # Validate riot_id
        is_valid, error = validate_riot_id(riot_id)
        if not is_valid:
            return jsonify({'error': error}), 400

        riot_id_parsed = parse_riot_id(riot_id)
        parts = riot_id_parsed.split('#')
        if len(parts) != 2:
            return jsonify({'error': 'Invalid riot_id format'}), 400

        game_name, tag_line = parts

        # Get player from DB to find story mode
        db_player = player_repo.get_by_riot_id(riot_id_parsed)
        if not db_player:
            return jsonify({'error': 'Player not found'}), 404

        # Get story mode from cached stories
        stories = get_all_stories(db_player.puuid)
        intro_story = next((s for s in stories if s['zone_id'] == 'intro'), None) if stories else None
        story_mode = intro_story.get('story_mode', 'coach') if intro_story else 'coach'

        platform = 'euw1'  # Default platform

        print(f"Fetching fresh player data from Riot API for {riot_id_parsed}...")

        # Fetch FRESH data from Riot API using Player class
        async def fetch_player_data():
            async with Player(game_name, tag_line, platform=platform) as player:
                # Load profile (gets summoner info, rank, champion mastery)
                success = await player.load_profile()
                if not success:
                    return None

                # Load recent matches to calculate stats
                await player.load_recent_matches(count=15)

                if not player.processed_stats:
                    return None

                # Process matches to get aggregated stats
                player.process_matches()

                return player

        player = run_async(fetch_player_data())

        if not player:
            return jsonify({'error': 'Failed to fetch player data'}), 500

        # Extract level from summoner_info
        lvl = player.summoner_info.get('summonerLevel', 100) if player.summoner_info else 100

        # Extract rank from rank_info
        rank = 'Unranked'
        if player.rank_info:
            for queue in player.rank_info:
                if queue.get('queueType') == 'RANKED_SOLO_5x5':
                    tier = queue.get('tier', 'Unranked')
                    division = queue.get('rank', '')
                    rank = f"{tier} {division}".strip()
                    break

        # Calculate stats from processed_stats
        matches = player.processed_stats
        total_matches = len(matches)

        # Calculate KDA
        total_kills = sum(m.get('kills', 0) for m in matches)
        total_deaths = sum(m.get('deaths', 0) for m in matches)
        total_assists = sum(m.get('assists', 0) for m in matches)
        kda = (total_kills + total_assists) / max(total_deaths, 1)

        # Calculate winrate
        wins = sum(1 for m in matches if m.get('win', False))
        winrate = (wins / total_matches * 100) if total_matches > 0 else 0.0

        # Get most played champion from processed_stats (count champion occurrences)
        champion_played = 'Unknown'
        if matches:
            from collections import Counter
            champion_counts = Counter(m.get('champion_name', 'Unknown') for m in matches)
            if champion_counts:
                champion_played = champion_counts.most_common(1)[0][0]

        print(f"Player data extracted:")
        print(f"  Champion: {champion_played}, Games: {total_matches}, KDA: {kda:.2f}")
        print(f"  Rank: {rank}, Level: {lvl}, Winrate: {winrate:.1f}%")

        # Generate AI-powered title and story for the card
        print(f"Generating AI card content ({story_mode} mode)...")
        card_content = generate_card_content_with_fallback(
            player_stats={
                'champion_played': champion_played,
                'games_played': total_matches,
                'kda': kda,
                'rank': rank,
                'winrate': winrate
            },
            story_mode=story_mode
        )

        title = card_content.get('title', 'The Legend')
        story = card_content.get('story', 'A summoner of great skill')

        profil = RewindExportProfil(
            player_name=game_name,
            champion_played=champion_played,
            games_played=total_matches,
            kd=kda,
            lvl=lvl,
            rank=rank,
            title=title,
            story=story
        )

        generator = RewindCardGeneration(profil)
        success = generator.create_card()

        if not success:
            return jsonify({'error': 'Failed to generate card'}), 500

        filename = f"{game_name}_rewind_card.png"
        with open(filename, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        os.remove(filename)

        return jsonify({
            'success': True,
            'image': f"data:image/png;base64,{image_data}",
            'player_name': game_name
        }), 200

    except Exception as e:
        print(f"Error generating card: {e}")
        traceback.print_exc()
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/matches', methods=['POST'])
def get_matches():
    """
    Fetch player match history

    Request body:
    {
        "session_token": "uuid-token"
    }

    Response:
    {
        "matches": [
            {
                "match_id": "...",
                "result": "win" or "loss",
                "champion": "Champion Name",
                "championIcon": "🦊",
                "kda": "12/3/8",
                "cs": "245",
                "duration": "32:15",
                "role": "Mid",
                "timeAgo": "2 hours ago",
                "timestamp": 1234567890
            }
        ]
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'Invalid JSON'}), 400

        session_token = data.get('session_token')

        if not session_token:
            return jsonify({'error': 'session_token is required'}), 400

        # Validate session token
        puuid = session_repo.get_puuid_from_session(session_token)

        if not puuid:
            return jsonify({'error': 'Invalid or expired session'}), 401

        # Fetch matches from DynamoDB
        from db.src.repositories.match_repository import MatchRepository
        match_repo = MatchRepository(dynamodb)

        matches = match_repo.get_recent_matches(puuid, count=20)

        if not matches:
            return jsonify({'matches': []}), 200

        # Format matches for frontend
        formatted_matches = []
        for match in matches:
            match_data = match.match_data

            # Convert Decimals to int/float for JSON serialization
            from decimal import Decimal
            def decimal_to_number(obj):
                if isinstance(obj, list):
                    return [decimal_to_number(item) for item in obj]
                elif isinstance(obj, dict):
                    return {key: decimal_to_number(value) for key, value in obj.items()}
                elif isinstance(obj, Decimal):
                    return int(obj) if obj % 1 == 0 else float(obj)
                else:
                    return obj

            match_data = decimal_to_number(match_data)

            info = match_data.get('info', {})
            participants = info.get('participants', [])

            # Find this player's data
            player_data = next((p for p in participants if p.get('puuid') == puuid), None)

            if not player_data:
                continue

            # Extract match details
            champion_name = player_data.get('championName', 'Unknown')
            kills = int(player_data.get('kills', 0))
            deaths = int(player_data.get('deaths', 0))
            assists = int(player_data.get('assists', 0))
            cs = int(player_data.get('totalMinionsKilled', 0)) + int(player_data.get('neutralMinionsKilled', 0))
            win = player_data.get('win', False)
            role = player_data.get('teamPosition', 'UTILITY')
            game_duration = info.get('gameDuration', 0)

            # Format duration as MM:SS
            minutes = game_duration // 60
            seconds = game_duration % 60
            duration_str = f"{minutes}:{seconds:02d}"

            # Format time ago
            import time
            current_time = int(time.time())
            time_diff = current_time - match.timestamp

            if time_diff < 3600:
                time_ago = f"{time_diff // 60} minutes ago"
            elif time_diff < 86400:
                time_ago = f"{time_diff // 3600} hours ago"
            else:
                time_ago = f"{time_diff // 86400} days ago"

            # Map role names
            role_map = {
                'TOP': 'Top',
                'JUNGLE': 'Jungle',
                'MIDDLE': 'Mid',
                'BOTTOM': 'ADC',
                'UTILITY': 'Support'
            }
            role_display = role_map.get(role, role)

            # Get champion emoji (basic mapping)
            champion_emoji = get_champion_emoji(champion_name)

            formatted_matches.append({
                'match_id': match.match_id,
                'result': 'win' if win else 'loss',
                'champion': champion_name,
                'championIcon': champion_emoji,
                'kda': f"{kills}/{deaths}/{assists}",
                'cs': str(cs),
                'duration': duration_str,
                'role': role_display,
                'timeAgo': time_ago,
                'timestamp': match.timestamp
            })

        return jsonify({'matches': formatted_matches}), 200

    except Exception as e:
        print(f"Error in /api/matches: {e}")
        traceback.print_exc()
        return jsonify({'error': 'Internal server error'}), 500


def get_champion_emoji(champion_name):
    """Get an emoji for a champion (basic mapping)"""
    emoji_map = {
        'Ahri': '🦊',
        'Yasuo': '⚔️',
        'Zed': '🥷',
        'Jinx': '💣',
        'Vayne': '🏹',
        'Lee Sin': '🥋',
        'Teemo': '🍄',
        'Lux': '✨',
        'Ezreal': '🎯',
        'Darius': '🪓',
        'Garen': '⚔️',
        'Miss Fortune': '💰',
        'Ashe': '❄️',
        'Thresh': '⛓️',
        'Blitzcrank': '🤖',
        'Annie': '🔥',
        'Malphite': '🪨',
        'Master Yi': '⚡',
        'Katarina': '🗡️',
        'Akali': '🌙',
        'Caitlyn': '🎯',
        'Jhin': '🎭',
        'Draven': '🪓',
        'Lucian': '🔫',
        'Viktor': '⚡',
        'Syndra': '🔮',
        'Xerath': '⚡',
        'Brand': '🔥',
        'Nami': '🌊',
        'Janna': '💨',
        'Sona': '🎵',
        'Soraka': '⭐',
        'Leona': '☀️',
        'Diana': '🌙',
        'Kayn': '👿',
        'Aatrox': '😈',
        'Riven': '⚔️',
        'Fiora': '🤺',
        'Irelia': '💃',
        'Camille': '🦿',
        'Jax': '🪨',
        'Nasus': '🐕',
        'Renekton': '🐊',
        'Vladimir': '🩸',
        'Fizz': '🐟',
        'Ekko': '⏰',
        'Twisted Fate': '🃏',
        'Veigar': '🧙',
        'Kassadin': '🌌',
        'Kayle': '😇',
        'Morgana': '😈',
        'Swain': '🦅',
        'Azir': '🏜️',
        'Orianna': '⚙️',
        'Zilean': '⏰',
        'Bard': '🎵',
        'Ivern': '🌳',
        'Pyke': '🔪',
        'Nautilus': '⚓',
        'Alistar': '🐂',
        'Braum': '🛡️',
        'Taric': '💎',
        'Shen': '🥷',
        'Rammus': '🦔',
        'Shaco': '🤡',
        'Kindred': '🐺',
        'Elise': '🕷️',
        'Nidalee': '🐆',
        'Rengar': '🦁',
        'Kha\'Zix': '🦗',
        'Rek\'Sai': '🦈',
        'Vi': '👊',
        'Sett': '👊',
        'Viego': '👑',
        'Gwen': '✂️',
        'Akshan': '🪃',
        'Samira': '🔫',
        'Aphelios': '🌙',
        'Senna': '🔫',
        'Seraphine': '🎤',
        'Yone': '👹',
        'Lillia': '🦌',
        'Rell': '🐴',
        'Vex': '😑',
        'Zeri': '⚡',
        'Renata Glasc': '⚗️',
        'K\'Sante': '🛡️',
        'Milio': '🔥',
        'Naafiri': '🐕',
        'Briar': '🩸',
        'Hwei': '🎨',
        'Smolder': '🐉',
    }
    return emoji_map.get(champion_name, '⚔️')


@app.route('/api/coach', methods=['POST'])
def coach_endpoint():
    """
    AI Coaching Chat Endpoint

    Request body:
    {
        "session_token": "uuid-token",
        "message": "user's question",
        "conversationHistory": [ {role, content, timestamp}, ... ],
        "playerData": {...} (optional)
    }

    Response:
    {
        "response": "AI coaching advice"
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'Invalid JSON'}), 400

        session_token = data.get('session_token')
        user_message = data.get('message', '')
        conversation_history = data.get('conversationHistory', [])

        if not session_token:
            return jsonify({'error': 'session_token is required'}), 400

        if not user_message:
            return jsonify({'error': 'message is required'}), 400

        print(f"\n{'='*60}")
        print(f"Chat Request")
        print(f"Message: {user_message}")
        print(f"Session: {session_token[:16]}...")
        print(f"{'='*60}\n")

        # Validate session token
        puuid = session_repo.get_puuid_from_session(session_token)

        if not puuid:
            return jsonify({'error': 'Invalid or expired session'}), 401

        # Extract player name from session token (since session has riot_id)
        session = session_repo.get_session(session_token)
        player_name = session.riot_id if session else f"Player ({puuid[:8]})"

        print(f"Session valid for player: {player_name}")

        # Set PUUID for tool use (match history access)
        set_player_puuid(puuid)

        # Load recent conversations from DynamoDB (last 3 conversations)
        recent_conversations = []
        try:
            recent_conversations = conversation_repo.get_recent_conversations(puuid, count=3)
            if recent_conversations:
                print(f"Loaded {len(recent_conversations)} previous conversation(s)")
        except Exception as e:
            print(f"Could not load conversation history: {e}")

        # Build system prompt with player context
        system_prompt = SYSTEM_PROMPT
        system_prompt += f"\n\nPLAYER CONTEXT:\nPlayer: {player_name}\n"

        # Add conversation history context to system prompt
        if recent_conversations:
            history_context = "\n\nRECENT CONVERSATION HISTORY:\n"
            history_context += "You have chatted with this player before. Here are summaries of recent conversations:\n\n"

            for idx, conv in enumerate(reversed(recent_conversations), 1):
                history_context += f"--- Conversation {idx} (from {conv.created_at[:10]}) ---\n"
                # Include last few messages from each conversation
                for msg in conv.messages[-4:]:  # Last 4 messages per conversation
                    role_label = "Player" if msg.role == "user" else "You"
                    history_context += f"{role_label}: {msg.content[:150]}{'...' if len(msg.content) > 150 else ''}\n"
                history_context += "\n"

            history_context += "Use this context to remember the player's preferences, past discussions, and provide continuity.\n"
            system_prompt += history_context

        # Initialize messages with system prompt
        messages = [SystemMessage(content=system_prompt)]

        # Add conversation history (last 6 messages for context)
        if conversation_history:
            for msg in conversation_history[-6:]:
                role = msg.get('role', 'user')
                content = msg.get('content', '')

                if role == 'user':
                    messages.append(HumanMessage(content=content))
                elif role == 'ai':
                    messages.append(AIMessage(content=content))

        # Add current user message
        messages.append(HumanMessage(content=user_message))

        # Create chat model with tools
        chat = create_chat()

        # Tool use loop - continue until we get a final response
        max_iterations = 10
        iteration = 0

        while iteration < max_iterations:
            iteration += 1

            # Get AI response with retry logic
            max_retries = 5
            for attempt in range(max_retries):
                try:
                    response = chat.invoke(messages)
                    break
                except Exception as retry_error:
                    error_str = str(retry_error)
                    # Check for rate limiting
                    is_rate_limit = any(keyword in error_str.lower() for keyword in [
                        "too many requests",
                        "too many connections",
                        "throttlingexception",
                        "throttling"
                    ])
                    if is_rate_limit and attempt < max_retries - 1:
                        wait_time = (2 ** attempt) * 2
                        print(f"Rate limited. Waiting {wait_time}s before retry...")
                        time.sleep(wait_time)
                    else:
                        raise

            # Add AI response to history
            messages.append(response)

            # Check if Claude wants to use tools
            if hasattr(response, 'tool_calls') and response.tool_calls:
                # Claude is requesting tool use
                print(f"AI using {len(response.tool_calls)} tool(s)")

                for tool_call in response.tool_calls:
                    tool_name = tool_call['name']
                    tool_input = tool_call['args']
                    tool_use_id = tool_call['id']

                    print(f"   Tool: {tool_name}({json.dumps(tool_input)})")

                    # Execute the tool
                    tool_result = execute_tool(tool_name, tool_input)

                    # Add tool result to messages
                    messages.append(ToolMessage(
                        content=json.dumps(tool_result, indent=2),
                        tool_call_id=tool_use_id
                    ))

                # Continue loop to get Claude's response after using tools
                continue
            else:
                # No more tool calls - we have final response
                ai_response = response.content

                print(f"AI Response: {ai_response[:100]}...")

                # Save conversation to DynamoDB
                try:
                    from db.src.models.conversation import Conversation

                    # Create new conversation
                    conv = Conversation.create_new(puuid)
                    conv.add_message("user", user_message)
                    conv.add_message("assistant", ai_response)
                    conversation_repo.create_conversation(conv)

                    print("Conversation saved to DynamoDB")
                except Exception as db_error:
                    print(f"Could not save conversation: {db_error}")

                return jsonify({
                    'response': ai_response,
                    'status': 'success'
                }), 200

        # Max iterations reached
        return jsonify({
            'error': 'AI processing took too long',
            'response': 'I apologize, but I need to simplify my analysis. Could you rephrase your question?'
        }), 200

    except Exception as e:
        print(f"\nError in /api/coach: {e}")
        traceback.print_exc()

        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500


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
