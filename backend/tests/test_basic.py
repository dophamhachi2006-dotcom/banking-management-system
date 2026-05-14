import os, sys, pytest
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from backend.app import create_app

@pytest.fixture
def app(): return create_app()

@pytest.fixture
def client(app): return app.test_client()

def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.get_json()["success"] is True

def test_login_missing(client):
    r = client.post("/api/auth/login", json={})
    assert r.status_code == 400

def test_protected_no_token(client):
    r = client.get("/api/customers")
    assert r.status_code == 401
