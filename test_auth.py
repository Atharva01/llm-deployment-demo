import os

os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("AUTH_USER", "admin")
os.environ.setdefault("AUTH_PASSWORD", "test-pass")

from fastapi.testclient import TestClient

import auth_app

client = TestClient(auth_app.app)


def test_verify_rejects_missing_cookie():
    assert client.get("/verify").status_code == 401


def test_login_wrong_password_rejected():
    resp = client.post("/login", data={"username": "admin", "password": "nope"})
    assert resp.status_code == 401


def test_login_then_verify_succeeds():
    resp = client.post(
        "/login",
        data={"username": "admin", "password": "test-pass"},
        follow_redirects=False,
    )
    assert resp.status_code == 302
    cookie = resp.cookies.get("session")
    assert cookie
    verify_resp = client.get("/verify", cookies={"session": cookie})
    assert verify_resp.status_code == 200


if __name__ == "__main__":
    test_verify_rejects_missing_cookie()
    test_login_wrong_password_rejected()
    test_login_then_verify_succeeds()
    print("ok")
