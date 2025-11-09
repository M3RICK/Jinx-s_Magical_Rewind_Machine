from typing import List, Optional
from boto3.dynamodb.conditions import Key
from .base_repository import BaseRepository
from ..models.match_history import MatchHistory


class MatchRepository(BaseRepository):
    """Repository for MatchHistory table operations"""

    def __init__(self, dynamodb_resource):
        super().__init__(dynamodb_resource, 'MatchHistory')

    def get_match(self, puuid: str, match_id: str) -> Optional[MatchHistory]:
        """
        Get a specific match by PUUID and match ID.

        Args:
            puuid: Player's unique identifier
            match_id: Match ID

        Returns:
            MatchHistory object or None if not found
        """
        item = self.get_item({'puuid': puuid, 'match_id': match_id})
        return MatchHistory.from_dynamodb_item(item) if item else None

    def get_player_matches(self, puuid: str, limit: Optional[int] = None) -> List[MatchHistory]:
        """
        Get all matches for a player, sorted by timestamp (most recent first).

        Args:
            puuid: Player's unique identifier
            limit: Maximum number of matches to return (default: all)

        Returns:
            List of MatchHistory objects
        """
        key_condition = Key('puuid').eq(puuid)

        query_params = {
            'IndexName': 'TimestampIndex',
            'ScanIndexForward': False  # Sort descending (newest first)
        }

        if limit:
            query_params['Limit'] = limit

        items = self.query(key_condition, **query_params)
        return [MatchHistory.from_dynamodb_item(item) for item in items]

    def get_recent_matches(self, puuid: str, count: int = 20) -> List[MatchHistory]:
        """
        Get the N most recent matches for a player.

        Args:
            puuid: Player's unique identifier
            count: Number of recent matches to retrieve (default: 20)

        Returns:
            List of MatchHistory objects sorted by timestamp (newest first)
        """
        return self.get_player_matches(puuid, limit=count)

    def save_match(self, match: MatchHistory) -> MatchHistory:
        """
        Save a match to the database.

        Args:
            match: MatchHistory object to save

        Returns:
            Saved MatchHistory object
        """
        self.put_item(match.to_dynamodb_item())
        return match

    def save_matches(self, matches: List[MatchHistory]) -> int:
        """
        Save multiple matches (batch operation).

        Args:
            matches: List of MatchHistory objects to save

        Returns:
            Number of matches saved
        """
        # Use batch write for efficiency
        with self.table.batch_writer() as batch:
            for match in matches:
                batch.put_item(Item=match.to_dynamodb_item())

        return len(matches)

    def delete_match(self, puuid: str, match_id: str) -> bool:
        """
        Delete a specific match.

        Args:
            puuid: Player's unique identifier
            match_id: Match ID to delete

        Returns:
            True if successful
        """
        return self.delete_item({'puuid': puuid, 'match_id': match_id})

    def match_exists(self, puuid: str, match_id: str) -> bool:
        """
        Check if a match already exists in the database.

        Args:
            puuid: Player's unique identifier
            match_id: Match ID to check

        Returns:
            True if match exists, False otherwise
        """
        return self.get_match(puuid, match_id) is not None

    def get_match_count(self, puuid: str) -> int:
        """
        Get the total number of matches stored for a player.

        Args:
            puuid: Player's unique identifier

        Returns:
            Number of matches
        """
        response = self.table.query(
            KeyConditionExpression=Key('puuid').eq(puuid),
            Select='COUNT'
        )
        return response.get('Count', 0)

    def delete_old_matches(self, puuid: str, keep_count: int = 20) -> int:
        """
        Delete old matches, keeping only the N most recent ones.

        Args:
            puuid: Player's unique identifier
            keep_count: Number of recent matches to keep (default: 20)

        Returns:
            Number of matches deleted
        """
        all_matches = self.get_player_matches(puuid)

        if len(all_matches) <= keep_count:
            return 0

        # Delete matches beyond the keep_count
        matches_to_delete = all_matches[keep_count:]

        with self.table.batch_writer() as batch:
            for match in matches_to_delete:
                batch.delete_item(
                    Key={'puuid': match.puuid, 'match_id': match.match_id}
                )

        return len(matches_to_delete)
