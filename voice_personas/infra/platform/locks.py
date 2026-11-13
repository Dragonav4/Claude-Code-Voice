"""Inter-process file lock: fcntl on macOS/Linux, msvcrt on Windows."""

import contextlib
import os
import time

POLL_S = 0.05
DEFAULT_TIMEOUT_S = 600  # a worker may wait while several long lines play


def _try_lock(handle):
    if os.name == "nt":
        import msvcrt

        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
    else:
        import fcntl

        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)


def _unlock(handle):
    if os.name == "nt":
        import msvcrt

        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
    else:
        import fcntl

        fcntl.flock(handle, fcntl.LOCK_UN)


@contextlib.contextmanager
def exclusive_lock(path, timeout_s=DEFAULT_TIMEOUT_S):
    """Holds an exclusive lock on `path` for the block. Raises TimeoutError."""
    path.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + timeout_s
    with open(path, "a+") as handle:
        while True:
            try:
                _try_lock(handle)
                break
            except OSError:
                if time.monotonic() >= deadline:
                    raise TimeoutError(f"lock {path} is busy") from None
                time.sleep(POLL_S)
        try:
            yield
        finally:
            with contextlib.suppress(OSError):
                _unlock(handle)
