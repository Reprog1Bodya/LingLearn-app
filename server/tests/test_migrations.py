"""Кейс 3: схема разворачивается на ПУСТОЙ базе только миграциями Alembic (без create_all)."""
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from server.database.config import settings
from server.database.migrate import SERVER_DIR

EXPECTED_TABLES = {
    "users", "languages", "language_features", "dictionaries", "words",
    "user_dictionaries", "user_word_progress", "test_results", "revoked_tokens",
}


def _cfg():
    cfg = Config(str(SERVER_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(SERVER_DIR / "alembic"))
    return cfg


def test_upgrade_head_on_empty_database(tmp_path, monkeypatch):
    url = f"sqlite:///{tmp_path / 'empty.db'}"
    monkeypatch.setattr(settings, "DATABASE_URL", url)
    command.upgrade(_cfg(), "head")

    insp = inspect(create_engine(url))
    tables = set(insp.get_table_names())
    assert EXPECTED_TABLES <= tables
    assert "alembic_version" in tables
    # последняя миграция действительно применена
    assert "reset_code_expires_at" in {c["name"] for c in insp.get_columns("users")}
    assert "notes" in {c["name"] for c in insp.get_columns("user_word_progress")}


def test_downgrade_then_upgrade(tmp_path, monkeypatch):
    url = f"sqlite:///{tmp_path / 'cycle.db'}"
    monkeypatch.setattr(settings, "DATABASE_URL", url)
    cfg = _cfg()
    command.upgrade(cfg, "head")
    command.downgrade(cfg, "-1")
    assert "reset_code_expires_at" not in {c["name"] for c in inspect(create_engine(url)).get_columns("users")}
    command.upgrade(cfg, "head")
    assert "reset_code_expires_at" in {c["name"] for c in inspect(create_engine(url)).get_columns("users")}
