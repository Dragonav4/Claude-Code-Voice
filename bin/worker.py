#!/usr/bin/env python3
"""Background speech worker. Started by the queue, reads its job from stdin."""

import signal
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from voice_personas.app.container import build_app  # noqa: E402
from voice_personas.app.runner import log_crash, read_payload, use_utf8_stdio  # noqa: E402
from voice_personas.app.speak import speak_job  # noqa: E402


def stop_gracefully(signum, frame):
    raise SystemExit(0)  # lets finally blocks restore Music volume and unregister


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, stop_gracefully)
    try:
        use_utf8_stdio()
        speak_job(build_app(), read_payload(sys.stdin))
    except Exception:
        log_crash("worker")
    sys.exit(0)
