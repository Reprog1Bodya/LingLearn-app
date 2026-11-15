import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Настраиваем окружение для тестов
os.environ["DATABASE_URL"] = "sqlite:///./test_suite.db"
os.environ["SECRET_KEY"] = "test_super_secret_key_32_bytes_test"
os.environ["SEED_ON_STARTUP"] = "false"
os.environ["ADMIN_PASSWORD"] = "admin123"  # не зависеть от локального .env
os.environ["AUTO_MIGRATE"] = "false"  # схему в тестах создаёт фикстура; миграции проверяет test_migrations.py

from server.main import app
from server.models.base import Base
from server.database.connection import get_db
from server.database.seed_data import seed_database
from server.services.auth_service import hash_password
from server.models.user import User

TEST_DB_URL = "sqlite:///./test_suite.db"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    # Создание схемы
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    # Базовое наполнение (seed)
    with TestingSessionLocal() as db:
        seed_database(db)

    yield

    # Очистка
    Base.metadata.drop_all(bind=test_engine)
    if os.path.exists("test_suite.db"):
        os.remove("test_suite.db")


@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def admin_token(client):
    r = client.post("/api/v1/login", json={"email": "admin@linglearn.local", "password": "admin123"})
    assert r.status_code == 200
    return r.json()["token"]


@pytest.fixture
def user_a(client):
    email = "user_a@test.com"
    r = client.post("/api/v1/register", json={
        "email": email,
        "username": "User A",
        "password": "password123",
        "password_confirm": "password123",
    })
    assert r.status_code in (201, 409)
    if r.status_code == 409:
        r = client.post("/api/v1/login", json={"email": email, "password": "password123"})
    data = r.json()
    return {"token": data["token"], "headers": {"Authorization": f"Bearer {data['token']}"}, "email": email}


@pytest.fixture
def user_b(client):
    email = "user_b@test.com"
    r = client.post("/api/v1/register", json={
        "email": email,
        "username": "User B",
        "password": "password123",
        "password_confirm": "password123",
    })
    assert r.status_code in (201, 409)
    if r.status_code == 409:
        r = client.post("/api/v1/login", json={"email": email, "password": "password123"})
    data = r.json()
    return {"token": data["token"], "headers": {"Authorization": f"Bearer {data['token']}"}, "email": email}
