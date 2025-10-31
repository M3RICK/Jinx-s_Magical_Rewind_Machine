import sys
import os
import time
import json
import uuid

# Add parent directories to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv
from langchain_aws import ChatBedrock
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from riot_client.riot.account import RiotAccountAPI
from db.src.db_handshake import get_dynamodb_reasources

# Load environment variables
load_dotenv()

# Region mapping for Riot API
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

def validate_riot_account(game_name, tag_line, region_config):
    """Validate if Riot account exists and return PUUID."""
    print(f"\n[INFO] Looking up Riot account: {game_name}#{tag_line}...")

    try:
        riot_api = RiotAccountAPI()
        puuid = riot_api.get_puuid(game_name, tag_line, region=region_config["region"])

        if puuid:
            print(f"[SUCCESS] Riot account found! PUUID: {puuid[:8]}...")
            return puuid
        else:
            print("[ERROR] Riot account not found. Please check the name and tag.")
            return None
    except Exception as e:
        print(f"[ERROR] Error validating Riot account: {e}")
        return None

def check_or_create_player(puuid, game_name, tag_line):
    """Check if player exists in DynamoDB, create if not."""
    print(f"\n[INFO] Checking player database...")

    try:
        dynamodb = get_dynamodb_reasources()
        table = dynamodb.Table('Players')

        # Try to get existing player
        response = table.get_item(Key={'puuid': puuid})

        if 'Item' in response:
            print(f"[SUCCESS] Welcome back! Found existing player record.")
            return response['Item']
        else:
            # Create new player record
            print(f"[INFO] First time user! Creating new player record...")

            player_uuid = str(uuid.uuid4())
            player_data = {
                'puuid': puuid,
                'player_uuid': player_uuid,
                'game_name': game_name,
                'tag_line': tag_line,
                'created_at': int(time.time()),
                'last_accessed': int(time.time())
            }

            table.put_item(Item=player_data)
            print(f"[SUCCESS] Player record created! UUID: {player_uuid[:8]}...")

            return player_data

    except Exception as e:
        print(f"[ERROR] Database error: {e}")
        return None

def run_chat(session_token=None):
    """Start AI coaching chat with player lookup."""
    print("\n" + "=" * 50)
    print("  RiftRewind AI Coaching Chat")
    print("=" * 50)

    # Get player information
    game_name, tag_line = get_player_input()
    region_config = get_region_input()

    # Validate Riot account
    puuid = validate_riot_account(game_name, tag_line, region_config)
    if not puuid:
        print("\n[ERROR] Cannot proceed without valid Riot account.")
        return

    # Check or create player in database
    player_data = check_or_create_player(puuid, game_name, tag_line)
    if not player_data:
        print("\n[ERROR] Database error. Cannot proceed.")
        return

    print("\n" + "=" * 50)
    print(f"  Chat session ready for {game_name}#{tag_line}")
    print("=" * 50)
    print("\n[INFO] Chat functionality coming soon...")
    print("Player UUID:", player_data.get('player_uuid'))

    # TODO: Initialize AI chat session with player context
    # TODO: Load player stats and pass to AI
    # TODO: Implement chat loop
