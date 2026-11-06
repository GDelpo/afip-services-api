import os
import tempfile

import pytest

# INTENTIONAL: settings and logging are read at import time, so the test
# environment has to exist before `app` is imported. All values are fake.
_logs = tempfile.mkdtemp(prefix="afip-api-logs-")
os.environ.update(
    AUTH_USERNAME="tester",
    AUTH_PASSWORD="test-password",
    AUTH_SECRET_KEY="x" * 64,
    CERTIFICATE_PATH="missing.crt",
    PRIVATE_KEY_PATH="missing.key",
    LOG_FORMAT="text",
    LOG_DIR_PATH=_logs,
    ENVIRONMENT="dev",
)
os.environ.pop("LOGTAIL_TOKEN", None)

from afip_services import WSNService  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


class FakeWSN:
    """Stands in for afip_services.WSN: returns canned data, never calls AFIP."""

    def __init__(self, answers=None, dummy=True):
        self.answers = answers or {}
        self.dummy = dummy
        self.calls = []

    def request_persona_list(self, persona_ids):
        self.calls.append(persona_ids)
        return [
            {pid: self.answers.get(pid, {"error": "not returned by AFIP"})} for pid in persona_ids
        ]

    def request_afip_dummy(self):
        if isinstance(self.dummy, Exception):
            raise self.dummy
        return self.dummy


@pytest.fixture
def client():
    # Startup tries to build real AFIP clients; with fake cert paths it ends with none.
    with TestClient(app) as test_client:
        yield test_client
        app.state.wsn_clients = {}


@pytest.fixture
def auth_headers(client):
    response = client.post(
        "/api/v1/token", data={"username": "tester", "password": "test-password"}
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['accessToken']}"}


@pytest.fixture
def fake_services(client):
    def install(**by_service):
        app.state.wsn_clients = {WSNService[name]: fake for name, fake in by_service.items()}

    return install
