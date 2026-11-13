"""Composition root: here (and in runner.py) app is wired to a concrete infra.

Use cases get dependencies only through App and never import infra."""

import os
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from ..domain import Settings
from ..infra.audio import Player
from ..infra.elevenlabs import ElevenLabs
from ..infra.music import ducked
from ..infra.paths import Paths
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


def build_app(env=None):
    env = os.environ if env is None else env
    paths = Paths.from_env(env)
    log = Log(paths.log_file)
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
        player=Player(settings, log),
        ducked=ducked,
        read_transcript=read_text_blocks,
    )
