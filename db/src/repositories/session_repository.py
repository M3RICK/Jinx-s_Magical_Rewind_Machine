from typing import Optional
from .base_repository import BaseRepository
from ..models.session import Session


class SessionRepository(BaseRepository):
    """Repository for Sessions table operations"""

    def __init__(self, dynamodb_resource):
        super().__init__(dynamodb_resource, 'Sessions')

    def get_session(self, session_token: str) -> Optional[Session]:
        """
        Get a session by token.

        Args:
            session_token: Session token UUID

        Returns:
            Session object or None if not found
        """
        item = self.get_item({'session_token': session_token})
        return Session.from_dynamodb_item(item) if item else None

    def create_session(self, session: Session) -> Session:
        """
        Create a new session.

        Args:
            session: Session object to create

        Returns:
            Created Session object
        """
        self.put_item(session.to_dynamodb_item())
        return session

    def delete_session(self, session_token: str) -> bool:
        """
        Delete a session.

        Args:
            session_token: Session token to delete

        Returns:
            True if successful
        """
        return self.delete_item({'session_token': session_token})

    def is_valid_session(self, session_token: str) -> bool:
        """
        Check if a session token is valid (exists and not expired).

        Args:
            session_token: Session token to validate

        Returns:
            True if valid, False otherwise
        """
        session = self.get_session(session_token)
        if not session:
            return False

        return not session.is_expired()

    def get_puuid_from_session(self, session_token: str) -> Optional[str]:
        """
        Get PUUID associated with a session token.

        Args:
            session_token: Session token

        Returns:
            PUUID or None if session not found or expired
        """
        session = self.get_session(session_token)
        if not session or session.is_expired():
            return None

        return session.puuid

    def extend_session(self, session_token: str, days: int = 7) -> Optional[Session]:
        """
        Extend session expiry.

        Args:
            session_token: Session token to extend
            days: Number of days to extend by (default: 7)

        Returns:
            Updated Session object or None if not found
        """
        session = self.get_session(session_token)
        if not session:
            return None

        session.extend_expiry(days)
        self.put_item(session.to_dynamodb_item())
        return session

    def cleanup_expired_sessions(self) -> int:
        """
        Remove all expired sessions from the database.

        Returns:
            Number of sessions deleted
        """
        # Scan for all sessions (use carefully - this is a full table scan)
        all_sessions = self.scan()

        expired_count = 0
        with self.table.batch_writer() as batch:
            for item in all_sessions:
                session = Session.from_dynamodb_item(item)
                if session.is_expired():
                    batch.delete_item(Key={'session_token': session.session_token})
                    expired_count += 1

        return expired_count
