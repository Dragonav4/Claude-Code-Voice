#!/usr/bin/env python3
"""Фоновый воркер озвучки. Запускается очередью, задание читает из stdin."""
import signal
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from voice_personas.app.container import build_app  # noqa: E402
from voice_personas.app.runner import log_crash, read_payload  # noqa: E402
from voice_personas.app.speak import speak_job  # noqa: E402


def stop_gracefully(signum, frame):
    raise SystemExit(0)  # finally-блоки вернут громкость Music и снимут регистрацию


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, stop_gracefully)
    try:
        speak_job(build_app(), read_payload(sys.stdin))
    except Exception:
        log_crash("worker")
    sys.exit(0)
