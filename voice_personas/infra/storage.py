"""Files on disk: log, state, config, spoken lines, personas."""

import json
import os
import re
import time

from ..domain import Persona, State
from .platform.locks import exclusive_lock

LOG_MAX_BYTES = 200_000
LOG_KEEP_LINES = 500


def _read_json(path):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _write_json(path, data):
    """Atomic write: a reader never sees half a file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


class Log:
    """Narration error log. Never raises."""

    def __init__(self, path):
        self._path = path

    def write(self, message):
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._path, "a", encoding="utf-8") as f:
                f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + message + "\n")
            if self._path.stat().st_size > LOG_MAX_BYTES:
                tail = self._path.read_text(encoding="utf-8").splitlines()[-LOG_KEEP_LINES:]
                self._path.write_text("\n".join(tail) + "\n", encoding="utf-8")
        except OSError:
            pass


class Store:
    def __init__(self, paths):
        self._paths = paths

    def load_state(self):
        return State.from_dict(_read_json(self._paths.state_file))

    def save_state(self, state):
        _write_json(self._paths.state_file, state.to_dict())

    def load_config(self):
        return _read_json(self._paths.config_file)

    @staticmethod
    def _session_name(session):
        return re.sub(r"[^A-Za-z0-9_-]", "_", session)[:80] or "unknown"

    def _spoken_file(self, session):
        return self._paths.spoken_dir / f"{self._session_name(session)}.json"

    def _context_file(self, session):
        return self._paths.home / "sessions" / f"{self._session_name(session)}.json"

    def load_context_mark(self, session):
        """Fingerprint of the persona text this session has already received."""
        mark = _read_json(self._context_file(session)).get("persona")
        return mark if isinstance(mark, str) else None

    def save_context_mark(self, session, mark):
        _write_json(self._context_file(session), {"persona": mark})

    def clear_context_mark(self, session):
        try:
            self._context_file(session).unlink()
        except OSError:
            pass

    def load_seen(self, session):
        keys = _read_json(self._spoken_file(session)).get("keys", [])
        return tuple(key for key in keys if isinstance(key, str)) if isinstance(keys, list) else ()

    def save_seen(self, session, keys):
        _write_json(self._spoken_file(session), {"keys": list(keys)})

    def lock(self, name):
        """Inter-process lock: hooks and workers run in parallel."""
        return exclusive_lock(self._paths.lock(name))


class Personas:
    """Built-in personas plus the user's own from ~/.claude/voice-personas/personas."""

    def __init__(self, paths):
        self._dirs = (paths.builtin_personas, paths.user_personas)

    def all(self):
        found = {}
        for directory in self._dirs:
            if directory.is_dir():
                for path in sorted(directory.glob("*.md")):
                    found[path.stem] = path
        return {
            name: Persona.parse(name, path.read_text(encoding="utf-8"))
            for name, path in found.items()
        }

    def get(self, name):
        return self.all().get(name) if name else None
