"""Где лежат файлы плагина. Всё вне папки плагина переживает его обновления."""
from dataclasses import dataclass
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Paths:
    home: Path                 # ~/.claude/voice-personas
    plugin_root: Path = PLUGIN_ROOT

    @classmethod
    def from_env(cls, env):
        home = env.get("VOICE_PERSONAS_HOME") or Path.home() / ".claude" / "voice-personas"
        return cls(home=Path(home))

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
        return self.home / "personas"   # свои персоны перекрывают встроенные

    @property
    def spoken_dir(self):
        return self.home / "spoken"     # какие реплики сессии уже озвучены

    @property
    def cache_dir(self):
        return self.home / "cache"      # синтезированные фразы

    @property
    def workers_dir(self):
        return self.home / "workers"    # pid активных воркеров озвучки

    @property
    def worker_script(self):
        return self.plugin_root / "bin" / "worker.py"

    def lock(self, name):
        return self.home / f"{name}.lock"
