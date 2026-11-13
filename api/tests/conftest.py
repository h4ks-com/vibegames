import os
import tempfile
from collections.abc import Iterator
from pathlib import Path
from urllib.parse import parse_qs
from urllib.parse import urlparse

import pytest
from fastapi.testclient import TestClient

API_ROOT = Path(__file__).resolve().parent.parent
os.chdir(API_ROOT)  # alembic.ini and ./static are resolved relative to this directory

_TMP = tempfile.mkdtemp(prefix="vibegames-tests-")
os.environ["GITHUB_API_TOKEN"] = "test-token"
os.environ["GITHUB_REPOSITORY"] = "https://github.com/h4ks-com/vibedgames-ai.git"
os.environ["PROJECTS_PATH"] = "games"
os.environ["API_KEYS"] = "test-key"
os.environ["CAPTURE_API_URL"] = "http://capture.test"
os.environ["CAPTURE_API_KEY"] = "test-capture"
os.environ["DB_PATH"] = f"sqlite:///{_TMP}/test.db"
os.environ["APP_URL"] = "http://games.test"
os.environ["ENABLE_SUBDOMAINS"] = "true"
os.environ["BASE_DOMAIN"] = "games.test"
os.environ["LOGTO_ISSUER"] = "https://logto.test/oidc"
os.environ["LOGTO_CLIENT_ID"] = "test-client"
os.environ["LOGTO_CLIENT_SECRET"] = "test-secret"
os.environ["SESSION_COOKIE_DOMAIN"] = "games.test"
os.environ["OBBY_DEV_APP"] = "dev"

from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from app import app as fastapi_app  # noqa: E402  (must come after the env above)
from app.database import engine  # noqa: E402
from app.models import Base  # noqa: E402


def _bootstrap_schema() -> None:
    """Prepare the database the way the app does in production.

    The initial alembic revision is empty: the schema is created by `create_all()` and
    alembic only tracks the deltas, which is why the lifespan calls both. Do the same here
    and stamp at head, so the tests run against the real schema.
    """
    Base.metadata.create_all(bind=engine)
    config = Config(str(API_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(API_ROOT / "alembic"))
    command.stamp(config, "head")


_bootstrap_schema()


@pytest.fixture()
def fake_idp(monkeypatch: pytest.MonkeyPatch) -> None:
    """Stand-in for Logto: `code` becomes the subject, no network."""
    from app import oidc

    def authorize_url(state: str, nonce: str, code_challenge: str) -> str:
        return (
            "https://logto.test/oidc/auth?response_type=code"
            f"&state={state}&nonce={nonce}&code_challenge={code_challenge}&code_challenge_method=S256"
        )

    def exchange_code(code: str, code_verifier: str) -> dict:
        assert code_verifier
        return {"access_token": f"at:{code}"}

    def userinfo(access_token: str) -> dict:
        sub = access_token.split(":", 1)[1]
        return {"sub": sub, "username": f"user_{sub}", "name": sub.title(), "picture": None}

    monkeypatch.setattr(oidc, "authorize_url", authorize_url)
    monkeypatch.setattr(oidc, "exchange_code", exchange_code)
    monkeypatch.setattr(oidc, "userinfo", userinfo)


@pytest.fixture()
def client() -> Iterator[TestClient]:
    with TestClient(fastapi_app, base_url="https://sobby.games.test") as test_client:
        yield test_client


def new_client(app_name: str = "sobby") -> TestClient:
    test_client = TestClient(fastapi_app, base_url=f"https://{app_name}.games.test")
    test_client.__enter__()
    return test_client


def reset_rows(test_client: TestClient) -> None:
    """Each test starts from an empty namespace for its user."""
    assert test_client.delete("/__api/rows").status_code == 200


def login(test_client: TestClient, sub: str) -> TestClient:
    """Walk the login redirects with a fake code; returns the same client, now authenticated."""
    response = test_client.get("/__auth/login?next=/", follow_redirects=False)
    assert response.status_code == 302, response.text
    state = parse_qs(urlparse(response.headers["location"]).query)["state"][0]
    response = test_client.get(f"/__auth/callback?code={sub}&state={state}", follow_redirects=False)
    assert response.status_code == 302, response.text
    assert "vg_session" in test_client.cookies
    return test_client


@pytest.fixture()
def user_a(fake_idp: None) -> Iterator[TestClient]:
    test_client = new_client("sobby")
    login(test_client, "alice")
    reset_rows(test_client)
    yield test_client
    test_client.__exit__(None, None, None)


@pytest.fixture()
def user_b(fake_idp: None) -> Iterator[TestClient]:
    test_client = new_client("sobby")
    login(test_client, "bob")
    reset_rows(test_client)
    yield test_client
    test_client.__exit__(None, None, None)
