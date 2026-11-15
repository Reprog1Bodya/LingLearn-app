import os
from pathlib import Path
from dotenv import load_dotenv

# Загружаем .env из папки server (переменные окружения процесса имеют приоритет)
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


def _flag(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).lower() in ("1", "true", "yes")


def _require_secret() -> str:
    """Секрет подписи JWT берётся ТОЛЬКО из окружения: значения по умолчанию в коде нет."""
    key = os.getenv("SECRET_KEY", "").strip()
    if len(key) < 32:
        raise RuntimeError(
            "SECRET_KEY не задан или короче 32 символов. Скопируйте server/.env.example в "
            "server/.env (или корневой .env.example в .env для Docker) и задайте SECRET_KEY. "
            "Сгенерировать: python -c \"import secrets; print(secrets.token_hex(32))\""
        )
    return key


class Settings:
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8080"))
    DEBUG: bool = _flag("DEBUG")

    # PostgreSQL — основная СУБД проекта (см. docker-compose.yml). SQLite допустим только
    # как явный выбор через DATABASE_URL (например, для быстрых локальных тестов).
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://linglearn:linglearn@localhost:5432/linglearn",
    )
    # Применять миграции Alembic при старте сервера (alembic upgrade head)
    AUTO_MIGRATE: bool = _flag("AUTO_MIGRATE", "true")

    # JWT Security
    SECRET_KEY: str = _require_secret()
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

    # Восстановление пароля
    RESET_CODE_TTL_MINUTES: int = int(os.getenv("RESET_CODE_TTL_MINUTES", "15"))
    # ТОЛЬКО для отладки: вернуть код восстановления в ответе API (в продакшене должно быть false)
    DEV_EXPOSE_RESET_CODE: bool = _flag("DEV_EXPOSE_RESET_CODE")

    # Initial data
    SEED_ON_STARTUP: bool = _flag("SEED_ON_STARTUP", "true")
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@linglearn.local").lower()
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "Administrator")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "admin123")

    # Запись адреса сервера в client/server.cfg при запуске через server.py (удобство разработки)
    WRITE_CLIENT_CONFIG: bool = _flag("WRITE_CLIENT_CONFIG", "true")


settings = Settings()
