import sys
import os
import asyncio

# Add parent directories to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv
from API.Core import Core
from API.riot.account import RiotAccountAPI
from app.cli.client_check import check_and_build_client

# Load environment variables
load_dotenv()

# Helper function to call async API from sync code
def get_puuid_from_riot(riot_id, region):
    """
    Wrapper to call async Riot API from synchronous CLI code.

    Args:
        riot_id: "Name#TAG" format
        region: Region like "americas", "europe", "asia"

    Returns:
        PUUID string or None if not found
    """
    async def _fetch():
        async with Core() as core:
            riot_api = RiotAccountAPI(core)

            # Split riot_id into name and tag
            parts = riot_id.split('#')
            if len(parts) != 2:
                return None

            game_name, tag_line = parts[0], parts[1]
            puuid = await riot_api.get_puuid(game_name, tag_line, region=region)
            return puuid

    # Run the async function
    return asyncio.run(_fetch())

# Region mapping for Riot API
# TODO: Consolidate duplicate region mappings across codebase
REGION_MAP = {
    "na": {"region": "americas", "platform": "na1"},
    "na1": {"region": "americas", "platform": "na1"},
    "euw": {"region": "europe", "platform": "euw1"},
    "euw1": {"region": "europe", "platform": "euw1"},
    "eune": {"region": "europe", "platform": "eun1"},
    "eun1": {"region": "europe", "platform": "eun1"},
    "kr": {"region": "asia", "platform": "kr"},
    "jp": {"region": "asia", "platform": "jp1"},
    "jp1": {"region": "asia", "platform": "jp1"},
    "br": {"region": "americas", "platform": "br1"},
    "br1": {"region": "americas", "platform": "br1"},
    "lan": {"region": "americas", "platform": "la1"},
    "la1": {"region": "americas", "platform": "la1"},
    "las": {"region": "americas", "platform": "la2"},
    "la2": {"region": "americas", "platform": "la2"},
    "oce": {"region": "sea", "platform": "oc1"},
    "oc1": {"region": "sea", "platform": "oc1"},
    "tr": {"region": "europe", "platform": "tr1"},
    "tr1": {"region": "europe", "platform": "tr1"},
    "ru": {"region": "europe", "platform": "ru"},
}

def get_player_input():
    """Get player name and tag from user."""
    print("\n" + "=" * 50)
    print("  Player Identification")
    print("=" * 50)

    while True:
        player_input = input("\nEnter player name (format: Name#TAG): ").strip()

        if "#" not in player_input:
            print("[ERROR] Invalid format. Please use format: Name#TAG (e.g., Faker#KR1)")
            continue

        parts = player_input.split("#")
        if len(parts) != 2:
            print("[ERROR] Invalid format. Please use format: Name#TAG")
            continue

        game_name, tag_line = parts[0].strip(), parts[1].strip()

        if not game_name or not tag_line:
            print("[ERROR] Both name and tag are required")
            continue

        return game_name, tag_line

def get_region_input():
    """Get region from user."""
    print("\n" + "-" * 50)
    print("Available regions:")
    print("  NA, EUW, EUNE, KR, JP, BR, LAN, LAS, OCE, TR, RU")
    print("-" * 50)

    while True:
        region_input = input("\nEnter region: ").strip().lower()

        if region_input in REGION_MAP:
            return REGION_MAP[region_input]

        print(f"[ERROR] Invalid region '{region_input}'. Please choose from the list above.")

def validate_and_authenticate_player(riot_id, platform):
    """
    Validate Riot account and authenticate player.

    Flow:
    1. Check if riot_id exists in Riot API
    2. Check if player exists in database
    3. If not, create player in database
    4. Create session token

    Returns:
        Tuple of (session_token, player) or (None, None) if failed
    """
    print(f"\n[STEP 1/2] Validating Riot account: {riot_id}...")

    try:
        # Map platform to region for Riot API
        # TODO: Consolidate duplicate region mappings across codebase
        region_to_riot_region = {
            "na1": "americas",
            "br1": "americas",
            "la1": "americas",
            "la2": "americas",
            "euw1": "europe",
            "eun1": "europe",
            "tr1": "europe",
            "ru": "europe",
            "kr": "asia",
            "jp1": "asia",
            "oc1": "sea"
        }

        riot_region = region_to_riot_region.get(platform, "americas")

        # Use your friend's async API
        puuid = get_puuid_from_riot(riot_id, riot_region)

        if not puuid:
            print(f"[ERROR] Riot account '{riot_id}' not found in region '{platform}'")
            print("[TIP] Make sure you're using the correct region")
            return None, None

        print(f"[SUCCESS] Riot account found! PUUID: {puuid[:16]}...")

    except Exception as e:
        print(f"[ERROR] Failed to validate Riot account: {e}")
        import traceback
        traceback.print_exc()
        return None, None

    print(f"\n[STEP 2/2] Checking database...")

    try:
        # Check and build/update player profile in database
        success, player, session_token = check_and_build_client(puuid, riot_id, riot_region, platform)

        if success and player and session_token:
            print(f"[SUCCESS] Player authenticated!")
            return session_token, player
        else:
            print("[ERROR] Failed to authenticate player")
            return None, None

    except Exception as e:
        print(f"[ERROR] Database error: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def run_chat(session_token=None):
    """Start AI coaching chat with player lookup."""
    print("\n" + "=" * 50)
    print("  RiftRewind AI Coaching Chat")
    print("=" * 50)

    # Get player information
    game_name, tag_line = get_player_input()
    riot_id = f"{game_name}#{tag_line}"

    region_config = get_region_input()
    platform = region_config["platform"]  # Platform (na1, euw1, etc.)

    # Validate and authenticate player
    session_token, player = validate_and_authenticate_player(riot_id, platform)

    if not player:
        print("\n[ERROR] Cannot proceed without valid player.")
        return

    # Display player info
    print("\n" + "=" * 50)
    print(f"  Chat Session Ready")
    print("=" * 50)
    print(f"Player: {player.riot_id}")
    print(f"Region: {player.region}")
    print(f"PUUID: {player.puuid[:16]}...")
    print(f"Session Token: {session_token[:16]}...")

    if player.main_role:
        print(f"Main Role: {player.main_role}")
    if player.winrate:
        print(f"Winrate: {player.winrate}%")
    if player.current_rank:
        print(f"Rank: {player.current_rank.tier} {player.current_rank.division}")

    print("=" * 50)

    # Build AI context with player data and privacy rules
    from app.cli.ai_context import build_ai_context_from_player
    ai_context = build_ai_context_from_player(player)

    # Start AI coaching session
    print("\n[INFO] Starting AI coaching session...")

    # Import AI chat module
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend', 'src'))
    from ai_chat import start_chat_session

    # Launch chat with player context
    start_chat_session(player_context=ai_context)