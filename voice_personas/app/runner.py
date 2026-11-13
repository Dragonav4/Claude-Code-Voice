"""Обвязка точек входа: разбор stdin, сборка App, ошибки — в лог, не на экран.

Вместе с container.py это composition root: лог нужен, даже если App не собрался."""
import json
import os
import sys
import traceback

from ..infra.paths import Paths
from ..infra.storage import Log
from .container import build_app


def read_payload(stream):
    try:
        data = json.load(stream)
    except (ValueError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def log_crash(where):
    Log(Paths.from_env(os.environ).log_file).write(
        f"{where} failed:\n{traceback.format_exc()}")


def run_hook(handler):
    """Hook никогда не роняет Claude Code: всегда выходит с кодом 0."""
    try:
        output = handler(build_app(), read_payload(sys.stdin))
        if output:
            print(output)  # для UserPromptSubmit stdout попадает в контекст Claude
    except Exception:
        log_crash(handler.__name__)
    return 0
