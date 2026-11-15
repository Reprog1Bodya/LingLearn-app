"""Кейс 6: восстановление пароля не должно раскрывать код и не должно позволять перебор email."""
from datetime import datetime, timedelta

from sqlalchemy import select

from server.models.user import User

RECOVER = "/api/v1/recover"
CONFIRM = "/api/v1/recover/confirm"


def _register(client, email):
    """Отдельные пользователи для этих тестов: смена пароля не должна ломать фикстуры user_a / user_b."""
    r = client.post("/api/v1/register", json={
        "email": email, "username": "Recover User",
        "password": "password123", "password_confirm": "password123",
    })
    assert r.status_code in (201, 409)
    return email


def _user(db, email):
    db.expire_all()
    return db.execute(select(User).where(User.email == email)).scalar_one()


def test_recover_does_not_leak_code(client):
    email = _register(client, "rec_leak@test.com")
    r = client.post(RECOVER, json={"email": email})
    assert r.status_code == 200
    assert not r.json().get("demo_code")


def test_recover_unknown_email_looks_the_same(client):
    email = _register(client, "rec_same@test.com")
    known = client.post(RECOVER, json={"email": email})
    unknown = client.post(RECOVER, json={"email": "nobody@test.com"})
    assert unknown.status_code == known.status_code == 200
    assert unknown.json() == known.json()


def test_recover_confirm_with_valid_code_changes_password(client, db_session):
    email = _register(client, "rec_ok@test.com")
    client.post(RECOVER, json={"email": email})
    code = _user(db_session, email).reset_code
    assert code
    r = client.post(CONFIRM, json={"email": email, "code": code, "password": "new-password-1"})
    assert r.status_code == 200
    ok = client.post("/api/v1/login", json={"email": email, "password": "new-password-1"})
    assert ok.status_code == 200
    # код одноразовый
    again = client.post(CONFIRM, json={"email": email, "code": code, "password": "new-password-2"})
    assert again.status_code == 400


def test_recover_confirm_rejects_expired_code(client, db_session):
    email = _register(client, "rec_exp@test.com")
    client.post(RECOVER, json={"email": email})
    u = _user(db_session, email)
    code = u.reset_code
    u.reset_code_expires_at = datetime.utcnow() - timedelta(minutes=1)
    db_session.commit()
    r = client.post(CONFIRM, json={"email": email, "code": code, "password": "new-password-3"})
    assert r.status_code == 400
