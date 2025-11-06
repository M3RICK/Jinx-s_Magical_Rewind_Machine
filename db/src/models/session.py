from datetime import datetime, timedelta
from typing import Dict, Optional
from dataclasses import dataclass
import uuid


@dataclass
class Session:
    """
    Represents a user session for authentication.

    Maps session tokens to player PUUIDs for persistent access.
    """
    session_token: str  # UUID format
    puuid: str
    riot_id: str  # For quick reference without lookup
    created_at: Optional[str] = None
    expires_at: Optional[str] = None

    def __post_init__(self):
        """Initialize timestamps if not provided"""
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat()

        # Default session expiry: 7 days from creation
        if self.expires_at is None:
            expiry = datetime.utcnow() + timedelta(days=7)
            self.expires_at = expiry.isoformat()

    def is_expired(self) -> bool:
        """Check if session has expired"""
        expiry = datetime.fromisoformat(self.expires_at)
        return datetime.utcnow() > expiry

    def extend_expiry(self, days: int = 7):
        """Extend session expiry by specified number of days"""
        expiry = datetime.utcnow() + timedelta(days=days)
        self.expires_at = expiry.isoformat()

    def to_dynamodb_item(self) -> Dict:
        """Convert to DynamoDB item format"""
        return {
            'session_token': self.session_token,
            'puuid': self.puuid,
            'riot_id': self.riot_id,
            'created_at': self.created_at,
            'expires_at': self.expires_at
        }

    @staticmethod
    def from_dynamodb_item(item: Dict) -> 'Session':
        """Create Session instance from DynamoDB item"""
        return Session(
            session_token=item['session_token'],
            puuid=item['puuid'],
            riot_id=item['riot_id'],
            created_at=item.get('created_at'),
            expires_at=item.get('expires_at')
        )

    @staticmethod
    def create_new(puuid: str, riot_id: str, expiry_days: int = 7) -> 'Session':
        """Create a new session with generated token"""
        session_token = str(uuid.uuid4())
        expiry = datetime.utcnow() + timedelta(days=expiry_days)

        return Session(
            session_token=session_token,
            puuid=puuid,
            riot_id=riot_id,
            expires_at=expiry.isoformat()
        )
