"""
Chat Router

API endpoints for AI-powered personalized tutoring.
Supports streaming responses via Server-Sent Events (SSE).
"""

import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..deps import get_db, get_current_user, get_anthropic_client
from ..db.models import User
from ..integrations import AnthropicClient
from ..common.errors import NotFoundError
from .service import ChatService
from .schemas import (
    ChatMessageRequest,
    ConversationSummary,
    ConversationDetail,
    ConversationUpdateRequest,
    ConversationListResponse,
    MessageSchema,
)

router = APIRouter(tags=["chat"])


def get_chat_service(
    db: Session = Depends(get_db),
    anthropic: AnthropicClient = Depends(get_anthropic_client)
) -> ChatService:
    return ChatService(db, anthropic)


@router.post("/messages")
async def send_message(
    request: ChatMessageRequest,
    current_user: User = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
):
    """
    Send a message and get a streamed AI response.

    Uses Server-Sent Events (SSE) for real-time streaming.

    Response format (each line is a separate event):
    ```
    data: {"type": "start", "conversation_id": "uuid"}
    data: {"type": "token", "content": "Hello"}
    data: {"type": "token", "content": " there"}
    data: {"type": "done", "message_id": "uuid"}
    ```

    On error:
    ```
    data: {"type": "error", "content": "Error message"}
    ```
    """
    async def event_stream():
        async for event in service.send_message_stream(
            user_id=current_user.id,
            message=request.message,
            conversation_id=request.conversation_id
        ):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Important for nginx
        }
    )


@router.get("/conversations", response_model=ConversationListResponse)
def list_conversations(
    current_user: User = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
) -> ConversationListResponse:
    """List all conversations for the current user."""
    conversations = service.get_conversations(current_user.id)

    summaries = []
    for conv in conversations:
        message_count = len(conv.messages)
        last_message = conv.messages[-1] if conv.messages else None
        preview = None
        if last_message:
            preview = last_message.content[:100] + "..." if len(last_message.content) > 100 else last_message.content

        summaries.append(ConversationSummary(
            id=conv.id,
            title=conv.title,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
            message_count=message_count,
            last_message_preview=preview
        ))

    return ConversationListResponse(
        conversations=summaries,
        total=len(summaries)
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
) -> ConversationDetail:
    """Get a conversation with full message history."""
    conversation = service.get_conversation(current_user.id, conversation_id)

    if not conversation:
        raise NotFoundError("Conversation not found")

    messages = [
        MessageSchema(
            id=msg.id,
            role=msg.role,
            content=msg.content,
            created_at=msg.created_at
        )
        for msg in conversation.messages
    ]

    return ConversationDetail(
        id=conversation.id,
        title=conversation.title,
        messages=messages,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at
    )


@router.delete("/conversations/{conversation_id}")
def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
) -> dict:
    """Delete a conversation and all its messages."""
    deleted = service.delete_conversation(current_user.id, conversation_id)

    if not deleted:
        raise NotFoundError("Conversation not found")

    return {"deleted": True, "conversation_id": conversation_id}


@router.patch("/conversations/{conversation_id}", response_model=ConversationDetail)
def update_conversation(
    conversation_id: str,
    request: ConversationUpdateRequest,
    current_user: User = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
) -> ConversationDetail:
    """Update a conversation (e.g., rename title)."""
    conversation = service.update_conversation(
        user_id=current_user.id,
        conversation_id=conversation_id,
        title=request.title
    )

    if not conversation:
        raise NotFoundError("Conversation not found")

    messages = [
        MessageSchema(
            id=msg.id,
            role=msg.role,
            content=msg.content,
            created_at=msg.created_at
        )
        for msg in conversation.messages
    ]

    return ConversationDetail(
        id=conversation.id,
        title=conversation.title,
        messages=messages,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at
    )
