"""Shared pytest fixtures: run the API in-process against a throwaway SQLite DB."""
import os
import sys
import tempfile
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Must be set before `app` is imported so the engine binds to the temp DB.
_tmp_dir = tempfile.mkdtemp(prefix="sentinel-crm-tests-")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp_dir}/test.db"
os.environ.setdefault("SECRET_KEY", "test-only-secret-key")


@pytest.fixture(scope="session")
def client():
    from fastapi.testclient import TestClient
    from app.main import app

    # Not using `with TestClient(app)` on purpose: that would fire the startup
    # hook and start the APScheduler background jobs during tests.
    return TestClient(app)


@pytest.fixture(scope="session")
def auth_headers(client):
    creds = {"email": "testimporter@example.com", "password": "testpassword123!"}
    client.post("/api/auth/register", json={**creds, "full_name": "Test Importer"})
    resp = client.post("/api/auth/login", json=creds)
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}
