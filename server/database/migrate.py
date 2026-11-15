"""Программное применение миграций Alembic (эквивалент `alembic upgrade head`)."""
import logging
from pathlib import Path

from alembic import command
from alembic.config import Config

logger = logging.getLogger("linglearn")

SERVER_DIR = Path(__file__).resolve().parent.parent


def upgrade_head() -> None:
    cfg = Config(str(SERVER_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(SERVER_DIR / "alembic"))
    logger.info("Применение миграций Alembic (upgrade head)...")
    command.upgrade(cfg, "head")
