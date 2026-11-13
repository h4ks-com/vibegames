"""Logto (OIDC) client for the login flow.

Only three things are needed: build an authorize URL, exchange the code, and read the
profile. We deliberately do **not** parse the id_token here: the access token comes from
our own TLS connection to the token endpoint (confidential client, PKCE-bound code), and
`/oidc/me` is the authoritative source for `sub` and the profile. That removes a JWT
parser from the request path and one class of "trusted the wrong token" bugs.
"""

import base64
import hashlib
import secrets
import time
from urllib.parse import urlencode

import requests

from app.settings import settings

DISCOVERY_TTL_SECONDS = 600
TIMEOUT_SECONDS = 10

_discovery: dict | None = None
_discovery_at: float = 0.0


class OIDCError(Exception):
    pass


def discovery() -> dict:
    global _discovery, _discovery_at
    now = time.time()
    if _discovery is not None and now - _discovery_at < DISCOVERY_TTL_SECONDS:
        return _discovery
    url = f"{settings.LOGTO_ISSUER.rstrip('/')}/.well-known/openid-configuration"
    try:
        response = requests.get(url, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
        document = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise OIDCError(f"cannot reach {url}: {exc}") from exc
    for field in ("authorization_endpoint", "token_endpoint", "userinfo_endpoint"):
        if field not in document:
            raise OIDCError(f"{url} is missing {field}")
    _discovery = document
    _discovery_at = now
    return document


def redirect_uri() -> str:
    if settings.LOGTO_REDIRECT_URI:
        return settings.LOGTO_REDIRECT_URI
    return f"{settings.APP_URL.rstrip('/')}/__auth/callback"


def new_pkce() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode()).digest()
    challenge = base64.urlsafe_b64encode(digest).decode().rstrip("=")
    return verifier, challenge


def authorize_url(state: str, nonce: str, code_challenge: str) -> str:
    document = discovery()
    params = {
        "response_type": "code",
        "client_id": settings.LOGTO_CLIENT_ID,
        "redirect_uri": redirect_uri(),
        "scope": settings.LOGTO_SCOPE,
        "state": state,
        "nonce": nonce,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    return f"{document['authorization_endpoint']}?{urlencode(params)}"


def exchange_code(code: str, code_verifier: str) -> dict:
    document = discovery()
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri(),
        "client_id": settings.LOGTO_CLIENT_ID,
        "code_verifier": code_verifier,
    }
    if settings.LOGTO_CLIENT_SECRET:
        data["client_secret"] = settings.LOGTO_CLIENT_SECRET
    try:
        response = requests.post(document["token_endpoint"], data=data, timeout=TIMEOUT_SECONDS)
    except requests.RequestException as exc:
        raise OIDCError(f"token request failed: {exc}") from exc
    if response.status_code != 200:
        raise OIDCError(f"token endpoint returned {response.status_code}")
    payload = response.json()
    if not payload.get("access_token"):
        raise OIDCError("token response has no access_token")
    return payload


def userinfo(access_token: str) -> dict:
    document = discovery()
    try:
        response = requests.get(
            document["userinfo_endpoint"],
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        raise OIDCError(f"userinfo request failed: {exc}") from exc
    if response.status_code != 200:
        raise OIDCError(f"userinfo returned {response.status_code}")
    profile = response.json()
    if not profile.get("sub"):
        raise OIDCError("userinfo has no sub")
    return profile
