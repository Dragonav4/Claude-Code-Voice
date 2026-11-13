import os
import subprocess
import sys
import time
import unittest
from types import MappingProxyType
from unittest import mock

import support
from voice_personas.domain import Settings, State
from voice_personas.infra import audio, music
from voice_personas.infra.elevenlabs import ElevenLabs
from voice_personas.infra.paths import Paths
from voice_personas.infra.platform import LINUX, Command
from voice_personas.infra.speech_queue import WORKER_FLAG, ProcessQueue
from voice_personas.infra.storage import Log, Personas, Store
from voice_personas.infra.transcript import read_text_blocks

SLEEPER = "import time; time.sleep(30)"


class StoreTest(support.TempHomeTest):
    def setUp(self):
        super().setUp()
        self.store = Store(Paths(self.home))

    def test_state_roundtrip(self):
        self.store.save_state(State("noir", voice=False))
        self.assertEqual(self.store.load_state(), State("noir", voice=False))

    def test_broken_files_give_defaults(self):
        (self.home / "state.json").write_text("{broken")
        self.assertEqual(self.store.load_state(), State())
        self.assertEqual(self.store.load_config(), {})

    def test_seen_keys_per_session(self):
        self.store.save_seen("a/b", ("k1", "k2"))
        self.assertEqual(self.store.load_seen("a/b"), ("k1", "k2"))
        self.assertEqual(self.store.load_seen("other"), ())


class PersonasTest(support.TempHomeTest):
    def test_builtin_personas_have_phrases(self):
        personas = Personas(Paths(self.home)).all()
        self.assertEqual(set(personas), {"tsundere", "warrior", "butler", "noir"})
        for persona in personas.values():
            self.assertTrue(persona.phrases.get("permission"), persona.name)
            self.assertTrue(persona.phrases.get("idle"), persona.name)

    def test_user_persona_overrides_builtin(self):
        (self.home / "personas").mkdir()
        (self.home / "personas" / "noir.md").write_text("---\ndescription: мой\n---\nmine")
        self.assertEqual(Personas(Paths(self.home)).get("noir").description, "мой")


class TranscriptTest(support.TempHomeTest):
    def test_reads_only_assistant_text(self):
        path = support.write_transcript(
            self.home / "t.jsonl",
            [
                {"type": "user", "message": {"role": "user", "content": "нет"}},
                "{broken",
                support.assistant("да"),
            ],
        )
        self.assertEqual([(b.key, b.text) for b in read_text_blocks(path)], [("2:0", "да")])

    def test_missing_file(self):
        self.assertEqual(read_text_blocks(self.home / "nope.jsonl"), [])


class ElevenLabsTest(support.TempHomeTest):
    def synth(self, **config):
        settings = Settings.from_sources({"api_key": "k", **config}, {})
        return ElevenLabs(settings, self.home / "cache", Log(self.home / "log"))

    def test_miss_requests_and_caches(self):
        synth = self.synth()
        with mock.patch.object(synth, "request", return_value=b"mp3") as request:
            path = synth.audio_file("привет", "V")
            again = synth.audio_file("привет", "V")
        self.assertEqual((path.read_bytes(), again), (b"mp3", path))
        request.assert_called_once_with("привет", "V")

    def test_failure_returns_none(self):
        synth = self.synth()
        with mock.patch.object(synth, "request", return_value=None):
            self.assertIsNone(synth.audio_file("привет", "V"))

    def test_no_key_or_voice_skips_network(self):
        synth = ElevenLabs(Settings(), self.home / "cache", Log(self.home / "log"))
        with mock.patch.object(synth, "request") as request:
            self.assertIsNone(synth.audio_file("привет", "V"))
            self.assertIsNone(self.synth().audio_file("привет", None))
        request.assert_not_called()

    def test_prune_removes_oldest(self):
        cache = self.home / "cache"
        cache.mkdir()
        old, new = cache / "old.mp3", cache / "new.mp3"
        for i, path in enumerate((old, new)):
            path.write_bytes(b"x" * 700_000)
            os.utime(path, (1000 + i, 1000 + i))
        self.synth(cache_mb=1).prune_cache()
        self.assertEqual((old.exists(), new.exists()), (False, True))


class PlayerTest(support.TempHomeTest):
    def player(self, system):
        return audio.Player(Settings(), Log(self.home / "log"), system)

    def test_missing_player_is_logged_not_raised(self):
        with mock.patch.object(audio.players, "file_command", return_value=None):
            self.player(LINUX).play_file(self.home / "a.mp3")
        self.assertIn("no audio player for .mp3 files on linux", (self.home / "log").read_text())

    def test_command_gets_stdin_and_env(self):
        command = Command(("tool",), stdin="привет", env=MappingProxyType({"VP_X": "1"}))
        with (
            mock.patch.object(audio.voices, "say_command", return_value=command),
            mock.patch.object(audio.subprocess, "run") as run,
        ):
            self.player(LINUX).say("привет")
        kwargs = run.call_args.kwargs
        self.assertEqual(run.call_args.args[0], ("tool",))
        self.assertEqual(kwargs["input"], "привет".encode())
        self.assertEqual(kwargs["env"]["VP_X"], "1")


class MusicTest(unittest.TestCase):
    def run_ducked(self, current, enabled=True):
        with (
            mock.patch.object(music, "music_volume", return_value=current),
            mock.patch.object(music, "set_music_volume") as set_volume,
            mock.patch.object(music.shutil, "which", return_value="/usr/bin/osascript"),
        ):
            with self.assertRaises(RuntimeError):
                with music.ducked(enabled, 20):
                    raise RuntimeError
        return [c.args[0] for c in set_volume.call_args_list]

    def test_restores_volume_even_on_error(self):
        self.assertEqual(self.run_ducked(80), [20, 80])

    def test_quiet_or_disabled_untouched(self):
        self.assertEqual(self.run_ducked(10), [])
        self.assertEqual(self.run_ducked(80, enabled=False), [])
        self.assertEqual(self.run_ducked(None), [])


class ProcessQueueTest(support.TempHomeTest):
    def setUp(self):
        super().setUp()
        self.queue = ProcessQueue(Paths(self.home), Log(self.home / "log"))

    def spawn(self, *args):
        proc = subprocess.Popen([sys.executable, "-c", SLEEPER, *args], start_new_session=True)
        self.addCleanup(proc.wait)
        self.addCleanup(proc.kill)
        return proc

    def register(self, pid):
        (self.home / "workers").mkdir(exist_ok=True)
        (self.home / "workers" / str(pid)).write_text(str(pid))

    def test_kills_registered_worker(self):
        proc = self.spawn(WORKER_FLAG)
        self.register(proc.pid)
        time.sleep(0.2)
        self.assertEqual(self.queue.stop_all(), 1)
        self.assertIsNotNone(proc.wait(timeout=5))
        self.assertEqual(list((self.home / "workers").iterdir()), [])

    def test_never_kills_foreign_process(self):
        proc = self.spawn()
        self.register(proc.pid)
        self.assertEqual(self.queue.stop_all(), 0)
        self.assertIsNone(proc.poll())

    def test_garbage_marker_removed(self):
        (self.home / "workers").mkdir()
        (self.home / "workers" / "junk").write_text("abc")
        self.assertEqual(self.queue.stop_all(), 0)
        self.assertEqual(list((self.home / "workers").iterdir()), [])

    def test_registration_removed_after_block(self):
        with self.queue.registered(12345):
            self.assertTrue((self.home / "workers" / "12345").exists())
        self.assertFalse((self.home / "workers" / "12345").exists())


if __name__ == "__main__":
    unittest.main()
