"""
Chat Schemas

Pydantic models for chat requests and responses.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class ChatMessageRequest(BaseModel):
    """Request to send a chat message."""
    message: str
    conversation_id: Optional[str] = None  # None = new conversation


class ChatMessageResponse(BaseModel):
    """Response for non-streaming chat (used internally)."""
    conversation_id: str
    message_id: str
    content: str


class MessageSchema(BaseModel):
    """Schema for a single message."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    role: str
    content: str
    created_at: datetime


class ConversationSummary(BaseModel):
    """Summary of a conversation for listing."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    message_count: int
    last_message_preview: Optional[str] = None


class ConversationDetail(BaseModel):
    """Full conversation with messages."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: Optional[str]
    messages: list[MessageSchema]
    created_at: datetime
    updated_at: datetime


class ConversationUpdateRequest(BaseModel):
    """Request to update a conversation."""
    title: Optional[str] = None


class ConversationListResponse(BaseModel):
    """Response for listing conversations."""
    conversations: list[ConversationSummary]
    total: int


class StreamEvent(BaseModel):
    """SSE event structure."""
    type: str  # "start", "token", "done", "error"
    conversation_id: Optional[str] = None
    message_id: Optional[str] = None
    content: Optional[str] = None
