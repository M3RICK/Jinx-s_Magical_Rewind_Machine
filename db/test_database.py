"""
Simple test script for the database setup.
Tests all tables and operations.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from db.src.db_handshake import get_dynamodb_reasources
from db.src.models.player import Player, RankInfo
from db.src.models.match_history import MatchHistory
from db.src.models.conversation import Conversation
from db.src.models.session import Session
from db.src.repositories.player_repository import PlayerRepository
from db.src.repositories.match_repository import MatchRepository
from db.src.repositories.conversation_repository import ConversationRepository
from db.src.repositories.session_repository import SessionRepository


def test_connection():
    """Test database connection"""
    print("\n[TEST 1] Testing database connection...")
    try:
        dynamodb = get_dynamodb_reasources()
        client = dynamodb.meta.client
        response = client.list_tables()
        print(f"Connected! Found {len(response['TableNames'])} tables")
        print(f"  Tables: {', '.join(response['TableNames'])}")
        return True
    except Exception as e:
        print(f"Connection failed: {e}")
        return False


def test_player_operations():
    """Test player CRUD operations"""
    print("\n[TEST 2] Testing Player operations...")

    try:
        dynamodb = get_dynamodb_reasources()
        player_repo = PlayerRepository(dynamodb)

        # Create a test player
        test_player = Player(
            puuid="test_puuid_12345",
            riot_id="TestPlayer#NA1",
            region="na1",
            main_role="MID",
            main_champions=["Ahri", "Syndra", "Orianna"],
            winrate=55.5,
            current_rank=RankInfo(tier="GOLD", division="II", lp=50)
        )

        print("  Creating test player...")
        player_repo.create(test_player)
        print("  Player created")

        # Retrieve by PUUID
        print("  Retrieving by PUUID...")
        retrieved = player_repo.get_by_puuid("test_puuid_12345")
        if retrieved and retrieved.riot_id == "TestPlayer#NA1":
            print("  Retrieved by PUUID")
        else:
            print("  Failed to retrieve by PUUID")
            return False

        # Retrieve by Riot ID
        print("  Retrieving by Riot ID...")
        retrieved = player_repo.get_by_riot_id("TestPlayer#NA1")
        if retrieved and retrieved.puuid == "test_puuid_12345":
            print("  Retrieved by Riot ID (GSI working!)")
        else:
            print("  Failed to retrieve by Riot ID")
            return False

        # Update player
        print("  Updating player...")
        test_player.winrate = 60.0
        player_repo.update(test_player)
        updated = player_repo.get_by_puuid("test_puuid_12345")
        if updated.winrate == 60.0:
            print("  Player updated")
        else:
            print("  Update failed")
            return False

        # Clean up
        print("  Cleaning up...")
        player_repo.delete("test_puuid_12345")
        print("  Player deleted")

        return True

    except Exception as e:
        print(f"  Player operations failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_match_operations():
    """Test match history operations"""
    print("\n[TEST 3] Testing MatchHistory operations...")

    try:
        dynamodb = get_dynamodb_reasources()
        match_repo = MatchRepository(dynamodb)

        # Create test matches
        print("  Creating test matches...")
        test_matches = []
        for i in range(5):
            match = MatchHistory(
                puuid="test_puuid_12345",
                match_id=f"NA1_match_{i}",
                timestamp=1700000000 + i * 1000,
                match_data={"gameId": i, "test": "data"}
            )
            test_matches.append(match)
            match_repo.save_match(match)

        print(f"  Created {len(test_matches)} matches")

        # Retrieve matches
        print("  Retrieving matches...")
        retrieved = match_repo.get_player_matches("test_puuid_12345")
        if len(retrieved) == 5:
            print(f"  Retrieved {len(retrieved)} matches")
        else:
            print(f"  Expected 5 matches, got {len(retrieved)}")
            return False

        # Get recent matches (sorted by timestamp)
        print("  Getting recent matches...")
        recent = match_repo.get_recent_matches("test_puuid_12345", count=3)
        if len(recent) == 3:
            print("  Got 3 most recent matches (LSI working!)")
        else:
            print(f"  Expected 3 matches, got {len(recent)}")
            return False

        # Clean up
        print("  Cleaning up...")
        for match in test_matches:
            match_repo.delete_match("test_puuid_12345", match.match_id)
        print("  Matches deleted")

        return True

    except Exception as e:
        print(f"  Match operations failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_conversation_operations():
    """Test conversation operations"""
    print("\n[TEST 4] Testing Conversation operations...")

    try:
        dynamodb = get_dynamodb_reasources()
        conv_repo = ConversationRepository(dynamodb)

        # Create test conversation
        print("  Creating test conversation...")
        test_conv = Conversation.create_new("test_puuid_12345", session_id="test_session")
        conv_repo.create_conversation(test_conv)
        print("  Conversation created")

        # Add messages
        print("  Adding messages...")
        test_conv.add_message("user", "Hello coach!")
        test_conv.add_message("assistant", "Hello! How can I help?")
        conv_repo.update_conversation(test_conv)
        print("  Messages added")

        # Retrieve conversation
        print("  Retrieving conversation...")
        retrieved = conv_repo.get_conversation("test_puuid_12345", test_conv.conversation_id)
        if retrieved and len(retrieved.messages) == 2:
            print(f"  Retrieved conversation with {len(retrieved.messages)} messages")
        else:
            print("  Failed to retrieve conversation")
            return False

        # Clean up
        print("  Cleaning up...")
        conv_repo.delete_conversation("test_puuid_12345", test_conv.conversation_id)
        print("  Conversation deleted")

        return True

    except Exception as e:
        print(f"  Conversation operations failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_session_operations():
    """Test session operations"""
    print("\n[TEST 5] Testing Session operations...")

    try:
        dynamodb = get_dynamodb_reasources()
        session_repo = SessionRepository(dynamodb)

        # Create test session
        print("  Creating test session...")
        test_session = Session.create_new(
            puuid="test_puuid_12345",
            riot_id="TestPlayer#NA1",
            expiry_days=7
        )
        session_repo.create_session(test_session)
        print(f"  Session created: {test_session.session_token}")

        # Validate session
        print("  Validating session...")
        is_valid = session_repo.is_valid_session(test_session.session_token)
        if is_valid:
            print("  Session is valid")
        else:
            print("  Session validation failed")
            return False

        # Get PUUID from session
        print("  Getting PUUID from session...")
        puuid = session_repo.get_puuid_from_session(test_session.session_token)
        if puuid == "test_puuid_12345":
            print("  Retrieved PUUID from session")
        else:
            print("  Failed to get PUUID from session")
            return False

        # Clean up
        print("  Cleaning up...")
        session_repo.delete_session(test_session.session_token)
        print("  Session deleted")

        return True

    except Exception as e:
        print(f"  Session operations failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("=" * 60)
    print("RIFT REWIND - DATABASE TEST SUITE")
    print("=" * 60)

    results = []

    # Run all tests
    results.append(("Connection", test_connection()))
    results.append(("Player Operations", test_player_operations()))
    results.append(("Match Operations", test_match_operations()))
    results.append(("Conversation Operations", test_conversation_operations()))
    results.append(("Session Operations", test_session_operations()))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{status} - {test_name}")

    print("\n" + "=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)

    if passed == total:
        print("\nAll tests passed! Database is ready to use.")
        return 0
    else:
        print("\nSome tests failed. Check errors above.")
        return 1


if __name__ == "__main__":
    exit(main())
