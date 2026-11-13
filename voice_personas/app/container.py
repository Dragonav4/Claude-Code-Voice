"""Composition root: here (and in runner.py) app is wired to a concrete infra.

Use cases get dependencies only through App and never import infra."""

import contextlib
import os
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from ..domain import Settings
from ..infra.audio import Player
from ..infra.elevenlabs import ElevenLabs
from ..infra.environment import load_environment
from ..infra.music import ducked
from ..infra.paths import PLUGIN_ROOT, Paths
from ..infra.platform import MACOS, current_system
from ..infra.speech_queue import PrintQueue, ProcessQueue
from ..infra.storage import Log, Personas, Store
from ..infra.transcript import read_text_blocks


@dataclass(frozen=True)
class App:
    paths: Paths
    log: Log
    store: Store
    personas: Personas
    settings: Settings
    queue: Any  # ProcessQueue | PrintQueue
    synth: ElevenLabs
    player: Player
    ducked: Callable  # (enabled, level) -> context manager
    read_transcript: Callable  # (path) -> [TextBlock]


def _no_ducking(enabled, level):
    return contextlib.nullcontext()


def build_app(env=None, env_dir=PLUGIN_ROOT):
    """`env_dir` is where the plugin-level .env lives; tests point it at an empty folder."""
    loaded = load_environment(os.environ if env is None else env, env_dir)
    env = loaded.env
    system = current_system()
    paths = Paths.from_env(env)
    log = Log(paths.log_file)
    for warning in loaded.warnings:
        log.write(warning)
    store = Store(paths)
    settings = Settings.from_sources(store.load_config(), env)
    dry_run = bool(env.get("VOICE_PERSONAS_DRY_RUN"))
    return App(
        paths=paths,
        log=log,
        store=store,
        personas=Personas(paths),
        settings=settings,
        queue=PrintQueue() if dry_run else ProcessQueue(paths, log),
        synth=ElevenLabs(settings, paths.cache_dir, log),
        player=Player(settings, log, system),
        ducked=ducked if system == MACOS else _no_ducking,  # Music.app is macOS-only
        read_transcript=read_text_blocks,
    )
