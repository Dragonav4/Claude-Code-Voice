"""Speech queue: background workers that can be cut off.

Each worker runs in its own process group with the audio player inside it, so
stopping the group stops both the worker and the sound.
"""

import contextlib
import json
import os
import sys

from .platform.processes import command_line, spawn_detached, terminate_tree

WORKER_FLAG = "--voice-personas-worker"  # identifies our own worker in the process list


class ProcessQueue:
    def __init__(self, paths, log):
        self._paths = paths
        self._log = log

    def enqueue(self, persona, texts):
        """Starts a worker and returns at once: the hook never waits for audio."""
        payload = json.dumps({"persona": persona, "texts": list(texts)}).encode("utf-8")
        spawn_detached([sys.executable, str(self._paths.worker_script), WORKER_FLAG], payload)

    @contextlib.contextmanager
    def registered(self, pid):
        """While the block runs, the worker is visible to stop_all()."""
        self._paths.workers_dir.mkdir(parents=True, exist_ok=True)
        marker = self._paths.workers_dir / str(pid)
        marker.write_text(str(pid), encoding="utf-8")
        try:
            yield
        finally:
            with contextlib.suppress(OSError):
                marker.unlink()

    def stop_all(self):
        """Cuts off playing and queued lines. Returns how many were stopped."""
        directory = self._paths.workers_dir
        if not directory.is_dir():
            return 0
        stopped = 0
        for marker in directory.iterdir():
            pid = self._read_pid(marker)
            if pid and WORKER_FLAG in (command_line(pid) or ""):  # never a reused pid
                with contextlib.suppress(OSError):
                    terminate_tree(pid)
                    stopped += 1
            with contextlib.suppress(OSError):
                marker.unlink()
        return stopped

    @staticmethod
    def _read_pid(marker):
        try:
            pid = int(marker.read_text(encoding="utf-8").strip())
        except (OSError, ValueError):
            return None
        return pid if pid > 1 and pid != os.getpid() else None


class PrintQueue:
    """VOICE_PERSONAS_DRY_RUN mode: prints lines instead of synthesis and audio."""

    def enqueue(self, persona, texts):
        for text in texts:
            print(f"[dry-run:{persona}] {text}")

    @contextlib.contextmanager
    def registered(self, pid):
        yield

    def stop_all(self):
        return 0
