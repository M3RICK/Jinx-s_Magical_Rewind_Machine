from typing import Optional, List, Dict
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from db.src.repositories.conversation_repository import ConversationRepository
from db.src.models.conversation import Conversation
from db.src.db_handshake import get_dynamodb_reasources


class ConversationService:
    """
    Service layer for managing AI conversations.

    Handles conversation history storage and retrieval.
    """

    def __init__(self):
        """Initialize repository"""
        dynamodb = get_dynamodb_reasources()
        self.conversation_repo = ConversationRepository(dynamodb)

    def start_new_conversation(self, puuid: str, session_id: Optional[str] = None) -> Conversation:
        """
        Start a new conversation for a player.

        Args:
            puuid: Player's unique identifier
            session_id: Optional session ID to group related conversations

        Returns:
            New Conversation object
        """
        conversation = Conversation.create_new(puuid, session_id)
        return self.conversation_repo.create_conversation(conversation)

    def add_user_message(self, puuid: str, conversation_id: str, message: str) -> Optional[Conversation]:
        """
        Add a user message to a conversation.

        Args:
            puuid: Player's unique identifier
            conversation_id: Conversation ID
            message: User's message content

        Returns:
            Updated Conversation object or None if not found
        """
        return self.conversation_repo.add_message(puuid, conversation_id, "user", message)

    def add_assistant_message(self, puuid: str, conversation_id: str, message: str) -> Optional[Conversation]:
        """
        Add an assistant message to a conversation.

        Args:
            puuid: Player's unique identifier
            conversation_id: Conversation ID
            message: Assistant's response content

        Returns:
            Updated Conversation object or None if not found
        """
        return self.conversation_repo.add_message(puuid, conversation_id, "assistant", message)

    def get_conversation(self, puuid: str, conversation_id: str) -> Optional[Conversation]:
        """
        Get a specific conversation.

        Args:
            puuid: Player's unique identifier
            conversation_id: Conversation ID

        Returns:
            Conversation object or None if not found
        """
        return self.conversation_repo.get_conversation(puuid, conversation_id)

    def get_conversation_history(self, puuid: str, limit: int = 10) -> List[Conversation]:
        """
        Get recent conversation history for a player.

        Args:
            puuid: Player's unique identifier
            limit: Maximum number of conversations to return

        Returns:
            List of Conversation objects
        """
        return self.conversation_repo.get_recent_conversations(puuid, count=limit)

    def get_messages_for_ai(self, puuid: str, conversation_id: str) -> Optional[List[Dict]]:
        """
        Get conversation messages formatted for AI input.

        Args:
            puuid: Player's unique identifier
            conversation_id: Conversation ID

        Returns:
            List of message dictionaries or None if conversation not found
        """
        conversation = self.get_conversation(puuid, conversation_id)
        if not conversation:
            return None

        return [
            {
                'role': msg.role,
                'content': msg.content
            }
            for msg in conversation.messages
        ]

    def continue_conversation(self, puuid: str, conversation_id: str,
                            user_message: str) -> Optional[Conversation]:
        """
        Add a user message to an existing conversation.

        This is a convenience method that combines getting the conversation
        and adding a message.

        Args:
            puuid: Player's unique identifier
            conversation_id: Conversation ID
            user_message: User's message

        Returns:
            Updated Conversation object or None if not found
        """
        return self.add_user_message(puuid, conversation_id, user_message)

    def delete_conversation(self, puuid: str, conversation_id: str) -> bool:
        """
        Delete a conversation.

        Args:
            puuid: Player's unique identifier
            conversation_id: Conversation ID

        Returns:
            True if successful
        """
        return self.conversation_repo.delete_conversation(puuid, conversation_id)

    def get_latest_conversation(self, puuid: str) -> Optional[Conversation]:
        """
        Get the most recent conversation for a player.

        Args:
            puuid: Player's unique identifier

        Returns:
            Latest Conversation object or None if no conversations exist
        """
        conversations = self.conversation_repo.get_recent_conversations(puuid, count=1)
        return conversations[0] if conversations else None
