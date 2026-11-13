"""Проигрывание звука: mp3 через afplay (или mpv/ffplay), текст через `say`."""
import re
import shutil
import subprocess

SAY_BASE_WPM = 175          # скорость `say` при rate = 1.0
PLAY_TIMEOUT_S = 120
LIST_TIMEOUT_S = 3
SAY_LINE_RE = re.compile(r"^(.+?)\s+[a-z]{2,3}_[A-Za-z0-9]+\s+#")  # "<имя>  <локаль>  # ..."
LANGUAGE_SUFFIX_RE = re.compile(r"\s*\(.*\)$")                     # " (Русский (Россия))"
OTHER_PLAYERS = (
    ["mpv", "--no-video", "--really-quiet"],
    ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet"],
)


def say_voice_names(listing):
    """Имена голосов из `say -v ?`. В русской macOS: "Milena (Русский (Россия)) ru_RU  # ..."."""
    names = set()
    for line in listing.splitlines():
        match = SAY_LINE_RE.match(line)
        if match:
            names.add(LANGUAGE_SUFFIX_RE.sub("", match.group(1)).strip())
    return names


class Player:
    def __init__(self, settings, log):
        self._settings = settings
        self._log = log

    def play_file(self, path):
        self._run(self.file_command(path))

    def say(self, text):
        self._run(self.say_command(text))

    def file_command(self, path):
        if shutil.which("afplay"):
            return ["afplay", "-r", f"{self._settings.rate:g}",
                    "-v", f"{self._settings.volume:g}", str(path)]
        for player in OTHER_PLAYERS:
            if shutil.which(player[0]):
                return [*player, str(path)]
        return None

    def say_command(self, text):
        if not shutil.which("say"):
            return None
        command = ["say", "-r", str(int(SAY_BASE_WPM * self._settings.rate))]
        voice = self._settings.fallback_voice
        if voice in self._installed_say_voices():
            command += ["-v", voice]
        return [*command, "--", text]  # "--": текст никогда не станет опцией

    def _installed_say_voices(self):
        try:
            listing = subprocess.run(["say", "-v", "?"], capture_output=True, text=True,
                                     timeout=LIST_TIMEOUT_S, check=False).stdout
        except (OSError, subprocess.TimeoutExpired):
            return set()
        return say_voice_names(listing)

    def _run(self, command):
        if command is None:
            self._log.write("no audio player found (expected afplay/say on macOS)")
            return
        try:
            subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           timeout=PLAY_TIMEOUT_S, check=False)
        except (OSError, subprocess.TimeoutExpired) as err:
            self._log.write(f"playback failed: {err}")
