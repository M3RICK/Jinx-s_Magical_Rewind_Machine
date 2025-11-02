from typing import Optional
from boto3.dynamodb.conditions import Key
from .base_repository import BaseRepository
from ..models.player import Player


class PlayerRepository(BaseRepository):
    """Repository for Player table operations"""

    def __init__(self, dynamodb_resource):
        super().__init__(dynamodb_resource, 'Players')

    def get_by_puuid(self, puuid: str) -> Optional[Player]:
        """
        Get player by PUUID.

        Args:
            puuid: Player's unique Riot identifier

        Returns:
            Player object or None if not found
        """
        item = self.get_item({'puuid': puuid})
        return Player.from_dynamodb_item(item) if item else None

    def get_by_riot_id(self, riot_id: str) -> Optional[Player]:
        """
        Get player by Riot ID (name#tag) using GSI.

        Args:
            riot_id: Player's Riot ID in "name#tag" format

        Returns:
            Player object or None if not found
        """
        try:
            response = self.table.query(
                IndexName='RiotIdIndex',
                KeyConditionExpression=Key('riot_id').eq(riot_id)
            )

            items = response.get('Items', [])
            if items:
                return Player.from_dynamodb_item(items[0])
            return None
        except Exception as e:
            print(f"Error querying by riot_id: {e}")
            raise

    def create(self, player: Player) -> Player:
        """
        Create a new player.

        Args:
            player: Player object to create

        Returns:
            Created Player object
        """
        self.put_item(player.to_dynamodb_item())
        return player

    def update(self, player: Player) -> Player:
        """
        Update an existing player.

        Args:
            player: Player object with updated data

        Returns:
            Updated Player object
        """
        player.update_timestamp()
        self.put_item(player.to_dynamodb_item())
        return player

    def delete(self, puuid: str) -> bool:
        """
        Delete a player by PUUID.

        Args:
            puuid: Player's unique identifier

        Returns:
            True if successful
        """
        return self.delete_item({'puuid': puuid})

    def exists(self, puuid: str) -> bool:
        """
        Check if player exists by PUUID.

        Args:
            puuid: Player's unique identifier

        Returns:
            True if player exists, False otherwise
        """
        return self.get_by_puuid(puuid) is not None

    def exists_by_riot_id(self, riot_id: str) -> bool:
        """
        Check if player exists by Riot ID.

        Args:
            riot_id: Player's Riot ID in "name#tag" format

        Returns:
            True if player exists, False otherwise
        """
        return self.get_by_riot_id(riot_id) is not None

    def update_stats(self, puuid: str, winrate: float, main_role: str,
                    main_champions: list, current_rank: dict) -> Optional[Player]:
        """
        Update player statistics.

        Args:
            puuid: Player's unique identifier
            winrate: Updated winrate percentage
            main_role: Main role played
            main_champions: List of main champions
            current_rank: Current rank information

        Returns:
            Updated Player object or None if not found
        """
        player = self.get_by_puuid(puuid)
        if not player:
            return None

        player.winrate = winrate
        player.main_role = main_role
        player.main_champions = main_champions
        player.current_rank = current_rank
        player.update_timestamp()

        self.put_item(player.to_dynamodb_item())
        return player
