"""Commands that speak text with the operating system's own voice."""

import re
import shutil
from types import MappingProxyType

from ...domain import detect_language
from . import LINUX, MACOS, WINDOWS, Command

BASE_WPM = 175  # words per minute at rate = 1.0
WINDOWS_RATE_STEP = 10  # SpeechSynthesizer.Rate is -10..10 around the normal speed
SAY_LINE_RE = re.compile(r"^(.+?)\s+([a-z]{2,3}_[A-Za-z0-9]+)\s+#")  # name, locale, sample
LANGUAGE_SUFFIX_RE = re.compile(r"\s*\(.*\)$")  # localized suffix, e.g. " (Russian (Russia))"
ESPEAK = ("espeak-ng", "espeak")

# The text is read from stdin and the voice from the environment: nothing the
# model wrote is ever spliced into the script.
WINDOWS_SPEAKER = (
    "[Console]::InputEncoding = [Text.Encoding]::UTF8;"
    "Add-Type -AssemblyName System.Speech;"
    "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer;"
    "$s.Rate = [int]$env:VP_RATE;"
    "$all = $s.GetInstalledVoices() | Where-Object Enabled | ForEach-Object VoiceInfo;"
    "$pick = if ($env:VP_VOICE) { $all | Where-Object Name -eq $env:VP_VOICE }"
    " elseif ($env:VP_LANG) { $all | Where-Object { $_.Culture.TwoLetterISOLanguageName"
    " -eq $env:VP_LANG } };"
    "if ($pick) { $s.SelectVoice(@($pick)[0].Name) };"
    "$s.Speak([Console]::In.ReadToEnd())"
)


def parse_say_listing(listing):
    """{voice name: locale} from `say -v ?`, e.g. "Milena (<language>) ru_RU  # ..."."""
    voices = {}
    for line in listing.splitlines():
        match = SAY_LINE_RE.match(line)
        if match:
            voices[LANGUAGE_SUFFIX_RE.sub("", match.group(1)).strip()] = match.group(2)
    return voices


def _macos_voice(voice, language, listing):
    installed = parse_say_listing(listing)
    if voice in installed:
        return voice
    if language:
        return next(
            (name for name, locale in installed.items() if locale.startswith(f"{language}_")), None
        )
    return None


def say_command(system, text, voice, rate, which=shutil.which, say_listing=""):
    """A Command that speaks `text`, or None when no system voice is available.

    `voice` is the user's explicit choice; otherwise a voice matching the text's
    language is picked when one is installed.
    """
    language = detect_language(text)
    wpm = str(int(BASE_WPM * rate))
    if system == MACOS:
        if not which("say"):
            return None
        chosen = _macos_voice(voice, language, say_listing)
        options = ("-v", chosen) if chosen else ()
        return Command(("say", "-r", wpm, *options, "--", text))  # "--": text is never an option
    if system == LINUX:
        tool = next((name for name in ESPEAK if which(name)), None)
        if not tool:
            return None
        chosen = voice or language
        options = ("-v", chosen) if chosen else ()
        return Command((tool, *options, "-s", wpm, "--stdin"), stdin=text)
    if system == WINDOWS:
        env = {
            "VP_RATE": str(round((rate - 1) * WINDOWS_RATE_STEP)),
            "VP_VOICE": voice or "",
            "VP_LANG": language or "",
        }
        argv = ("powershell", "-NoProfile", "-NonInteractive", "-Command", WINDOWS_SPEAKER)
        return Command(argv, stdin=text, env=MappingProxyType(env))
    return None
