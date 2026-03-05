"""Chat API endpoints."""

import ast
import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Any, AsyncGenerator, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.agents.supervisor import get_supervisor_agent
from src.api._limiter import limiter
from src.core.llm import ServiceUnavailableError
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
    chart_data: Optional[dict] = Field(None, description="Chart data for visualization")
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
@limiter.limit("30/minute")
async def chat(
    request: Request,
    body: ChatRequest,
    session: AsyncSession = Depends(get_db_session),
) -> ChatResponse:
    """Process a chat message and return response.

    Args:
        body: Chat request with message.
        session: Database session.

    Returns:
        Chat response with bot answer.
    """
    # Generate session ID if not provided
    session_id = body.session_id or str(uuid.uuid4())

    logger.info(f"Chat request: session={session_id}")

    try:
        from sqlalchemy import select as sa_select

        # Fetch recent conversation history (last 5 messages) for context
        history_result = await session.execute(
            sa_select(ChatHistory.role, ChatHistory.content)
            .where(ChatHistory.session_id == session_id)
            .order_by(ChatHistory.created_at.desc())
            .limit(5)
        )
        conversation_history = [
            {"role": row.role, "content": row.content}
            for row in reversed(history_result.all())
        ]

        # Save user message to history
        user_history = ChatHistory(
            session_id=session_id,
            role="user",
            content=body.message,
        )
        session.add(user_history)
        await session.flush()

        # Process through supervisor agent with conversation context (60s timeout)
        supervisor = get_supervisor_agent()
        try:
            result = await asyncio.wait_for(
                supervisor.process(
                    query=body.message,
                    session_id=session_id,
                    conversation_history=conversation_history,
                ),
                timeout=60.0,
            )
        except asyncio.TimeoutError:
            logger.warning(f"Supervisor timeout: session={session_id}")
            await session.rollback()
            raise HTTPException(status_code=504, detail="Yêu cầu xử lý quá lâu, vui lòng thử lại.")

        # Save assistant response to history
        assistant_history = ChatHistory(
            session_id=session_id,
            role="assistant",
            content=result.get("response", ""),
            chat_metadata=json.dumps({
                "intent": result.get("intent"),
                "sources": result.get("sources"),
            }, ensure_ascii=False),
        )
        session.add(assistant_history)
        await session.commit()

        return ChatResponse(
            response=result.get("response", "Xin lỗi, đã xảy ra lỗi."),
            session_id=session_id,
            intent=result.get("intent"),
            sources=result.get("sources", []),
            chart_data=result.get("chart_data"),
        )

    except ServiceUnavailableError:
        await session.rollback()
        raise HTTPException(status_code=503, detail="Hệ thống AI đang tạm thời bận. Vui lòng thử lại sau ít phút.")
    except Exception as e:
        logger.error(f"Chat error: {e}")
        await session.rollback()
        raise HTTPException(status_code=500, detail="Lỗi xử lý tin nhắn")


@router.post("/chat/stream")
@limiter.limit("30/minute")
async def chat_stream(
    request: Request,
    body: ChatRequest,
    session: AsyncSession = Depends(get_db_session),
) -> StreamingResponse:
    """SSE streaming endpoint — two-phase: route+retrieve → stream LLM tokens.

    Events format: data: {json}\\n\\n
    """
    session_id = body.session_id or str(uuid.uuid4())
    logger.info(f"Stream chat request: session={session_id}")

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            from sqlalchemy import select as sa_select

            # Fetch conversation history
            history_result = await session.execute(
                sa_select(ChatHistory.role, ChatHistory.content)
                .where(ChatHistory.session_id == session_id)
                .order_by(ChatHistory.created_at.desc())
                .limit(5)
            )
            conversation_history = [
                {"role": row.role, "content": row.content}
                for row in reversed(history_result.all())
            ]

            # Save user message
            user_history = ChatHistory(
                session_id=session_id,
                role="user",
                content=body.message,
            )
            session.add(user_history)
            await session.flush()

            supervisor = get_supervisor_agent()
            accumulated_content = ""
            final_chart_data = None
            final_intent = None
            final_sources: list = []

            async for event in supervisor.process_stream(
                query=body.message,
                session_id=session_id,
                conversation_history=conversation_history,
            ):
                event_type = event.get("type")

                if event_type == "meta":
                    final_intent = event.get("intent")
                    sources = event.get("sources", [])
                    if sources:
                        final_sources = sources
                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

                elif event_type == "token":
                    accumulated_content += event.get("content", "")
                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

                elif event_type == "done":
                    final_chart_data = event.get("chart_data")
                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

                elif event_type == "error":
                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                    await session.rollback()
                    return

            # Save assistant response to DB
            assistant_history = ChatHistory(
                session_id=session_id,
                role="assistant",
                content=accumulated_content,
                chat_metadata=json.dumps({
                    "intent": final_intent,
                    "sources": final_sources,
                }, ensure_ascii=False),
            )
            session.add(assistant_history)
            await session.commit()

        except Exception as e:
            logger.error(f"Stream error: {e}", exc_info=True)
            error_event = {"type": "error", "message": "Lỗi xử lý tin nhắn"}
            yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"
            await session.rollback()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Tắt nginx buffering cho SSE
        },
    )


