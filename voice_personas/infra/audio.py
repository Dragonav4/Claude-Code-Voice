"""Audio playback: an audio file or the system voice, on the current OS."""

import os
import shutil
import subprocess

from .platform import MACOS, players, voices

PLAY_TIMEOUT_S = 120
LIST_TIMEOUT_S = 3


class Player:
    def __init__(self, settings, log, system):
        self._settings = settings
        self._log = log
        self._system = system

    def play_file(self, path):
        command = players.file_command(
            self._system, path, self._settings.rate, self._settings.volume
        )
        self._run(command, f"no audio player for {path.suffix} files on {self._system}")

    def say(self, text):
        listing = self._say_listing() if self._system == MACOS else ""
        command = voices.say_command(
            self._system,
            text,
            self._settings.fallback_voice,
            self._settings.rate,
            shutil.which,
            listing,
        )
        self._run(command, f"no system voice on {self._system}")

    @staticmethod
    def _say_listing():
        try:
            return subprocess.run(
                ["say", "-v", "?"],
                capture_output=True,
                text=True,
                timeout=LIST_TIMEOUT_S,
                check=False,
            ).stdout
        except (OSError, subprocess.TimeoutExpired):
            return ""

    def _run(self, command, missing_message):
        if command is None:
            self._log.write(missing_message)
            return
        try:
            subprocess.run(
                command.argv,
                input=command.stdin.encode("utf-8") if command.stdin is not None else None,
                env={**os.environ, **command.env},
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=PLAY_TIMEOUT_S,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as err:
            self._log.write(f"playback failed: {err}")
