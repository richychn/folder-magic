from __future__ import annotations

import httpx
from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from google.oauth2.credentials import Credentials
from starlette import status

from ..config import Settings, get_settings
from ..security import (
    ensure_valid_credentials,
    expires_at_from_token,
    get_session,
    get_session_store,
    require_session,
)
from ..session import SessionData

router = APIRouter(prefix="/api/auth", tags=["auth"])


def get_oauth(request: Request) -> OAuth:
    return request.app.state.oauth  # type: ignore[attr-defined]


def get_settings_dependency() -> Settings:
    return get_settings()


@router.get("/login")
async def login(request: Request, oauth: OAuth = Depends(get_oauth)):
    redirect_uri = request.url_for("auth_callback")
    return await oauth.google.authorize_redirect(request, redirect_uri)


async def _fetch_userinfo(token: dict) -> dict:
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            "https://openidconnect.googleapis.com/v1/userinfo",
            headers={"Authorization": f"Bearer {token['access_token']}"},
        )
        response.raise_for_status()
        return response.json()


@router.get("/callback", name="auth_callback")
async def auth_callback(
    request: Request,
    oauth: OAuth = Depends(get_oauth),
    settings: Settings = Depends(get_settings_dependency),
):
    token = await oauth.google.authorize_access_token(request)
    if not token or "access_token" not in token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to obtain access token")

    user = None
    if token.get("id_token"):
        try:
            user = await oauth.google.parse_id_token(request, token)
        except Exception:  # pragma: no cover - fallback to userinfo
            user = None

    if not user:
        try:
            user = await _fetch_userinfo(token)
        except httpx.HTTPError as exc:  # pragma: no cover - network error
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Failed to fetch user profile") from exc

    credentials = Credentials(
        token=token["access_token"],
        refresh_token=token.get("refresh_token"),
        id_token=token.get("id_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        scopes=settings.google_scopes,
    )

    expiry = expires_at_from_token(token)
    if expiry:
        credentials.expiry = expiry

    session_store = get_session_store(request)
    session_id = session_store.create(
        SessionData(
            credentials=credentials,
            user={
                "email": user.get("email", ""),
                "name": user.get("name", ""),
                "picture": user.get("picture"),
            },
        )
    )

    redirect_target = f"{settings.frontend_origin}/drive"
    response = RedirectResponse(url=redirect_target, status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key=settings.session_cookie_name,
        value=session_id,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
        max_age=settings.session_cookie_max_age,
        path="/",
    )
    return response


@router.get("/me")
def get_me(request: Request, settings: Settings = Depends(get_settings_dependency)):
    session_id, session = get_session(request)
    if not session_id or session is None:
        return {"authenticated": False}
    return {
        "authenticated": True,
        "user": session.user,
        "frontend": settings.frontend_origin,
    }


@router.post("/logout")
def logout(request: Request, settings: Settings = Depends(get_settings_dependency)):
    session_id, _ = get_session(request)
    store = get_session_store(request)
    if session_id:
        store.delete(session_id)
    response = JSONResponse({"ok": True})
    response.delete_cookie(settings.session_cookie_name, path="/")
    return response


@router.get("/picker-token")
def picker_token(request: Request):
    session_id, session = require_session(request)
    store = get_session_store(request)
    credentials = ensure_valid_credentials(session_id, session, store)
    expires_at = credentials.expiry.isoformat() if credentials.expiry else None
    return {
        "access_token": credentials.token,
        "expires_at": expires_at,
        "token_type": "Bearer",
    }
