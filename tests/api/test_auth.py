"""
API integration tests for real credential authentication (register, login, /me).
"""

import uuid
from backend.app.db.session import SessionLocal
from backend.app.db.models import User


def test_register_login_and_me_flow(client):
    unique_email = f"test_{uuid.uuid4().hex[:8]}@cinemetrics-test.ai"
    password = "SecurePass!2026"

    try:
        # 1. Register new account
        reg_res = client.post(
            "/api/v1/auth/register",
            json={"name": "Naitik Analyst", "email": unique_email, "password": password},
        )
        assert reg_res.status_code == 201
        reg_data = reg_res.json()
        assert reg_data["token"]
        assert reg_data["user"]["email"] == unique_email.lower()
        assert reg_data["user"]["avatarInitials"] == "NA"

        # 2. Duplicate registration rejected
        dup_res = client.post(
            "/api/v1/auth/register",
            json={"name": "Duplicate", "email": unique_email, "password": password},
        )
        assert dup_res.status_code == 409

        # 3. Wrong password rejected
        bad_login = client.post(
            "/api/v1/auth/login",
            json={"email": unique_email, "password": "wrong-password"},
        )
        assert bad_login.status_code == 401

        # 4. Valid login succeeds
        ok_login = client.post(
            "/api/v1/auth/login",
            json={"email": unique_email, "password": password},
        )
        assert ok_login.status_code == 200
        token = ok_login.json()["token"]

        # 5. /me validates token and rejects missing/tampered token
        me_ok = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me_ok.status_code == 200
        assert me_ok.json()["email"] == unique_email.lower()

        me_bad = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid.token"})
        assert me_bad.status_code == 401
    finally:
        db = SessionLocal()
        try:
            db.query(User).filter(User.email == unique_email.lower()).delete()
            db.commit()
        finally:
            db.close()

