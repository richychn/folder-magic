from __future__ import annotations

import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..config import get_settings
from ..session import SessionStore
from agents import OpenAIConversationsSession

from .service import run_agent

router = APIRouter(prefix="/api/agent", tags=["agent"])
logger = logging.getLogger(__name__)


def _get_session_store(websocket: WebSocket) -> SessionStore | None:
    return getattr(websocket.app.state, "session_store", None)  # type: ignore[attr-defined]


@router.websocket("/chat")
async def chat_endpoint(websocket: WebSocket):
    settings = get_settings()
    session_cookie_name = settings.session_cookie_name

    session_id = websocket.cookies.get(session_cookie_name)
    store = _get_session_store(websocket)
    if store is None:
        logger.error("session store unavailable for websocket")
        await websocket.close(code=1011)
        return

    session = store.get(session_id) if session_id else None

    if session is None:
        logger.info("websocket auth failed", extra={"reason": "missing session"})
        await websocket.close(code=4401)
        return

    await websocket.accept()
    logger.info("websocket connected", extra={"session_id": session_id, "user": session.user.get("email")})

    if session.pending_agent_messages:
        logger.info(
            "sending pending agent messages",
            extra={"count": len(session.pending_agent_messages)},
        )
        for pending in session.pending_agent_messages:
            await websocket.send_json({"type": "assistant", "delta": pending})
            await websocket.send_json({"type": "assistant", "event": "done"})
        session.pending_agent_messages.clear()
        store.put(session_id, session)

    try:
        while True:
            payload = await websocket.receive_text()
            logger.info("message received", extra={"payload": payload})
            try:
                data = json.loads(payload)
                user_message = data.get("message")
            except json.JSONDecodeError:
                user_message = payload

            if not user_message:
                await websocket.send_json({"type": "error", "message": "Empty message"})
                continue

            await websocket.send_json({"type": "ack", "message": user_message})

            if session.agent_session is None:
                session.agent_session = OpenAIConversationsSession()
            convo_session = session.agent_session

            try:
                stream = await run_agent(convo_session, user_message)
                async for chunk in stream:
                    logger.info("sending delta", extra={"length": len(chunk)})
                    await websocket.send_json({"type": "assistant", "delta": chunk})
            except Exception as exc:  # pragma: no cover - defensive
                logger.exception("agent streaming error")
                await websocket.send_json({"type": "error", "message": str(exc)})

            await websocket.send_json({"type": "assistant", "event": "done"})

            store.put(session_id, session)
    except WebSocketDisconnect:
        logger.info("websocket disconnected", extra={"session_id": session_id})
        return
