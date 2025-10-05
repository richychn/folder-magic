from __future__ import annotations

from authlib.integrations.starlette_client import OAuth
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from .agents import router as agent_router
from .api import auth, drive
from .config import get_settings
from .session import SessionStore


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.resolved_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.session_secret_key,
        https_only=settings.session_cookie_secure,
        max_age=settings.session_cookie_max_age,
        same_site="lax",
        session_cookie=f"{settings.session_cookie_name}_state",
    )

    session_store = SessionStore()
    app.state.session_store = session_store  # type: ignore[attr-defined]

    oauth = OAuth()
    oauth.register(
        name="google",
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={
            "scope": " ".join(settings.google_scopes),
            "prompt": "consent",
            "access_type": "offline",
            "include_granted_scopes": "true",
        },
    )
    app.state.oauth = oauth  # type: ignore[attr-defined]

    app.include_router(auth.router)
    app.include_router(drive.router)
    app.include_router(agent_router)

    @app.get("/healthz")
    def health_check() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
