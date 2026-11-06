import datetime as dt

import jwt
import pytest
from conftest import FakeWSN

from app.config import settings

PADRON = "WS_SR_PADRON_A13"
INSCRIPTION = "WS_SR_CONSTANCIA_INSCRIPCION"


def test_health_needs_no_auth(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_catalog_routes_are_registered(client):
    paths = set(client.get("/api/v1/openapi.json").json()["paths"])
    assert {
        "/api/v1/token",
        "/api/v1/padron",
        "/api/v1/padron/health",
        "/api/v1/inscription",
        "/api/v1/inscription/health",
    } <= paths


@pytest.mark.parametrize(
    ("username", "password"),
    [("tester", "wrong"), ("someone", "test-password"), ("tester", "test-password ")],
)
def test_token_rejects_bad_credentials(client, username, password):
    response = client.post("/api/v1/token", data={"username": username, "password": password})
    assert response.status_code == 401


def test_token_is_a_valid_jwt(auth_headers):
    token = auth_headers["Authorization"].removeprefix("Bearer ")
    payload = jwt.decode(token, settings.auth_secret_key, algorithms=[settings.auth_algorithm])
    assert payload["sub"] == "tester"


def test_queries_require_a_token(client):
    assert client.post("/api/v1/padron", json={"personaIds": [1]}).status_code == 401
    bad = {"Authorization": "Bearer not-a-jwt"}
    assert client.post("/api/v1/padron", json={"personaIds": [1]}, headers=bad).status_code == 401


def test_expired_token_is_rejected(client):
    expired = jwt.encode(
        {"sub": "tester", "exp": dt.datetime.now(dt.UTC) - dt.timedelta(minutes=1)},
        settings.auth_secret_key,
        algorithm=settings.auth_algorithm,
    )
    response = client.post(
        "/api/v1/padron",
        json={"personaIds": [1]},
        headers={"Authorization": f"Bearer {expired}"},
    )
    assert response.status_code == 401


def test_query_without_afip_client_is_503(client, auth_headers):
    response = client.post("/api/v1/padron", json={"personaIds": [1]}, headers=auth_headers)
    assert response.status_code == 503
    assert response.json()["error"] == "service_unavailable"


def test_successful_query_returns_string_keys(client, auth_headers, fake_services):
    fake = FakeWSN(answers={20111111112: {"datosGenerales": {"idPersona": 20111111112}}})
    fake_services(**{INSCRIPTION: fake})

    response = client.post(
        "/api/v1/inscription",
        json={"personaIds": [20111111112, 20222222223]},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json() == {
        "data": [
            {"20111111112": {"datosGenerales": {"idPersona": 20111111112}}},
            {"20222222223": {"error": "not returned by AFIP"}},
        ]
    }
    assert fake.calls == [[20111111112, 20222222223]]


@pytest.mark.parametrize("ids", [[], list(range(1, 252)), ["abc"]])
def test_query_validates_ids(client, auth_headers, fake_services, ids):
    fake_services(**{PADRON: FakeWSN()})
    response = client.post("/api/v1/padron", json={"personaIds": ids}, headers=auth_headers)
    assert response.status_code == 422


@pytest.mark.parametrize(("dummy", "expected"), [(True, "UP"), (False, "DOWN")])
def test_service_health(client, auth_headers, fake_services, dummy, expected):
    fake_services(**{PADRON: FakeWSN(dummy=dummy)})
    response = client.get("/api/v1/padron/health", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["status"] == expected


def test_service_health_when_afip_fails_is_503(client, auth_headers, fake_services):
    fake_services(**{PADRON: FakeWSN(dummy=RuntimeError("AFIP down"))})
    response = client.get("/api/v1/padron/health", headers=auth_headers)
    assert response.status_code == 503
    assert response.json()["error"] == "afip_unavailable"


def test_cors_does_not_allow_other_origins_by_default(client):
    response = client.options(
        "/api/v1/token",
        headers={"Origin": "https://evil.example.com", "Access-Control-Request-Method": "POST"},
    )
    assert "access-control-allow-origin" not in response.headers
    assert "access-control-allow-credentials" not in response.headers


def test_dashboard_pages_render(client):
    assert client.get("/dashboard/login").status_code == 200
    assert client.get("/dashboard").status_code == 200
