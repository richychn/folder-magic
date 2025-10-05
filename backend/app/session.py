from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from datetime import datetime
from threading import Lock
from typing import Dict, Optional

from google.oauth2.credentials import Credentials


@dataclass
class SessionData:
    """Holds authenticated user state in memory."""

    credentials: Credentials
    user: Dict[str, str]
    created_at: datetime = field(default_factory=datetime.utcnow)


class SessionStore:
    """Simple in-memory session registry keyed by opaque identifiers."""

    def __init__(self) -> None:
        self._entries: Dict[str, SessionData] = {}
        self._lock = Lock()

    def create(self, data: SessionData) -> str:
        session_id = secrets.token_urlsafe(32)
        with self._lock:
            self._entries[session_id] = data
        return session_id

    def put(self, session_id: str, data: SessionData) -> None:
        with self._lock:
            self._entries[session_id] = data

    def get(self, session_id: str) -> Optional[SessionData]:
        with self._lock:
            return self._entries.get(session_id)

    def delete(self, session_id: str) -> None:
        with self._lock:
            self._entries.pop(session_id, None)

    def cleanup(self, older_than: datetime) -> None:
        with self._lock:
            stale = [key for key, value in self._entries.items() if value.created_at < older_than]
            for key in stale:
                self._entries.pop(key, None)
