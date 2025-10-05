from __future__ import annotations

import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..config import get_settings
from ..session import SessionStore
from .service import stream_chat_completion

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
    session = store.get(session_id) if store and session_id else None

    if session is None:
        logger.info("websocket auth failed", extra={"reason": "missing session"})
        await websocket.close(code=4401)
        return

    await websocket.accept()
    logger.info("websocket connected", extra={"session_id": session_id, "user": session.user.get("email")})
    print("[agent] websocket connected", session_id)

    try:
        while True:
            payload = await websocket.receive_text()
            logger.info("message received", extra={"payload": payload})
            print("[agent] received", payload)
            try:
                data = json.loads(payload)
                user_message = data.get("message")
            except json.JSONDecodeError:
                user_message = payload

            if not user_message:
                await websocket.send_json({"type": "error", "message": "Empty message"})
                continue

            await websocket.send_json({"type": "ack", "message": user_message})
            print("[agent] ack sent", user_message)

            try:
                async for chunk in stream_chat_completion(user_message):
                    logger.info("sending delta", extra={"length": len(chunk)})
                    print("[agent] send", chunk)
                    await websocket.send_json({"type": "assistant", "delta": chunk})
            except Exception as exc:  # pragma: no cover - defensive
                logger.exception("agent streaming error")
                await websocket.send_json({"type": "error", "message": str(exc)})
                print("[agent] error", exc)

            await websocket.send_json({"type": "assistant", "event": "done"})
            print("[agent] done")
    except WebSocketDisconnect:
        logger.info("websocket disconnected", extra={"session_id": session_id})
        return
