"""Commands that play an audio file on each operating system."""

import shutil
from types import MappingProxyType

from . import LINUX, MACOS, WINDOWS, Command

PERCENT = 100
WAV_ONLY_PLAYERS = ("paplay", "aplay")  # cannot decode mp3 reliably

# Windows has no CLI player out of the box. The file path comes in through the
# environment, so no path or text is ever spliced into the script.
WINDOWS_PLAYER = (
    "Add-Type -AssemblyName PresentationCore;"
    "$p = New-Object System.Windows.Media.MediaPlayer;"
    "$p.Volume = [double]$env:VP_VOLUME;"
    "$p.SpeedRatio = [double]$env:VP_RATE;"
    "$p.Open([Uri]$env:VP_FILE);"
    "$deadline = (Get-Date).AddSeconds(5);"
    "while (-not $p.NaturalDuration.HasTimeSpan -and (Get-Date) -lt $deadline)"
    " { Start-Sleep -Milliseconds 50 };"
    "$p.Play();"
    "if ($p.NaturalDuration.HasTimeSpan) { Start-Sleep -Milliseconds"
    " ([int]($p.NaturalDuration.TimeSpan.TotalMilliseconds / $p.SpeedRatio) + 200) };"
    "$p.Close()"
)


def _mpv(path, rate, volume):
    return (
        "mpv",
        "--no-video",
        "--really-quiet",
        f"--speed={rate:g}",
        f"--volume={round(volume * PERCENT)}",
        str(path),
    )


def _ffplay(path, rate, volume):
    return (
        "ffplay",
        "-nodisp",
        "-autoexit",
        "-loglevel",
        "quiet",
        "-volume",
        str(round(volume * PERCENT)),
        "-af",
        f"atempo={rate:g}",
        str(path),
    )


def _first_cross_platform(path, rate, volume, which):
    if which("mpv"):
        return Command(_mpv(path, rate, volume))
    if which("ffplay"):
        return Command(_ffplay(path, rate, volume))
    return None


def file_command(system, path, rate, volume, which=shutil.which):
    """A Command that plays `path`, or None when no suitable player is installed."""
    if system == MACOS and which("afplay"):
        return Command(("afplay", "-r", f"{rate:g}", "-v", f"{volume:g}", str(path)))
    found = _first_cross_platform(path, rate, volume, which)
    if found:
        return found
    if system == LINUX and path.suffix == ".wav":
        player = next((name for name in WAV_ONLY_PLAYERS if which(name)), None)
        return Command((player, str(path))) if player else None
    if system == WINDOWS:
        env = {"VP_FILE": str(path), "VP_RATE": f"{rate:g}", "VP_VOLUME": f"{volume:g}"}
        argv = ("powershell", "-NoProfile", "-NonInteractive", "-Command", WINDOWS_PLAYER)
        return Command(argv, env=MappingProxyType(env))
    return None
