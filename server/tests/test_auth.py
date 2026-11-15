def test_register_success(client):
    r = client.post("/api/v1/register", json={
        "email": "newstudent@test.com",
        "username": "New Student",
        "password": "strongpassword123",
        "password_confirm": "strongpassword123",
    })
    assert r.status_code == 201
    data = r.json()
    assert "token" in data
    assert data["token_type"] == "Bearer"
    assert data["profile"]["email"] == "newstudent@test.com"
    assert data["profile"]["username"] == "New Student"
    # Безопасность: хеш пароля не должен присутствовать в ответе
    assert "password_hash" not in data["profile"]
    assert "password" not in data["profile"]


def test_register_duplicate_email(client):
    payload = {
        "email": "dup@test.com",
        "username": "Dup User",
        "password": "password123",
        "password_confirm": "password123",
    }
    r1 = client.post("/api/v1/register", json=payload)
    assert r1.status_code == 201

    r2 = client.post("/api/v1/register", json=payload)
    assert r2.status_code == 409
    assert "уже существует" in r2.json()["detail"]


def test_register_validation_errors(client):
    # Короткий пароль (< 6 символов)
    r1 = client.post("/api/v1/register", json={
        "email": "valid@test.com",
        "username": "Valid User",
        "password": "123",
        "password_confirm": "123",
    })
    assert r1.status_code == 422

    # Некорректный email
    r2 = client.post("/api/v1/register", json={
        "email": "not-an-email",
        "username": "Valid User",
        "password": "password123",
        "password_confirm": "password123",
    })
    assert r2.status_code == 422

    # Пароли не совпадают
    r3 = client.post("/api/v1/register", json={
        "email": "mismatch@test.com",
        "username": "Mismatch User",
        "password": "password123",
        "password_confirm": "differentpassword",
    })
    assert r3.status_code == 422


def test_login_success(client):
    r = client.post("/api/v1/login", json={
        "email": "admin@linglearn.local",
        "password": "admin123",
    })
    assert r.status_code == 200
    data = r.json()
    assert "token" in data
    assert data["profile"]["role"] == "admin"


def test_login_wrong_password(client):
    r = client.post("/api/v1/login", json={
        "email": "admin@linglearn.local",
        "password": "wrong_password_here",
    })
    assert r.status_code == 401
    assert "Неверный email или пароль" in r.json()["detail"]


def test_logout_revokes_token(client):
    # Логинимся
    login_res = client.post("/api/v1/login", json={
        "email": "admin@linglearn.local",
        "password": "admin123",
    })
    token = login_res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Проверяем, что токен работает
    r_check1 = client.get("/api/v1/profile", headers=headers)
    assert r_check1.status_code == 200

    # Выходим
    r_logout = client.post("/api/v1/logout", headers=headers)
    assert r_logout.status_code == 200

    # Проверяем, что отозванный токен больше не принимается (401)
    r_check2 = client.get("/api/v1/profile", headers=headers)
    assert r_check2.status_code == 401
