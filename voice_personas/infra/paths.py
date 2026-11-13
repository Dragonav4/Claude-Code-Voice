"""Where plugin files live. Everything outside the plugin folder survives updates."""

from dataclasses import dataclass
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[2]


def default_home():
    """~/.claude/voice-personas, resolved lazily.

    Path.home() raises on Windows when USERPROFILE is missing, so never call it at import time.
    """
    return Path.home() / ".claude" / "voice-personas"


@dataclass(frozen=True)
class Paths:
    home: Path  # ~/.claude/voice-personas
    plugin_root: Path = PLUGIN_ROOT

    @classmethod
    def from_env(cls, env):
        home = env.get("VOICE_PERSONAS_HOME") or default_home()
        return cls(home=Path(home).expanduser())

    @property
    def state_file(self):
        return self.home / "state.json"

    @property
    def config_file(self):
        return self.home / "config.json"

    @property
    def log_file(self):
        return self.home / "speak.log"

    @property
    def builtin_personas(self):
        return self.plugin_root / "personas"

    @property
    def user_personas(self):
        return self.home / "personas"  # user personas override built-in ones

    @property
    def spoken_dir(self):
        return self.home / "spoken"  # which lines of a session were already spoken

    @property
    def cache_dir(self):
        return self.home / "cache"  # synthesized phrases

    @property
    def workers_dir(self):
        return self.home / "workers"  # pids of active speech workers

    @property
    def worker_script(self):
        return self.plugin_root / "bin" / "worker.py"

    def lock(self, name):
        return self.home / f"{name}.lock"
