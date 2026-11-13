"""Detached background processes: start, find by command line, stop with children."""

import os
import signal
import subprocess

TOOL_TIMEOUT_S = 5
WINDOWS = os.name == "nt"

# Windows: a new process group with no console window. Breaking away from the job
# keeps the worker alive if the caller's job is closed when the hook exits.
CREATE_NEW_PROCESS_GROUP = 0x00000200
CREATE_NO_WINDOW = 0x08000000
CREATE_BREAKAWAY_FROM_JOB = 0x01000000

PS_COMMAND_LINE = "(Get-CimInstance Win32_Process -Filter ('ProcessId=' + $env:VP_PID)).CommandLine"


def _popen(argv, flags):
    options = {"creationflags": flags} if WINDOWS else {"start_new_session": True}
    return subprocess.Popen(
        argv,
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        **options,
    )


def spawn_detached(argv, payload):
    """Starts `argv` in its own process group and writes `payload` to its stdin."""
    flags = CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW
    try:
        process = _popen(argv, flags | CREATE_BREAKAWAY_FROM_JOB)
    except OSError:
        if not WINDOWS:
            raise
        process = _popen(argv, flags)  # the job does not allow breakaway
    process.stdin.write(payload)
    process.stdin.close()
    return process


def terminate_tree(pid):
    """Stops the process and everything it started (for example, the audio player)."""
    if WINDOWS:
        subprocess.run(
            ["taskkill", "/PID", str(pid), "/T", "/F"],
            capture_output=True,
            timeout=TOOL_TIMEOUT_S,
            check=False,
        )
    else:
        os.killpg(pid, signal.SIGTERM)  # the worker leads its group, the player is inside


def command_line(pid):
    """The command line of a running process, or None if it is not running."""
    if WINDOWS:
        argv = ["powershell", "-NoProfile", "-NonInteractive", "-Command", PS_COMMAND_LINE]
        env = {**os.environ, "VP_PID": str(int(pid))}
    else:
        argv, env = ["ps", "-o", "command=", "-p", str(int(pid))], None
    try:
        result = subprocess.run(
            argv, capture_output=True, text=True, env=env, timeout=TOOL_TIMEOUT_S, check=False
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    output = result.stdout.strip()
    return output or None
