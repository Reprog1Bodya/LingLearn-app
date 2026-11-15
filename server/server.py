#!/usr/bin/env python3
"""Единая точка запуска LingLearn.

    python server/server.py          (из корня проекта)
    python server.py                 (из папки server)

Что делает: применяет миграции (через lifespan в main.py), запускает API, печатает адрес
в локальной сети и записывает его в client/server.cfg — клиент Godot «вшивает» этот адрес
в APK при экспорте, поэтому вводить IP на телефоне не нужно.
"""
import socket
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import uvicorn  # noqa: E402

from server.database.config import settings  # noqa: E402


def lan_ip() -> str:
    """IP компьютера в локальной сети (пакеты при этом не отправляются)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


def write_client_config(url: str) -> None:
    cfg = root_dir / "client" / "server.cfg"
    if cfg.parent.exists():
        cfg.write_text(f'[server]\nurl="{url}"\n', encoding="utf-8")


if __name__ == "__main__":
    url = f"http://{lan_ip()}:{settings.PORT}"
    print(f"\n  LingLearn API: {url}   (документация: {url}/docs)\n")
    if settings.WRITE_CLIENT_CONFIG:
        write_client_config(url)
        print("  Адрес записан в client/server.cfg — теперь можно экспортировать APK.\n")
    uvicorn.run(
        "server.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
