from typing import Optional, Tuple
import sys
import os

# Add parent directories to path to import API modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from db.src.repositories.player_repository import PlayerRepository
from db.src.repositories.match_repository import MatchRepository
from db.src.repositories.session_repository import SessionRepository
from db.src.models.player import Player, RankInfo
from db.src.models.session import Session
from db.src.db_handshake import get_dynamodb_reasources


class PlayerService:
    """
    Service layer that integrates Riot API with database operations.

    This service handles the workflow:
    1. Check if name#tag exists in Riot API
    2. Check if player exists in database
    3. Get PUUID from database or fetch from Riot
    4. Store/update player data
    """

    def __init__(self):
        """Initialize repositories"""
        dynamodb = get_dynamodb_reasources()
        self.player_repo = PlayerRepository(dynamodb)
        self.match_repo = MatchRepository(dynamodb)
        self.session_repo = SessionRepository(dynamodb)

    def get_or_create_player(self, riot_id: str, region: str) -> Tuple[Optional[Player], str]:
        """
        Get existing player or create new one from Riot API.

        Workflow:
        1. Check if riot_id exists in our database
        2. If yes, return existing player
        3. If no, fetch from Riot API and create new player

        Args:
            riot_id: Riot ID in "name#tag" format
            region: Player's region (e.g., "na1", "euw1")

        Returns:
            Tuple of (Player object or None, status message)
        """
        # First, check if player exists in database
        existing_player = self.player_repo.get_by_riot_id(riot_id)
        if existing_player:
            print(f"Player {riot_id} found in database with PUUID: {existing_player.puuid}")
            return existing_player, "Player found in database"

        # Player not in database, need to fetch from Riot API
        print(f"Player {riot_id} not found in database. Fetching from Riot API...")

        try:
            # Import here to avoid circular dependencies
            from API.riot.account import get_puuid_by_riot_id

            # Fetch PUUID from Riot API
            puuid = get_puuid_by_riot_id(riot_id, region)

            if not puuid:
                return None, f"Player {riot_id} not found in Riot API"

            # Create new player in database
            new_player = Player(
                puuid=puuid,
                riot_id=riot_id,
                region=region
            )

            self.player_repo.create(new_player)
            print(f"Created new player {riot_id} with PUUID: {puuid}")

            return new_player, "Player created successfully"

        except Exception as e:
            print(f"Error fetching player from Riot API: {e}")
            return None, f"Error: {str(e)}"

    def authenticate_player(self, riot_id: str, region: str) -> Tuple[Optional[str], Optional[Player]]:
        """
        Authenticate a player and create a session.

        Args:
            riot_id: Riot ID in "name#tag" format
            region: Player's region

        Returns:
            Tuple of (session_token or None, Player object or None)
        """
        # Get or create player
        player, status = self.get_or_create_player(riot_id, region)

        if not player:
            print(f"Authentication failed: {status}")
            return None, None

        # Create session
        session = Session.create_new(
            puuid=player.puuid,
            riot_id=player.riot_id,
            expiry_days=7
        )

        self.session_repo.create_session(session)
        print(f"Created session for {riot_id}: {session.session_token}")

        return session.session_token, player

    def get_player_by_session(self, session_token: str) -> Optional[Player]:
        """
        Get player from session token.

        Args:
            session_token: Session token

        Returns:
            Player object or None if session invalid
        """
        puuid = self.session_repo.get_puuid_from_session(session_token)
        if not puuid:
            return None

        return self.player_repo.get_by_puuid(puuid)

    def update_player_stats(self, puuid: str, stats: dict) -> Optional[Player]:
        """
        Update player statistics from match analysis.

        Args:
            puuid: Player's unique identifier
            stats: Dictionary containing winrate, main_role, main_champions, current_rank

        Returns:
            Updated Player object or None if not found
        """
        player = self.player_repo.get_by_puuid(puuid)
        if not player:
            return None

        # Update player fields
        if 'winrate' in stats:
            player.winrate = stats['winrate']

        if 'main_role' in stats:
            player.main_role = stats['main_role']

        if 'main_champions' in stats:
            player.main_champions = stats['main_champions']

        if 'current_rank' in stats:
            rank_data = stats['current_rank']
            player.current_rank = RankInfo(
                tier=rank_data.get('tier', ''),
                division=rank_data.get('division', ''),
                lp=rank_data.get('lp', 0)
            )

        return self.player_repo.update(player)

    def sync_player_matches(self, puuid: str, match_count: int = 20) -> Tuple[int, str]:
        """
        Sync player's match history from Riot API to database.

        Args:
            puuid: Player's unique identifier
            match_count: Number of recent matches to sync (default: 20)

        Returns:
            Tuple of (number of new matches synced, status message)
        """
        try:
            # Import here to avoid circular dependencies
            from API.league.match import get_match_history, get_match_details
            from db.src.models.match_history import MatchHistory

            player = self.player_repo.get_by_puuid(puuid)
            if not player:
                return 0, "Player not found"

            # Get match IDs from Riot API
            match_ids = get_match_history(puuid, player.region, count=match_count)

            if not match_ids:
                return 0, "No matches found"

            new_matches = 0
            for match_id in match_ids:
                # Check if match already exists
                if self.match_repo.match_exists(puuid, match_id):
                    continue

                # Fetch match details
                match_data = get_match_details(match_id, player.region)
                if not match_data:
                    continue

                # Create MatchHistory object
                match_history = MatchHistory.from_riot_match(puuid, match_id, match_data)

                # Save to database
                self.match_repo.save_match(match_history)
                new_matches += 1

            # Clean up old matches if we have more than match_count
            self.match_repo.delete_old_matches(puuid, keep_count=match_count)

            return new_matches, f"Synced {new_matches} new matches"

        except Exception as e:
            print(f"Error syncing matches: {e}")
            return 0, f"Error: {str(e)}"

    def get_player_overview(self, puuid: str) -> Optional[dict]:
        """
        Get complete player overview (profile + recent matches).

        Args:
            puuid: Player's unique identifier

        Returns:
            Dictionary with player info and recent matches
        """
        player = self.player_repo.get_by_puuid(puuid)
        if not player:
            return None

        recent_matches = self.match_repo.get_recent_matches(puuid, count=20)

        return {
            'player': player.to_dynamodb_item(),
            'match_count': len(recent_matches),
            'recent_matches': [match.to_dynamodb_item() for match in recent_matches]
        }
