"""Per-app, per-user rows.

Every endpoint resolves two things on the server before it runs:

* ``app``  — the subdomain the browser is on (``current_app``);
* ``user`` — the session cookie (``current_user``).

No endpoint accepts an app id or a user id from the client. That is why "write into
another app's data" and "post as another user" are not permission bugs here: there is
nowhere to put the claim.
"""

import json
import re
import time
from typing import Any

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from fastapi import Response
from pydantic import BaseModel
from sqlalchemy import delete
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.errors import ApiError
from app.identity import current_app
from app.identity import current_user
from app.models import Row
from app.models import UserSession
from app.settings import settings

router = APIRouter(tags=["Rows"], prefix="/__api")

KEY_PATTERN = re.compile(r"^[a-zA-Z0-9_.:-]{1,64}$")
PUBLIC_LIMIT_MAX = 50

_buckets: dict[str, tuple[float, float]] = {}


class RowBody(BaseModel):
    value: Any
    public: bool = False


def consume_token(bucket_key: str) -> None:
    """In-process token bucket. Per worker, which is fine: limits are approximate by design."""
    per_minute = max(settings.OBBY_WRITES_PER_MINUTE, 1)
    capacity = float(per_minute)
    rate = per_minute / 60.0
    now = time.monotonic()
    tokens, last = _buckets.get(bucket_key, (capacity, now))
    tokens = min(capacity, tokens + (now - last) * rate)
    if tokens < 1.0:
        _buckets[bucket_key] = (tokens, now)
        raise ApiError(429, "rate_limited", "too many writes, try again in a moment")
    _buckets[bucket_key] = (tokens - 1.0, now)


def usage(db: Session, app: str, sub: str) -> tuple[int, int]:
    count, total = db.execute(
        select(func.count(Row.key), func.coalesce(func.sum(Row.bytes), 0)).where(Row.app == app, Row.usr == sub)
    ).one()
    return int(count), int(total)


def row_payload(row: Row) -> dict:
    return {
        "key": row.key,
        "value": json.loads(row.value),
        "public": bool(row.public),
        "bytes": row.bytes,
        "updated_at": row.updated_at,
    }


@router.get("/health")
def health() -> dict:
    return {"ok": True}


@router.get("/me")
def me(user: UserSession = Depends(current_user)) -> dict:
    return {"sub": user.sub, "username": user.username, "name": user.name, "picture": user.picture}


@router.get("/rows")
def list_rows(
    app: str = Depends(current_app),
    user: UserSession = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict:
    rows = db.scalars(select(Row).where(Row.app == app, Row.usr == user.sub).order_by(Row.key)).all()
    count, total = usage(db, app, user.sub)
    return {
        "rows": [row_payload(row) for row in rows],
        "usage": {
            "keys": count,
            "bytes": total,
            "max_keys": settings.OBBY_MAX_KEYS,
            "max_bytes": settings.OBBY_MAX_BYTES,
        },
    }


@router.get("/rows/{key}")
def get_row(
    key: str,
    app: str = Depends(current_app),
    user: UserSession = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict:
    row = db.get(Row, (app, user.sub, key))
    if row is None:
        raise ApiError(404, "not_found", "no such row")
    return row_payload(row)


@router.put("/rows/{key}")
def put_row(
    key: str,
    body: RowBody,
    app: str = Depends(current_app),
    user: UserSession = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict:
    if not KEY_PATTERN.match(key):
        raise ApiError(400, "bad_key", "keys must match ^[a-zA-Z0-9_.:-]{1,64}$")
    consume_token(f"{app}:{user.sub}")

    encoded = json.dumps(body.value, separators=(",", ":"), ensure_ascii=False)
    size = len(encoded.encode())
    if size > settings.OBBY_MAX_VALUE_BYTES:
        raise ApiError(413, "too_large", f"value is {size} bytes, limit is {settings.OBBY_MAX_VALUE_BYTES}")

    existing = db.get(Row, (app, user.sub, key))
    count, total = usage(db, app, user.sub)
    if existing is None and count >= settings.OBBY_MAX_KEYS:
        raise ApiError(403, "quota_exceeded", f"at most {settings.OBBY_MAX_KEYS} keys per app")
    grown = total - (existing.bytes if existing else 0) + size
    if grown > settings.OBBY_MAX_BYTES:
        raise ApiError(403, "quota_exceeded", f"at most {settings.OBBY_MAX_BYTES} bytes per app")

    if body.public and not (existing is not None and existing.public):
        public_rows = db.scalar(select(func.count(Row.key)).where(Row.app == app, Row.public.is_(True)))
        if int(public_rows or 0) >= settings.OBBY_MAX_PUBLIC_ROWS:
            raise ApiError(403, "quota_exceeded", "this app has too many public rows")

    now = int(time.time())
    if existing is None:
        db.add(Row(app=app, usr=user.sub, key=key, value=encoded, public=body.public, bytes=size, updated_at=now))
    else:
        existing.value = encoded
        existing.public = body.public
        existing.bytes = size
        existing.updated_at = now
    db.commit()
    return {"key": key, "bytes": size, "public": body.public, "updated_at": now}


@router.delete("/rows/{key}")
def delete_row(
    key: str,
    app: str = Depends(current_app),
    user: UserSession = Depends(current_user),
    db: Session = Depends(get_db),
) -> Response:
    row = db.get(Row, (app, user.sub, key))
    if row is None:
        raise ApiError(404, "not_found", "no such row")
    db.delete(row)
    db.commit()
    return Response(status_code=204)


@router.delete("/rows")
def delete_all_rows(
    app: str = Depends(current_app),
    user: UserSession = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Hard-delete everything this user stored in this app."""
    count = int(db.scalar(select(func.count(Row.key)).where(Row.app == app, Row.usr == user.sub)) or 0)
    db.execute(delete(Row).where(Row.app == app, Row.usr == user.sub))
    db.commit()
    return {"deleted": count}


@router.get("/public")
def public_rows(
    app: str = Depends(current_app),
    limit: int = Query(50, ge=1, le=PUBLIC_LIMIT_MAX),
    db: Session = Depends(get_db),
) -> dict:
    """Rows their authors marked public, newest first. Readable without a session."""
    username = (
        select(UserSession.username)
        .where(UserSession.sub == Row.usr)
        .order_by(UserSession.created_at.desc())
        .limit(1)
        .correlate(Row)
        .scalar_subquery()
    )
    rows = db.execute(
        select(Row, username).where(Row.app == app, Row.public.is_(True)).order_by(Row.updated_at.desc()).limit(limit)
    ).all()
    return {
        "rows": [
            {**row_payload(row), "user": {"sub": row.usr, "username": username_value}} for row, username_value in rows
        ]
    }
