from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from decimal import Decimal


@dataclass
class RankInfo:
    """Represents player's current rank information"""
    tier: str  # e.g., "GOLD", "PLATINUM", "DIAMOND"
    division: str  # e.g., "I", "II", "III", "IV"
    lp: int  # League Points

    def to_dict(self) -> Dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict) -> 'RankInfo':
        return RankInfo(**data)


@dataclass
class Player:
    """
    Represents a League of Legends player profile.

    This is the main player table that stores:
    - PUUID (unique Riot identifier)
    - riot_id (name#tag format)
    - region
    - main_role
    - main_champions (top 5)
    - winrate
    - current_rank
    """
    puuid: str
    riot_id: str  # Format: "SummonerName#TAG"
    region: str  # e.g., "na1", "euw1", "kr"
    main_role: Optional[str] = None  # "TOP", "JUNGLE", "MID", "ADC", "SUPPORT"
    main_champions: Optional[List[str]] = None  # Top 5 champion names or IDs
    winrate: Optional[float] = None  # Overall winrate as percentage (0-100)
    current_rank: Optional[RankInfo] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def __post_init__(self):
        """Initialize timestamps if not provided"""
        now = datetime.utcnow().isoformat()
        if self.created_at is None:
            self.created_at = now
        if self.updated_at is None:
            self.updated_at = now
        if self.main_champions is None:
            self.main_champions = []

    def to_dynamodb_item(self) -> Dict:
        """Convert to DynamoDB item format"""
        item = {
            'puuid': self.puuid,
            'riot_id': self.riot_id,
            'region': self.region,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

        # Add optional fields only if they have values
        if self.main_role:
            item['main_role'] = self.main_role

        if self.main_champions:
            item['main_champions'] = self.main_champions

        if self.winrate is not None:
            item['winrate'] = Decimal(str(self.winrate))

        if self.current_rank:
            item['current_rank'] = self.current_rank.to_dict()

        return item

    @staticmethod
    def from_dynamodb_item(item: Dict) -> 'Player':
        """Create Player instance from DynamoDB item"""
        rank_data = item.get('current_rank')
        rank_info = RankInfo.from_dict(rank_data) if rank_data else None

        return Player(
            puuid=item['puuid'],
            riot_id=item['riot_id'],
            region=item['region'],
            main_role=item.get('main_role'),
            main_champions=item.get('main_champions', []),
            winrate=float(item['winrate']) if item.get('winrate') else None,
            current_rank=rank_info,
            created_at=item.get('created_at'),
            updated_at=item.get('updated_at')
        )

    def update_timestamp(self):
        """Update the updated_at timestamp"""
        self.updated_at = datetime.utcnow().isoformat()
