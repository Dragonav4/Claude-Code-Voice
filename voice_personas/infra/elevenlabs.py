"""Синтез речи через ElevenLabs с кэшем готовых фраз на диске."""
import hashlib
import json
import os
import urllib.error
import urllib.parse
import urllib.request

API_URL = "https://api.elevenlabs.io/v1/text-to-speech/"
OUTPUT_FORMAT = "mp3_44100_128"
TIMEOUT_S = 30
ERROR_BODY_CHARS = 300


class ElevenLabs:
    def __init__(self, settings, cache_dir, log):
        self._settings = settings
        self._cache_dir = cache_dir
        self._log = log

    def audio_file(self, text, voice_id):
        """mp3 с репликой (из кэша или свежий) или None."""
        if not self._settings.api_key or not voice_id:
            self._log.write("ElevenLabs skipped: " + ("no api key" if not self._settings.api_key
                                                      else "no voice_id"))
            return None
        path = self._cache_path(text, voice_id)
        if path.exists():
            os.utime(path)  # недавно использованное дольше живёт в кэше
            return path
        audio = self.request(text, voice_id)
        return self._store(path, audio) if audio else None

    def request(self, text, voice_id):
        url = (API_URL + urllib.parse.quote(voice_id, safe="")
               + f"?output_format={OUTPUT_FORMAT}")
        request = urllib.request.Request(
            url,
            data=json.dumps({"text": text, "model_id": self._settings.model_id}).encode("utf-8"),
            method="POST",
            headers={"xi-api-key": self._settings.api_key, "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT_S) as response:
                return response.read()
        except urllib.error.HTTPError as err:
            body = err.read(ERROR_BODY_CHARS).decode("utf-8", "replace")
            self._log.write(f"ElevenLabs HTTP {err.code}: {body}")
        except (urllib.error.URLError, OSError) as err:
            self._log.write(f"ElevenLabs request failed: {err}")
        return None

    def _cache_path(self, text, voice_id):
        key = f"{voice_id}\n{self._settings.model_id}\n{text}".encode("utf-8")
        return self._cache_dir / f"{hashlib.sha256(key).hexdigest()[:32]}.mp3"

    def _store(self, path, audio):
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_suffix(".tmp")
            tmp.write_bytes(audio)
            os.replace(tmp, path)
        except OSError as err:
            self._log.write(f"cache write failed: {err}")
            return None
        self.prune_cache()
        return path

    def prune_cache(self):
        """Удаляет самые старые фразы, пока кэш не влезет в лимит."""
        try:
            files = sorted(self._cache_dir.glob("*.mp3"), key=lambda p: p.stat().st_mtime)
            total = sum(p.stat().st_size for p in files)
            limit = self._settings.cache_mb * 1024 * 1024
            for path in files:
                if total <= limit:
                    break
                total -= path.stat().st_size
                path.unlink()
        except OSError as err:
            self._log.write(f"cache prune failed: {err}")
