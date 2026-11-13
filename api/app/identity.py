"""Who is calling: the app (subdomain) and the user (session cookie).

Both are resolved on the server, before any handler runs:

* the app is the subdomain of the project the browser is on — there is no request
  parameter anywhere that names an app;
* the user is an opaque cookie looked up in `sessions` — no header or body field is
  read for an identity.

That is the whole isolation story of the rows API.
"""

import hashlib
import secrets
import time

from fastapi import Depends
from fastapi import Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.errors import ApiError
from app.models import UserSession
from app.project_naming import extract_subdomain
from app.project_naming import get_host_from_headers
from app.settings import settings

COOKIE_NAME = settings.SESSION_COOKIE_NAME
TOUCH_INTERVAL_SECONDS = 3600


def session_ttl_seconds() -> int:
    return settings.SESSION_TTL_DAYS * 86400


def hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def cookie_domain() -> str | None:
    domain = settings.SESSION_COOKIE_DOMAIN or settings.BASE_DOMAIN
    if not domain or domain in ("localhost", "127.0.0.1"):
        return None
    return domain


def session_cookie_kwargs() -> dict:
    domain = cookie_domain()
    return {
        "key": COOKIE_NAME,
        "httponly": True,
        "samesite": "lax",
        "secure": domain is not None,
        "domain": domain,
        "path": "/",
        "max_age": session_ttl_seconds(),
    }


def create_session(
    db: Session,
    sub: str,
    username: str | None,
    name: str | None,
    picture: str | None,
) -> tuple[str, UserSession]:
    now = int(time.time())
    raw = secrets.token_urlsafe(32)
    record = UserSession(
        id=hash_token(raw),
        sub=sub,
        username=username,
        name=name,
        picture=picture,
        created_at=now,
        last_seen=now,
        expires_at=now + session_ttl_seconds(),
    )
    db.add(record)
    db.commit()
    return raw, record


def resolve_session(db: Session, raw: str | None) -> UserSession | None:
    if not raw:
        return None
    record = db.get(UserSession, hash_token(raw))
    if record is None:
        return None
    now = int(time.time())
    if record.expires_at <= now:
        db.delete(record)
        db.commit()
        return None
    if now - record.last_seen > TOUCH_INTERVAL_SECONDS:
        record.last_seen = now
        record.expires_at = now + session_ttl_seconds()
        db.commit()
    return record


def destroy_session(db: Session, raw: str | None) -> None:
    if not raw:
        return
    record = db.get(UserSession, hash_token(raw))
    if record is not None:
        db.delete(record)
        db.commit()


def current_app(request: Request) -> str:
    """The app is the subdomain. Never a parameter, never a header."""
    if settings.ENABLE_SUBDOMAINS:
        host = get_host_from_headers(dict(request.headers))
        app = extract_subdomain(host, settings.BASE_DOMAIN) if host else None
        if not app:
            raise ApiError(404, "not_a_project", "this host is not a project subdomain")
        return app
    return settings.OBBY_DEV_APP


def current_user(request: Request, db: Session = Depends(get_db)) -> UserSession:
    guard_same_site(request)
    record = resolve_session(db, request.cookies.get(COOKIE_NAME))
    if record is None:
        raise ApiError(401, "login_required", "sign in at /__auth/login")
    return record


def guard_same_site(request: Request) -> None:
    """Cheap CSRF belt on top of SameSite=Lax: reject anything the browser marks cross-site."""
    site = request.headers.get("sec-fetch-site")
    if site and site not in ("same-origin", "none"):
        raise ApiError(403, "cross_site", "cross-site requests are not allowed")
