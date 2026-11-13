"""Logto login endpoints.

The cookie is set on BASE_DOMAIN (e.g. games.h4ks.com) so every project subdomain shares
one session. It is HttpOnly, so an XSS in any game cannot read it, and SameSite=Lax, so a
cross-site form cannot use it either.
"""

import secrets
import time

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from fastapi import Request
from fastapi.responses import RedirectResponse
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app import oidc
from app.database import get_db
from app.errors import ApiError
from app.identity import COOKIE_NAME
from app.identity import create_session
from app.identity import destroy_session
from app.identity import session_cookie_kwargs
from app.models import LoginState
from app.settings import settings

router = APIRouter(tags=["Auth"], prefix="/__auth")

LOGIN_STATE_TTL_SECONDS = 600


def safe_next(value: str | None) -> str:
    """Only allow same-site paths: no absolute URLs, no protocol-relative ones."""
    if not value or not value.startswith("/") or value.startswith("//"):
        return "/"
    return value


@router.get("/login")
def login(next: str = Query("/", max_length=512), db: Session = Depends(get_db)) -> RedirectResponse:
    if not settings.LOGTO_CLIENT_ID:
        raise ApiError(503, "auth_disabled", "LOGTO_CLIENT_ID is not configured")
    now = int(time.time())
    db.execute(delete(LoginState).where(LoginState.created_at < now - LOGIN_STATE_TTL_SECONDS))
    verifier, challenge = oidc.new_pkce()
    state = secrets.token_urlsafe(24)
    pending = LoginState(
        state=state,
        verifier=verifier,
        nonce=secrets.token_urlsafe(24),
        next_path=safe_next(next),
        created_at=now,
    )
    db.add(pending)
    db.commit()
    try:
        url = oidc.authorize_url(state, pending.nonce, challenge)
    except oidc.OIDCError as exc:
        raise ApiError(502, "oidc_unavailable", str(exc)) from exc
    return RedirectResponse(url, status_code=302)


@router.get("/callback")
def callback(
    code: str = Query(..., max_length=2048),
    state: str = Query(..., max_length=256),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    pending = db.get(LoginState, state)
    if pending is None:
        raise ApiError(400, "bad_state", "unknown or expired login state")
    verifier = pending.verifier
    next_path = pending.next_path
    db.delete(pending)
    db.commit()

    try:
        tokens = oidc.exchange_code(code, verifier)
        profile = oidc.userinfo(tokens["access_token"])
    except oidc.OIDCError as exc:
        raise ApiError(502, "oidc_failed", str(exc)) from exc

    raw, _ = create_session(
        db,
        sub=str(profile["sub"]),
        username=profile.get("username"),
        name=profile.get("name"),
        picture=profile.get("picture"),
    )
    response = RedirectResponse(next_path, status_code=302)
    response.set_cookie(value=raw, **session_cookie_kwargs())
    return response


@router.get("/logout")
def logout(request: Request, db: Session = Depends(get_db)) -> RedirectResponse:
    destroy_session(db, request.cookies.get(COOKIE_NAME))
    kwargs = session_cookie_kwargs()
    response = RedirectResponse("/", status_code=302)
    response.delete_cookie(
        kwargs["key"],
        domain=kwargs["domain"],
        path=kwargs["path"],
        secure=kwargs["secure"],
        httponly=kwargs["httponly"],
        samesite=kwargs["samesite"],
    )
    return response
