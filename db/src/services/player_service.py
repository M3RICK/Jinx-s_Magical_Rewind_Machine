from typing import Optional, Tuple
import sys
import os
import asyncio

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

    def calculate_player_stats_from_matches(self, puuid: str) -> Optional[dict]:
        """
        Calculate player statistics from their match history.

        Analyzes matches to calculate:
        - Winrate (percentage)
        - Main role (most played)
        - Top 5 champions (most played)

        Args:
            puuid: Player's unique identifier

        Returns:
            Dictionary with calculated stats or None if no matches
        """
        matches = self.match_repo.get_recent_matches(puuid, count=20)

        if not matches:
            return None

        # Track stats
        wins = 0
        total_games = 0
        role_counts = {}  # {role: count}
        champion_counts = {}  # {champion_id: count}

        for match in matches:
            match_data = match.match_data
            participants = match_data.get('info', {}).get('participants', [])

            # Find this player's data in the match
            player_data = next((p for p in participants if p.get('puuid') == puuid), None)

            if not player_data:
                continue

            total_games += 1

            # Count wins
            if player_data.get('win', False):
                wins += 1

            # Count role
            role = player_data.get('teamPosition', 'UNKNOWN')
            if role and role != 'UNKNOWN':
                role_counts[role] = role_counts.get(role, 0) + 1

            # Count champion
            champion_id = player_data.get('championId')
            if champion_id:
                champion_counts[champion_id] = champion_counts.get(champion_id, 0) + 1

        # Calculate winrate
        winrate = (wins / total_games * 100) if total_games > 0 else 0

        # Get main role (most played)
        main_role = max(role_counts.items(), key=lambda x: x[1])[0] if role_counts else None

        # Get top 5 champions (most played)
        sorted_champions = sorted(champion_counts.items(), key=lambda x: x[1], reverse=True)
        main_champions = [str(champ_id) for champ_id, _ in sorted_champions[:5]]

        return {
            'winrate': round(winrate, 2),
            'main_role': main_role,
            'main_champions': main_champions
        }
