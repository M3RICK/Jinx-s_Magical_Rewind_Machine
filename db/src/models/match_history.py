from datetime import datetime
from typing import Dict, Optional, Any
from dataclasses import dataclass
from decimal import Decimal
import time


def convert_floats_to_decimal(obj):
    """
    Recursively convert all float values to Decimal for DynamoDB compatibility.

    DynamoDB doesn't support Python float types - only Decimal.
    This function walks through nested dicts and lists to convert all floats.
    """
    if isinstance(obj, list):
        return [convert_floats_to_decimal(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: convert_floats_to_decimal(value) for key, value in obj.items()}
    elif isinstance(obj, float):
        return Decimal(str(obj))
    else:
        return obj


@dataclass
class MatchHistory:
    """
    Represents a single match in a player's match history.

    Stores match data with PUUID as partition key and match_id as sort key.
    Includes a timestamp for easy chronological sorting.
    """
    puuid: str
    match_id: str
    timestamp: int  # Unix timestamp (seconds since epoch)
    match_data: Dict[str, Any]  # Complete match data from Riot API
    created_at: Optional[str] = None

    def __post_init__(self):
        """Initialize created_at if not provided"""
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat()

    def to_dynamodb_item(self) -> Dict:
        """Convert to DynamoDB item format"""
        return {
            'puuid': self.puuid,
            'match_id': self.match_id,
            'timestamp': self.timestamp,
            'match_data': convert_floats_to_decimal(self.match_data),
            'created_at': self.created_at
        }

    @staticmethod
    def from_dynamodb_item(item: Dict) -> 'MatchHistory':
        """Create MatchHistory instance from DynamoDB item"""
        return MatchHistory(
            puuid=item['puuid'],
            match_id=item['match_id'],
            timestamp=int(item['timestamp']),
            match_data=item['match_data'],
            created_at=item.get('created_at')
        )

    @staticmethod
    def from_riot_match(puuid: str, match_id: str, match_data: Dict) -> 'MatchHistory':
        """
        Create MatchHistory from Riot API match data.

        Args:
            puuid: Player's PUUID
            match_id: Match ID from Riot API
            match_data: Complete match data from Riot Match API
        """
        # Extract timestamp from match data (game creation time)
        game_creation = match_data.get('info', {}).get('gameCreation', time.time() * 1000)
        timestamp = int(game_creation / 1000)  # Convert milliseconds to seconds

        return MatchHistory(
            puuid=puuid,
            match_id=match_id,
            timestamp=timestamp,
            match_data=match_data
        )
