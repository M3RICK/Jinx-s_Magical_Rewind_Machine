from typing import List, Optional
from boto3.dynamodb.conditions import Key
from .base_repository import BaseRepository
from ..models.conversation import Conversation


class ConversationRepository(BaseRepository):
    """Repository for Conversations table operations"""

    def __init__(self, dynamodb_resource):
        super().__init__(dynamodb_resource, 'Conversations')

    def get_conversation(self, puuid: str, conversation_id: str) -> Optional[Conversation]:
        """
        Get a specific conversation by PUUID and conversation ID.

        Args:
            puuid: Player's unique identifier
            conversation_id: Conversation ID

        Returns:
            Conversation object or None if not found
        """
        item = self.get_item({'puuid': puuid, 'conversation_id': conversation_id})
        return Conversation.from_dynamodb_item(item) if item else None

    def get_player_conversations(self, puuid: str, limit: Optional[int] = None) -> List[Conversation]:
        """
        Get all conversations for a player (sorted by conversation_id, newest first).

        Args:
            puuid: Player's unique identifier
            limit: Maximum number of conversations to return

        Returns:
            List of Conversation objects
        """
        params = {
            'KeyConditionExpression': Key('puuid').eq(puuid),
            'ScanIndexForward': False  # Sort descending (newest first)
        }

        if limit:
            params['Limit'] = limit

        items = self.query(**params)
        return [Conversation.from_dynamodb_item(item) for item in items]

    def get_recent_conversations(self, puuid: str, count: int = 10) -> List[Conversation]:
        """
        Get the N most recent conversations for a player.

        Args:
            puuid: Player's unique identifier
            count: Number of recent conversations to retrieve (default: 10)

        Returns:
            List of Conversation objects
        """
        return self.get_player_conversations(puuid, limit=count)

    def create_conversation(self, conversation: Conversation) -> Conversation:
        """
        Create a new conversation.

        Args:
            conversation: Conversation object to create

        Returns:
            Created Conversation object
        """
        self.put_item(conversation.to_dynamodb_item())
        return conversation

    def update_conversation(self, conversation: Conversation) -> Conversation:
        """
        Update an existing conversation.

        Args:
            conversation: Conversation object with updated data

        Returns:
            Updated Conversation object
        """
        conversation.update_timestamp()
        self.put_item(conversation.to_dynamodb_item())
        return conversation

    def add_message(self, puuid: str, conversation_id: str,
                   role: str, content: str) -> Optional[Conversation]:
        """
        Add a message to an existing conversation.

        Args:
            puuid: Player's unique identifier
            conversation_id: Conversation ID
            role: Message role ("user" or "assistant")
            content: Message content

        Returns:
            Updated Conversation object or None if not found
        """
        conversation = self.get_conversation(puuid, conversation_id)
        if not conversation:
            return None

        conversation.add_message(role, content)
        return self.update_conversation(conversation)

    def delete_conversation(self, puuid: str, conversation_id: str) -> bool:
        """
        Delete a specific conversation.

        Args:
            puuid: Player's unique identifier
            conversation_id: Conversation ID to delete

        Returns:
            True if successful
        """
        return self.delete_item({'puuid': puuid, 'conversation_id': conversation_id})

    def get_conversations_by_session(self, puuid: str, session_id: str) -> List[Conversation]:
        """
        Get all conversations for a specific session.

        Args:
            puuid: Player's unique identifier
            session_id: Session ID to filter by

        Returns:
            List of Conversation objects
        """
        items = self.query(
            KeyConditionExpression=Key('puuid').eq(puuid),
            FilterExpression='session_id = :sid',
            ExpressionAttributeValues={':sid': session_id}
        )
        return [Conversation.from_dynamodb_item(item) for item in items]

    def conversation_exists(self, puuid: str, conversation_id: str) -> bool:
        """
        Check if a conversation exists.

        Args:
            puuid: Player's unique identifier
            conversation_id: Conversation ID to check

        Returns:
            True if conversation exists, False otherwise
        """
        return self.get_conversation(puuid, conversation_id) is not None
