"""The login flow, mostly the parts that must fail closed."""

from fastapi.testclient import TestClient

from app import oidc
from app.settings import settings
from tests.conftest import login
from tests.conftest import new_client


def test_authorize_url_uses_pkce_s256(monkeypatch) -> None:
    monkeypatch.setattr(
        oidc,
        "discovery",
        lambda: {
            "authorization_endpoint": "https://logto.test/oidc/auth",
            "token_endpoint": "https://logto.test/oidc/token",
            "userinfo_endpoint": "https://logto.test/oidc/me",
        },
    )
    url = oidc.authorize_url("st", "no", "ch")
    assert url.startswith("https://logto.test/oidc/auth?")
    assert "code_challenge_method=S256" in url
    assert "client_id=test-client" in url
    assert "redirect_uri=http%3A%2F%2Fgames.test%2F__auth%2Fcallback" in url


def test_login_redirects_to_logto(client: TestClient, fake_idp: None) -> None:
    response = client.get("/__auth/login", follow_redirects=False)
    assert response.status_code == 302
    location = response.headers["location"]
    assert location.startswith("https://logto.test/oidc/auth?")
    assert "code_challenge_method=S256" in location
    assert "state=" in location


def test_callback_rejects_unknown_state(client: TestClient, fake_idp: None) -> None:
    response = client.get("/__auth/callback?code=alice&state=nope", follow_redirects=False)
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "bad_state"


def test_login_sets_httponly_session_cookie(fake_idp: None) -> None:
    test_client = new_client("sobby")
    response = test_client.get("/__auth/login", follow_redirects=False)
    state = response.headers["location"].split("state=")[1].split("&")[0]
    callback = test_client.get(f"/__auth/callback?code=dave&state={state}", follow_redirects=False)

    assert callback.status_code == 302
    cookie = callback.headers["set-cookie"].lower()
    assert "vg_session=" in cookie
    assert "httponly" in cookie
    assert "samesite=lax" in cookie
    assert "domain=games.test" in cookie

    me = test_client.get("/__api/me").json()
    assert me["sub"] == "dave"
    assert me["username"] == "user_dave"
    test_client.__exit__(None, None, None)


def test_logout_drops_the_session(fake_idp: None) -> None:
    test_client = login(new_client("sobby"), "erin")
    assert test_client.get("/__api/me").status_code == 200

    test_client.get("/__auth/logout", follow_redirects=False)
    assert test_client.get("/__api/me").status_code == 401
    test_client.__exit__(None, None, None)


def test_login_disabled_without_client_id(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(settings, "LOGTO_CLIENT_ID", "")
    response = client.get("/__auth/login", follow_redirects=False)
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "auth_disabled"


def test_session_survives_for_other_subdomains(fake_idp: None) -> None:
    """One login, every project: the cookie is scoped to BASE_DOMAIN, not the host."""
    first = login(new_client("sobby"), "frank")
    cookie = first.cookies.get("vg_session")

    second = new_client("other-game")
    second.cookies.set("vg_session", cookie, domain="games.test")
    assert second.get("/__api/me").json()["sub"] == "frank"
    first.__exit__(None, None, None)
    second.__exit__(None, None, None)