@router.post("/feedback", response_model=FeedbackResponse)
@limiter.limit("20/minute")
async def submit_feedback(
    http_request: Request,
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


@router.get("/sessions")
async def get_chat_sessions(
    limit: int = 50,
    session: AsyncSession = Depends(get_db_session),
) -> list[dict]:
    """Get list of all chat sessions with preview.

    Returns:
        List of sessions with first user message as title.
    """
    from sqlalchemy import select, func, text

    # Single query: aggregate stats + first user message via DISTINCT ON
    # Step 1: stats per session
    stats_subq = (
        select(
            ChatHistory.session_id,
            func.min(ChatHistory.created_at).label("first_at"),
            func.max(ChatHistory.created_at).label("last_at"),
            func.count(ChatHistory.id).label("message_count"),
        )
        .group_by(ChatHistory.session_id)
        .order_by(func.max(ChatHistory.created_at).desc())
        .limit(limit)
        .subquery("stats")
    )

    # Step 2: first user message per session (using row_number window function)
    row_num = (
        func.row_number()
        .over(
            partition_by=ChatHistory.session_id,
            order_by=ChatHistory.created_at.asc(),
        )
        .label("rn")
    )
    first_msg_subq = (
        select(ChatHistory.session_id, ChatHistory.content, row_num)
        .where(ChatHistory.role == "user")
        .subquery("first_msgs")
    )

    # Step 3: join stats with first user message
    query = (
        select(
            stats_subq.c.session_id,
            stats_subq.c.first_at,
            stats_subq.c.last_at,
            stats_subq.c.message_count,
            first_msg_subq.c.content.label("first_content"),
        )
        .join(
            first_msg_subq,
            (first_msg_subq.c.session_id == stats_subq.c.session_id)
            & (first_msg_subq.c.rn == 1),
            isouter=True,
        )
        .order_by(stats_subq.c.last_at.desc())
    )

    result = await session.execute(query)
    rows = result.all()

    return [
        {
            "session_id": r.session_id,
            "title": (r.first_content or "Cuộc trò chuyện mới")[:100],
            "message_count": r.message_count,
            "created_at": r.first_at.isoformat(),
            "updated_at": r.last_at.isoformat(),
        }
        for r in rows
    ]


@router.delete("/sessions/{session_id}")
async def delete_chat_session(
    session_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """Delete a chat session and all its messages."""
    from sqlalchemy import delete

    try:
        await session.execute(
            delete(ChatHistory).where(ChatHistory.session_id == session_id)
        )
        await session.commit()
        return {"success": True, "message": "Đã xóa cuộc trò chuyện"}
    except Exception as e:
        logger.error(f"Delete session error: {e}")
        await session.rollback()
        raise HTTPException(status_code=500, detail="Lỗi khi xóa cuộc trò chuyện")


@router.get("/history/{session_id}")
@limiter.limit("60/minute")
async def get_chat_history(
    http_request: Request,
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
        .order_by(ChatHistory.id.asc())
        .limit(limit)
    )
    messages = result.scalars().all()

    history = []
    for msg in messages:
        entry: dict[str, Any] = {
            "id": msg.id,
            "role": msg.role,
            "content": msg.content,
            "timestamp": msg.created_at.isoformat(),
        }

        # Parse metadata for assistant messages to restore sources
        if msg.role == "assistant" and msg.chat_metadata:
            try:
                meta = json.loads(msg.chat_metadata)
            except (json.JSONDecodeError, ValueError):
                try:
                    meta = ast.literal_eval(msg.chat_metadata)
                except Exception:
                    meta = None

            if meta and isinstance(meta, dict):
                if meta.get("sources"):
                    entry["sources"] = meta["sources"]
                if meta.get("intent"):
                    entry["intent"] = meta["intent"]

        history.append(entry)

    return history


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
    from src.database.postgres import get_postgres_db

    await manager.connect(websocket, session_id)
    db = get_postgres_db()

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

            # Process through supervisor + persist to DB
            supervisor = get_supervisor_agent()

            async with db.get_session() as db_session:
                try:
                    from sqlalchemy import select as sa_select

                    # Fetch recent history for context
                    hist_result = await db_session.execute(
                        sa_select(ChatHistory.role, ChatHistory.content)
                        .where(ChatHistory.session_id == session_id)
                        .order_by(ChatHistory.created_at.desc())
                        .limit(5)
                    )
                    conversation_history = [
                        {"role": row.role, "content": row.content}
                        for row in reversed(hist_result.all())
                    ]

                    # Save user message
                    user_history = ChatHistory(
                        session_id=session_id,
                        role="user",
                        content=message,
                    )
                    db_session.add(user_history)
                    await db_session.flush()

                    result = await supervisor.process(
                        query=message,
                        session_id=session_id,
                        conversation_history=conversation_history,
                    )

                    # Save assistant response
                    assistant_history = ChatHistory(
                        session_id=session_id,
                        role="assistant",
                        content=result.get("response", ""),
                        chat_metadata=json.dumps({
                            "intent": result.get("intent"),
                            "sources": result.get("sources"),
                        }, ensure_ascii=False),
                    )
                    db_session.add(assistant_history)
                    await db_session.commit()

                except Exception:
                    await db_session.rollback()
                    raise

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
