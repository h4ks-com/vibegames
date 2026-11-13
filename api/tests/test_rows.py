"""The rows API: isolation, quotas and the public feed."""

from fastapi.testclient import TestClient

from app.settings import settings
from tests.conftest import login
from tests.conftest import new_client


def test_requires_login(client: TestClient) -> None:
    response = client.get("/__api/rows")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "login_required"


def test_put_get_delete(user_a: TestClient) -> None:
    put = user_a.put("/__api/rows/save", json={"value": {"level": 3, "hp": 12}})
    assert put.status_code == 200, put.text
    assert put.json()["bytes"] > 0

    got = user_a.get("/__api/rows/save")
    assert got.status_code == 200
    assert got.json()["value"] == {"level": 3, "hp": 12}
    assert got.json()["public"] is False

    listed = user_a.get("/__api/rows").json()
    assert [row["key"] for row in listed["rows"]] == ["save"]
    assert listed["usage"]["keys"] == 1

    assert user_a.delete("/__api/rows/save").status_code == 204
    assert user_a.get("/__api/rows/save").status_code == 404


def test_users_cannot_read_each_other(user_a: TestClient, user_b: TestClient) -> None:
    user_a.put("/__api/rows/secret", json={"value": {"s": "a"}})
    user_b.put("/__api/rows/secret", json={"value": {"s": "b"}})

    assert user_a.get("/__api/rows/secret").json()["value"] == {"s": "a"}
    assert user_b.get("/__api/rows/secret").json()["value"] == {"s": "b"}
    # bob's list only contains bob's rows
    assert user_b.get("/__api/rows").json()["usage"]["keys"] == 1


def test_apps_are_isolated(fake_idp: None) -> None:
    sobby = login(new_client("sobby"), "carol")
    other = login(new_client("other-game"), "carol")
    sobby.delete("/__api/rows")
    other.delete("/__api/rows")

    sobby.put("/__api/rows/score", json={"value": 10})
    assert other.get("/__api/rows/score").status_code == 404
    other.put("/__api/rows/score", json={"value": 99})
    assert sobby.get("/__api/rows/score").json()["value"] == 10

    sobby.__exit__(None, None, None)
    other.__exit__(None, None, None)


def test_public_feed(user_a: TestClient, user_b: TestClient, client: TestClient) -> None:
    user_a.put("/__api/rows/post:1", json={"value": {"text": "hello"}, "public": True})
    user_b.put("/__api/rows/draft", json={"value": {"text": "private"}})

    feed = client.get("/__api/public")
    assert feed.status_code == 200
    keys = [row["key"] for row in feed.json()["rows"]]
    assert "post:1" in keys
    assert "draft" not in keys

    entry = next(row for row in feed.json()["rows"] if row["key"] == "post:1")
    assert entry["value"] == {"text": "hello"}
    assert entry["user"]["sub"] == "alice"


def test_key_format_is_enforced(user_a: TestClient) -> None:
    assert user_a.put("/__api/rows/has%20space", json={"value": 1}).status_code == 400
    assert user_a.put("/__api/rows/" + "x" * 65, json={"value": 1}).status_code == 400
    assert user_a.put("/__api/rows/ok.key-name_1", json={"value": 1}).status_code == 200


def test_value_size_limit(user_a: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(settings, "OBBY_MAX_VALUE_BYTES", 16)
    response = user_a.put("/__api/rows/big", json={"value": "x" * 64})
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "too_large"


def test_key_quota(user_a: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(settings, "OBBY_MAX_KEYS", 2)
    assert user_a.put("/__api/rows/k1", json={"value": 1}).status_code == 200
    assert user_a.put("/__api/rows/k2", json={"value": 2}).status_code == 200
    third = user_a.put("/__api/rows/k3", json={"value": 3})
    assert third.status_code == 403
    assert third.json()["error"]["code"] == "quota_exceeded"
    # overwriting an existing key still works when full
    assert user_a.put("/__api/rows/k1", json={"value": 11}).status_code == 200


def test_byte_quota(user_a: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(settings, "OBBY_MAX_BYTES", 40)
    assert user_a.put("/__api/rows/a", json={"value": "x" * 20}).status_code == 200
    response = user_a.put("/__api/rows/b", json={"value": "y" * 20})
    assert response.status_code == 403


def test_cross_site_request_is_rejected(user_a: TestClient) -> None:
    response = user_a.get("/__api/rows", headers={"sec-fetch-site": "cross-site"})
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "cross_site"


def test_delete_all(user_a: TestClient) -> None:
    user_a.put("/__api/rows/a", json={"value": 1})
    user_a.put("/__api/rows/b", json={"value": 2})
    assert user_a.delete("/__api/rows").json()["deleted"] == 2
    assert user_a.get("/__api/rows").json()["rows"] == []
