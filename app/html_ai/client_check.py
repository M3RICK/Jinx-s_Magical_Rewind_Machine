import sys
import os
import asyncio
from typing import Optional, Tuple

# Add parent directories to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv
from API.Core import Core
from API.league.rank import Rank
from db.src.services.player_service import PlayerService
from db.src.models.player import Player, RankInfo
from db.src.models.session import Session
from db.src.models.match_history import MatchHistory

# Load environment variables
load_dotenv()


async def fetch_and_populate_data(puuid: str, region: str, platform: str, player_service: PlayerService, match_count: int = 20) -> bool:
    """
    Fetch matches and rank from Riot API and update in database.

    Args:
        puuid: Player's PUUID
        region: API region (americas, europe, asia, sea)
        platform: Platform region (na1, euw1, etc.)
        player_service: PlayerService instance
        match_count: Number of matches to fetch

    Returns:
        True if successful
    """
    try:
        async with Core() as core:
            from API.league.match import Match

            match_api = Match(core)
            rank_api = Rank(core)

            # Fetch matches
            print("[SYNCING] Match history...")
            match_ids = await match_api.get_match_history(puuid=puuid, region=region, count=match_count)

            if match_ids:
                print(f"[SUCCESS] Found {len(match_ids)} matches")

                new_matches = 0
                for i, match_id in enumerate(match_ids):
                    # Check if match already exists
                    if player_service.match_repo.match_exists(puuid, match_id):
                        continue

                    # Fetch match details
                    match_data = await match_api.get_match_details(match_id, region)
                    if not match_data:
                        continue

                    # Create and save MatchHistory
                    match_history = MatchHistory.from_riot_match(puuid, match_id, match_data)
                    player_service.match_repo.save_match(match_history)
                    new_matches += 1

                    if (i + 1) % 5 == 0:
                        print(f"  Progress: {i + 1}/{len(match_ids)}")

                print(f"[SUCCESS] Saved {new_matches} new matches")
            else:
                print("[WARNING] No match history found")

            # Fetch rank
            print("[FETCHING] Rank information...")
            rank_data = await rank_api.get_rank_info(
                identifier=puuid,
                platform=platform,
                by_puuid=True
            )

            if rank_data and len(rank_data) > 0:
                solo_queue = next((r for r in rank_data if r.get('queueType') == 'RANKED_SOLO_5x5'), None)
                if solo_queue:
                    current_rank = RankInfo(
                        tier=solo_queue.get('tier', 'UNRANKED'),
                        division=solo_queue.get('rank', ''),
                        lp=solo_queue.get('leaguePoints', 0)
                    )
                    print(f"[SUCCESS] Rank: {current_rank.tier} {current_rank.division} ({current_rank.lp} LP)")

                    # Update player stats in DB
                    player_service.update_player_stats(puuid, {
                        'current_rank': {
                            'tier': current_rank.tier,
                            'division': current_rank.division,
                            'lp': current_rank.lp
                        }
                    })
                else:
                    print("[INFO] Player is unranked")
            else:
                print("[INFO] No rank data available")

            return True

    except Exception as e:
        print(f"[ERROR] Failed to fetch data: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_and_build_client(puuid: str, riot_id: str, region: str, platform: str) -> Tuple[bool, Optional[Player], Optional[str]]:
    """
    Check if client exists in database, if not build their profile.

    If player exists: Update their stats (main role, top 5 champs, winrate, rank, match history)
    If player NOT exists: Create new player entry and populate all their data

    Args:
        puuid: Player's unique identifier
        riot_id: Player's Riot ID (name#tag)
        region: API region (americas, europe, asia, sea)
        platform: Platform region (na1, euw1, etc.)

    Returns:
        Tuple of (success, player_object, session_token)
    """
    player_service = PlayerService()
    player = player_service.player_repo.get_by_puuid(puuid)

    # If player doesn't exist, create them first
    if not player:
        print(f"\n[DATABASE] New player detected - creating profile...")
        new_player = Player(puuid=puuid, riot_id=riot_id, region=platform)
        player_service.player_repo.create(new_player)
        print(f"[SUCCESS] Created player profile")
    else:
        print(f"\n[DATABASE] Player {riot_id} found - updating profile...")

    # Now proceed with updating/populating data for everyone
    print("=" * 60)

    # Fetch matches and rank from API
    asyncio.run(fetch_and_populate_data(puuid, region, platform, player_service, match_count=20))

    # Calculate and update stats from matches
    # TODO: Re-enable when calculate_player_stats_from_matches is implemented
    # print("[CALCULATING] Player statistics from matches...")
    # stats = player_service.calculate_player_stats_from_matches(puuid)
    # if stats:
    #     player_service.update_player_stats(puuid, stats)
    #     print(f"[SUCCESS] Winrate: {stats['winrate']}%, Main role: {stats['main_role']}")
    # else:
    #     print("[INFO] No match data to calculate stats")
    print("[INFO] Skipping stats calculation (not yet implemented)")

    print("=" * 60)
    print("[COMPLETE] Profile ready!")

    # Create session token
    print("[SESSION] Creating session token...")
    session = Session.create_new(
        puuid=puuid,
        riot_id=riot_id,
        expiry_days=7
    )
    player_service.session_repo.create_session(session)
    print(f"[SUCCESS] Session created")

    # Reload player to get fresh data
    player = player_service.player_repo.get_by_puuid(puuid)
    return True, player, session.session_token
