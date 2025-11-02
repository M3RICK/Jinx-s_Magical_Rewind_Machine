from datetime import datetime
from typing import Dict, Optional, Any
from dataclasses import dataclass
import time


@dataclass
class MatchHistory:
    """
    Represents a single match in a player's match history.

    Stores match data with PUUID as partition key and match_id as sort key.
    Includes a timestamp for easy chronological sorting.
    """
    puuid: str
    match_id: str  # Riot match ID format: "NA1_4567890123"
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
            'match_data': self.match_data,
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
