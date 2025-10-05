from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import HTTPException, Request, status
from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials

from .config import get_settings
from .session import SessionData, SessionStore


def get_session_store(request: Request) -> SessionStore:
    return request.app.state.session_store  # type: ignore[attr-defined]


def get_session(request: Request) -> tuple[str | None, SessionData | None]:
    settings = get_settings()
    session_id = request.cookies.get(settings.session_cookie_name)
    if not session_id:
        return None, None
    store = get_session_store(request)
    session = store.get(session_id)
    if session is None:
        return None, None
    return session_id, session


def require_session(request: Request) -> tuple[str, SessionData]:
    session_id, session = get_session(request)
    if not session_id or session is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return session_id, session


def ensure_valid_credentials(session_id: str, session: SessionData, store: SessionStore) -> Credentials:
    """Refresh credentials when expired and persist refreshed data."""

    creds = session.credentials
    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(GoogleRequest())
        except RefreshError as exc:  # pragma: no cover - defensive branch
            store.delete(session_id)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired") from exc
        session.credentials = creds
        session.created_at = datetime.utcnow()
        store.put(session_id, session)
    return creds


def expires_at_from_token(token: dict) -> datetime | None:
    expires_at = token.get("expires_at")
    if expires_at:
        return datetime.utcfromtimestamp(int(expires_at))
    expires_in = token.get("expires_in")
    if expires_in:
        return datetime.utcnow() + timedelta(seconds=int(expires_in))
    return None
