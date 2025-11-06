from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import uuid


@dataclass
class Message:
    """Represents a single message in a conversation"""
    role: str
    content: str
    timestamp: str

    def to_dict(self) -> Dict:
        return {
            'role': self.role,
            'content': self.content,
            'timestamp': self.timestamp
        }

    @staticmethod
    def from_dict(data: Dict) -> 'Message':
        return Message(**data)


@dataclass
class Conversation:
    """
    Represents a conversation session between a player and the AI coach.

    Stores all messages in a conversation with PUUID as partition key
    and conversation_id as sort key.
    """
    puuid: str
    conversation_id: str  # UUID or timestamp-based ID
    messages: List[Message] = field(default_factory=list)
    session_id: Optional[str] = None  # To group related conversations
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def __post_init__(self):
        """Initialize timestamps if not provided"""
        now = datetime.utcnow().isoformat()
        if self.created_at is None:
            self.created_at = now
        if self.updated_at is None:
            self.updated_at = now

    def add_message(self, role: str, content: str):
        """Add a new message to the conversation"""
        message = Message(
            role=role,
            content=content,
            timestamp=datetime.utcnow().isoformat()
        )
        self.messages.append(message)
        self.update_timestamp()

    def update_timestamp(self):
        """Update the updated_at timestamp"""
        self.updated_at = datetime.utcnow().isoformat()

    def to_dynamodb_item(self) -> Dict:
        """Convert to DynamoDB item format"""
        item = {
            'puuid': self.puuid,
            'conversation_id': self.conversation_id,
            'messages': [msg.to_dict() for msg in self.messages],
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

        if self.session_id:
            item['session_id'] = self.session_id

        return item

    @staticmethod
    def from_dynamodb_item(item: Dict) -> 'Conversation':
        """Create Conversation instance from DynamoDB item"""
        messages = [Message.from_dict(msg) for msg in item.get('messages', [])]

        return Conversation(
            puuid=item['puuid'],
            conversation_id=item['conversation_id'],
            messages=messages,
            session_id=item.get('session_id'),
            created_at=item.get('created_at'),
            updated_at=item.get('updated_at')
        )

    @staticmethod
    def create_new(puuid: str, session_id: Optional[str] = None) -> 'Conversation':
        """Create a new conversation with a generated ID"""
        conversation_id = f"{datetime.utcnow().isoformat()}_{uuid.uuid4().hex[:8]}"
        return Conversation(
            puuid=puuid,
            conversation_id=conversation_id,
            session_id=session_id
        )
