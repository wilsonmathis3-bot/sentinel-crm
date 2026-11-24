"""Auth basics: token round-trip, bad tokens rejected, protected routes gated."""
from datetime import timedelta

from app.auth import create_access_token, get_password_hash, verify_password


def test_password_hash_roundtrip_including_long_passwords():
    hashed = get_password_hash("correct horse battery staple")
    assert verify_password("correct horse battery staple", hashed)
    assert not verify_password("wrong password!!", hashed)

    long_pw = "x" * 100  # > 72 bytes, bcrypt's limit
    assert verify_password(long_pw, get_password_hash(long_pw))


def test_protected_route_requires_token(client):
    assert client.get("/api/contacts/").status_code == 401


def test_protected_route_rejects_garbage_and_expired_tokens(client):
    bad = {"Authorization": "Bearer not-a-real-token"}
    assert client.get("/api/contacts/", headers=bad).status_code == 401

    expired = create_access_token({"sub": "testimporter@example.com"}, expires_delta=timedelta(minutes=-5))
    resp = client.get("/api/contacts/", headers={"Authorization": f"Bearer {expired}"})
    assert resp.status_code == 401


def test_valid_token_is_accepted(client, auth_headers):
    resp = client.get("/api/contacts/", headers=auth_headers)
    assert resp.status_code == 200, resp.text


def test_health(client):
    assert client.get("/health").json() == {"status": "healthy"}
