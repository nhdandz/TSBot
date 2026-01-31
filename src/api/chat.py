"""Chat API endpoints."""

import logging
import uuid
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.agents.supervisor import get_supervisor_agent
from src.database.models import ChatHistory, Feedback
from src.database.postgres import get_db_session

logger = logging.getLogger(__name__)
router = APIRouter()


# Request/Response Models
class ChatRequest(BaseModel):
    """Chat request model."""

    message: str = Field(..., min_length=1, max_length=2000, description="User message")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")


class ChatResponse(BaseModel):
    """Chat response model."""

    response: str = Field(..., description="Bot response")
    session_id: str = Field(..., description="Session ID")
    intent: Optional[str] = Field(None, description="Detected intent")
    sources: list[dict] = Field(default=[], description="Source references")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class FeedbackRequest(BaseModel):
    """Feedback request model."""

    session_id: str = Field(..., description="Session ID")
    message_id: Optional[int] = Field(None, description="Specific message ID")
    rating: Optional[int] = Field(None, ge=1, le=5, description="Rating 1-5")
    feedback_type: str = Field(..., description="Type: helpful, not_helpful, incorrect, incomplete")
    comment: Optional[str] = Field(None, max_length=1000, description="Additional comment")


class FeedbackResponse(BaseModel):
    """Feedback response model."""

    success: bool
    message: str


# REST Endpoints
@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    session: AsyncSession = Depends(get_db_session),
) -> ChatResponse:
    """Process a chat message and return response.

    Args:
        request: Chat request with message.
        session: Database session.

    Returns:
        Chat response with bot answer.
    """
    # Generate session ID if not provided
    session_id = request.session_id or str(uuid.uuid4())

    logger.info(f"Chat request: session={session_id}, message={request.message[:50]}...")

    try:
        # Save user message to history
        user_history = ChatHistory(
            session_id=session_id,
            role="user",
            content=request.message,
        )
        session.add(user_history)
        await session.flush()

        # Process through supervisor agent
        supervisor = get_supervisor_agent()
        result = await supervisor.process(
            query=request.message,
            session_id=session_id,
        )

        # Save assistant response to history
        assistant_history = ChatHistory(
            session_id=session_id,
            role="assistant",
            content=result.get("response", ""),
            metadata=str({
                "intent": result.get("intent"),
                "sources": result.get("sources"),
            }),
        )
        session.add(assistant_history)
        await session.commit()

        return ChatResponse(
            response=result.get("response", "Xin lỗi, đã xảy ra lỗi."),
            session_id=session_id,
            intent=result.get("intent"),
            sources=result.get("sources", []),
        )

    except Exception as e:
        logger.error(f"Chat error: {e}")
        await session.rollback()
        raise HTTPException(status_code=500, detail="Lỗi xử lý tin nhắn")


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    request: FeedbackRequest,
    session: AsyncSession = Depends(get_db_session),
) -> FeedbackResponse:
    """Submit feedback for a chat response.

    Args:
        request: Feedback request.
        session: Database session.

    Returns:
        Feedback submission result.
    """
    try:
        feedback = Feedback(
            session_id=request.session_id,
            chat_history_id=request.message_id,
            rating=request.rating,
            feedback_type=request.feedback_type,
            comment=request.comment,
        )
        session.add(feedback)
        await session.commit()

        logger.info(f"Feedback received: session={request.session_id}, type={request.feedback_type}")

        return FeedbackResponse(
            success=True,
            message="Cảm ơn bạn đã gửi phản hồi!",
        )

    except Exception as e:
        logger.error(f"Feedback error: {e}")
        await session.rollback()
        raise HTTPException(status_code=500, detail="Lỗi khi gửi phản hồi")


@router.get("/history/{session_id}")
async def get_chat_history(
    session_id: str,
    limit: int = 50,
    session: AsyncSession = Depends(get_db_session),
) -> list[dict]:
    """Get chat history for a session.

    Args:
        session_id: Session ID.
        limit: Maximum messages to return.
        session: Database session.

    Returns:
        List of chat messages.
    """
    from sqlalchemy import select

    result = await session.execute(
        select(ChatHistory)
        .where(ChatHistory.session_id == session_id)
        .order_by(ChatHistory.created_at.desc())
        .limit(limit)
    )
    messages = result.scalars().all()

    return [
        {
            "id": msg.id,
            "role": msg.role,
            "content": msg.content,
            "timestamp": msg.created_at.isoformat(),
        }
        for msg in reversed(messages)  # Return in chronological order
    ]


# WebSocket for streaming responses
class ConnectionManager:
    """WebSocket connection manager."""

    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket

    def disconnect(self, session_id: str):
        self.active_connections.pop(session_id, None)

    async def send_message(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_json(message)


manager = ConnectionManager()


@router.websocket("/ws/{session_id}")
async def websocket_chat(
    websocket: WebSocket,
    session_id: str,
):
    """WebSocket endpoint for streaming chat.

    Args:
        websocket: WebSocket connection.
        session_id: Session ID.
    """
    await manager.connect(websocket, session_id)

    try:
        while True:
            # Receive message
            data = await websocket.receive_json()
            message = data.get("message", "")

            if not message:
                continue

            logger.info(f"WebSocket message: session={session_id}, message={message[:50]}...")

            # Send acknowledgment
            await manager.send_message(session_id, {
                "type": "ack",
                "message": "Processing...",
            })

            # Process through supervisor
            supervisor = get_supervisor_agent()

            # Stream response if supported
            result = await supervisor.process(
                query=message,
                session_id=session_id,
            )

            # Send response
            await manager.send_message(session_id, {
                "type": "response",
                "response": result.get("response", ""),
                "intent": result.get("intent"),
                "sources": result.get("sources", []),
            })

    except WebSocketDisconnect:
        manager.disconnect(session_id)
        logger.info(f"WebSocket disconnected: session={session_id}")

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(session_id)
