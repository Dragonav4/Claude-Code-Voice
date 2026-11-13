"""Очередь озвучки: фоновые воркеры, которые можно оборвать.

Каждый воркер — лидер своей группы процессов (плеер внутри неё), поэтому
один killpg останавливает и воркера, и звук.
"""
import contextlib
import json
import os
import signal
import subprocess
import sys

WORKER_FLAG = "--voice-personas-worker"  # по нему узнаём своего воркера в `ps`
PS_TIMEOUT_S = 3


class ProcessQueue:
    def __init__(self, paths, log):
        self._paths = paths
        self._log = log

    def enqueue(self, persona, texts):
        """Запускает воркера и сразу возвращается: хук не ждёт звука."""
        process = subprocess.Popen(
            [sys.executable, str(self._paths.worker_script), WORKER_FLAG],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        process.stdin.write(json.dumps({"persona": persona, "texts": list(texts)}).encode("utf-8"))
        process.stdin.close()

    @contextlib.contextmanager
    def registered(self, pid):
        """Пока блок выполняется, воркер виден для stop_all()."""
        self._paths.workers_dir.mkdir(parents=True, exist_ok=True)
        marker = self._paths.workers_dir / str(pid)
        marker.write_text(str(pid), encoding="utf-8")
        try:
            yield
        finally:
            with contextlib.suppress(OSError):
                marker.unlink()

    def stop_all(self):
        """Обрывает звучащие и ожидающие реплики. Возвращает число остановленных."""
        directory = self._paths.workers_dir
        if not directory.is_dir():
            return 0
        stopped = 0
        for marker in directory.iterdir():
            pid = self._read_pid(marker)
            if pid and self._is_our_worker(pid):
                with contextlib.suppress(OSError):
                    os.killpg(pid, signal.SIGTERM)
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
        return pid if pid > 1 and pid != os.getpgrp() else None

    @staticmethod
    def _is_our_worker(pid):
        """Защита от переиспользованных pid: убиваем только свой процесс."""
        try:
            command = subprocess.run(["ps", "-o", "command=", "-p", str(pid)],
                                     capture_output=True, text=True,
                                     timeout=PS_TIMEOUT_S, check=False).stdout
        except (OSError, subprocess.TimeoutExpired):
            return False
        return WORKER_FLAG in command


class PrintQueue:
    """Режим VOICE_PERSONAS_DRY_RUN: печатает реплики вместо синтеза и звука."""

    def enqueue(self, persona, texts):
        for text in texts:
            print(f"[dry-run:{persona}] {text}")

    @contextlib.contextmanager
    def registered(self, pid):
        yield

    def stop_all(self):
        return 0
