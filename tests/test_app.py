import io
import json
import subprocess
import sys
import unittest
from contextlib import redirect_stdout
from unittest import mock

import support
from voice_personas.app.control import run_command
from voice_personas.app.narrate import narrate
from voice_personas.app.notify import notify
from voice_personas.app.prompt import on_prompt
from voice_personas.app.speak import speak_line
from voice_personas.domain import State


def captured(func, *args):
    out = io.StringIO()
    with redirect_stdout(out):
        result = func(*args)
    return result, out.getvalue()


class NarrateTest(support.TempHomeTest):
    def payload(self, text, session="s"):
        path = support.write_transcript(self.home / "t.jsonl", [support.assistant(text)])
        return {
            "session_id": session,
            "transcript_path": str(path),
            "hook_event_name": "PostToolUse",
        }

    def test_new_lines_spoken_once(self):
        app = self.app()
        app.store.save_state(State("warrior"))
        payload = self.payload("<speak>В бой</speak>")
        self.assertEqual(captured(narrate, app, payload)[1], "[dry-run:warrior] В бой\n")
        self.assertEqual(captured(narrate, app, payload)[1], "")

    def test_silent_when_voice_off(self):
        app = self.app()
        app.store.save_state(State("warrior", voice=False))
        self.assertEqual(captured(narrate, app, self.payload("<speak>В бой</speak>"))[1], "")


class NotifyTest(support.TempHomeTest):
    def test_persona_phrase(self):
        app = self.app()
        app.store.save_state(State("warrior"))
        out = captured(notify, app, {"notification_type": "idle_prompt"})[1]
        self.assertEqual(out, "[dry-run:warrior] Задание выполнено. Жду новых приказов.\n")

    def test_can_be_disabled(self):
        self.write_config({"notifications": False})
        app = self.app()
        app.store.save_state(State("warrior"))
        self.assertEqual(captured(notify, app, {"notification_type": "idle_prompt"})[1], "")


class PromptTest(support.TempHomeTest):
    def test_context_and_interrupt(self):
        app = self.app()
        app.store.save_state(State("noir"))
        with mock.patch.object(app.queue, "stop_all") as stop:
            context = on_prompt(app, {})
        stop.assert_called_once()
        self.assertIn("Active persona: noir", context)

    def test_no_persona_no_context(self):
        self.assertIsNone(on_prompt(self.app(), {}))

    def test_interrupt_can_be_disabled(self):
        self.write_config({"interrupt_on_prompt": False})
        app = self.app()
        with mock.patch.object(app.queue, "stop_all") as stop:
            on_prompt(app, {})
        stop.assert_not_called()


class SpeakLineTest(support.TempHomeTest):
    def run_line(self, synth_result, **config):
        self.write_config(config)
        app = self.app()
        with (
            mock.patch.object(app.synth, "audio_file", return_value=synth_result),
            mock.patch.object(app.player, "play_file") as play,
            mock.patch.object(app.player, "say") as say,
        ):
            speak_line(app, "привет", "V")
        return play, say

    def test_elevenlabs_audio_played(self):
        play, say = self.run_line("/a.mp3")
        play.assert_called_once_with("/a.mp3")
        say.assert_not_called()

    def test_falls_back_to_say(self):
        play, say = self.run_line(None)
        say.assert_called_once_with("привет")
        play.assert_not_called()

    def test_fallback_disabled(self):
        play, say = self.run_line(None, fallback="none")
        say.assert_not_called()


class ControlTest(support.TempHomeTest):
    def test_persona_and_voice(self):
        app = self.app()
        self.assertEqual(run_command(app, ["persona", "Butler"])[0], 0)
        self.assertEqual(run_command(app, ["voice", "off"]), (0, "Озвучка: выкл."))
        self.assertEqual(app.store.load_state(), State("butler", voice=False))

    def test_unknown_persona_and_command(self):
        app = self.app()
        self.assertEqual(run_command(app, ["persona", "ghost"])[0], 1)
        self.assertEqual(run_command(app, ["voice", "loud"])[0], 1)
        self.assertEqual(run_command(app, [])[0], 1)

    def test_voice_test_custom_text(self):
        app = self.app()
        app.store.save_state(State("noir"))
        (code, _), out = captured(run_command, app, ["voice", "test", "раз", "два"])
        self.assertEqual((code, out), (0, "[dry-run:noir] раз два\n"))

    def test_status_mentions_key_state(self):
        text = run_command(self.app(), ["voice", "status"])[1]
        self.assertIn("ElevenLabs API key: НЕ найден", text)


class EntrypointTest(support.TempHomeTest):
    """bin/*.py run like real hooks: a separate process with JSON on stdin."""

    def run_bin(self, name, payload="", *args):
        return subprocess.run(
            [sys.executable, str(support.ROOT / "bin" / name), *args],
            input=payload,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=self.env(),
            timeout=20,
        )

    def test_speak_hook(self):
        self.app().store.save_state(State("warrior"))
        path = support.write_transcript(
            self.home / "t.jsonl", [support.assistant("<speak>В бой</speak>")]
        )
        result = self.run_bin(
            "on_speak.py", json.dumps({"session_id": "x", "transcript_path": str(path)})
        )
        self.assertEqual((result.returncode, result.stdout), (0, "[dry-run:warrior] В бой\n"))

    def test_garbage_input_never_fails(self):
        for name in ("on_speak.py", "on_prompt.py", "on_notify.py", "worker.py"):
            result = self.run_bin(name, "not json")
            self.assertEqual((result.returncode, result.stderr), (0, ""), name)

    def test_prompt_hook_prints_persona(self):
        self.app().store.save_state(State("noir"))
        self.assertIn("Active persona: noir", self.run_bin("on_prompt.py", "{}").stdout)

    def test_ctl(self):
        result = self.run_bin("ctl.py", "", "persona", "list")
        self.assertEqual(result.returncode, 0)
        self.assertIn("warrior", result.stdout)


if __name__ == "__main__":
    unittest.main()
