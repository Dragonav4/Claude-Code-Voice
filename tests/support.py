"""Shared test helpers: package path and an isolated app in a temporary folder."""

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from voice_personas.app.container import build_app  # noqa: E402


class TempHomeTest(unittest.TestCase):
    """Every test gets its own empty ~/.claude/voice-personas."""

    def setUp(self):
        self.home = Path(tempfile.mkdtemp(prefix="voice-personas-test-"))
        self.addCleanup(shutil.rmtree, self.home, True)

    def env(self, **extra):
        return {"VOICE_PERSONAS_HOME": str(self.home), "VOICE_PERSONAS_DRY_RUN": "1", **extra}

    def write_config(self, config):
        (self.home / "config.json").write_text(json.dumps(config), encoding="utf-8")

    def app(self, **extra_env):
        # An empty .env folder: tests must never pick up a developer's real .env.
        return build_app(self.env(**extra_env), env_dir=self.home / "no-dotenv")


def assistant(text):
    return {
        "type": "assistant",
        "message": {"role": "assistant", "content": [{"type": "text", "text": text}]},
    }


def write_transcript(path, records):
    with open(path, "w", encoding="utf-8") as f:
        for record in records:
            f.write((record if isinstance(record, str) else json.dumps(record)) + "\n")
    return path
