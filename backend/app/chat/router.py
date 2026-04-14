"""
Chat Router

API endpoints for AI-powered personalized tutoring.
Supports streaming responses via Server-Sent Events (SSE).
"""

import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..deps import get_db, get_current_user, get_ai_client
from ..db.models import User
from ..db.models.chat import Conversation
from ..integrations import ResilientAIClient
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
logger = logging.getLogger(__name__)

FREE_CONVERSATION_LIMIT = 3


def get_chat_service(
    db: Session = Depends(get_db),
    ai_client: ResilientAIClient = Depends(get_ai_client)
) -> ChatService:
    return ChatService(db, ai_client)


def _get_user_friendly_error(error: Exception) -> str:
    """Map API errors to user-friendly messages."""
    error_name = type(error).__name__
    error_str = str(error).lower()

    if "AuthenticationError" in error_name or "401" in str(error):
        return "I'm having trouble connecting right now. Please try again later."
    elif "RateLimitError" in error_name or "429" in str(error):
        return "I'm getting a lot of questions right now. Give me a moment and try again."
    elif "overloaded" in error_str or "529" in str(error):
        return "I'm a bit overloaded at the moment. Try again in a few seconds."
    elif "PermissionDeniedError" in error_name or "403" in str(error):
        return "I'm having trouble connecting right now. Please try again later."
    else:
        return "Something went wrong on my end. Please try sending your message again."


@router.get("/session-status")
def get_session_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """
    Returns conversation count and whether the free limit is hit.
    Used by the frontend to gate new conversations for Free users.
    """
    count = (
        db.query(Conversation)
        .filter(Conversation.user_id == current_user.id)
        .count()
    )
    is_pro = current_user.tier == "pro"
    limit_reached = not is_pro and count >= FREE_CONVERSATION_LIMIT

    return {
        "conversation_count": count,
        "limit": FREE_CONVERSATION_LIMIT,
        "limit_reached": limit_reached,
        "is_pro": is_pro,
    }


@router.post("/messages")
async def send_message(
    request: ChatMessageRequest,
    current_user: User = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
    db: Session = Depends(get_db),
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
    # Enforce free tier limit on new conversations only
    if not request.conversation_id and current_user.tier != "pro":
        count = (
            db.query(Conversation)
            .filter(Conversation.user_id == current_user.id)
            .count()
        )
        if count >= FREE_CONVERSATION_LIMIT:
            raise HTTPException(
                status_code=402,
                detail="Free plan limit reached. Upgrade to Pro for unlimited conversations."
            )

    async def event_stream():
        try:
            async for event in service.send_message_stream(
                user_id=current_user.id,
                message=request.message,
                conversation_id=request.conversation_id
            ):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            error_name = type(e).__name__
            logger.error(f"Chat stream error: {error_name}: {e}")
            user_message = _get_user_friendly_error(e)
            yield f"data: {json.dumps({'type': 'error', 'content': user_message})}\n\n"

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
