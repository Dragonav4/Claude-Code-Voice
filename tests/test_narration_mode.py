"""Narration mode: every step or only the end of a turn, plus a per-turn limit (#3)."""

import io
import json
from contextlib import redirect_stdout

import support
from voice_personas.app.control import run_command
from voice_personas.app.narrate import narrate
from voice_personas.app.prompt import on_prompt
from voice_personas.domain import Persona, Settings, State

OPEN, CLOSE = "<speak>", "</speak>"


class StateTest(support.TempHomeTest):
    def test_default_and_garbage(self):
        self.assertEqual(State().narration, "all")
        self.assertEqual(State.from_dict({"narration": "loud"}).narration, "all")
        self.assertEqual(State.from_dict({"narration": "end"}).narration, "end")

    def test_roundtrip(self):
        app = self.app()
        app.store.save_state(State("noir").with_narration("end"))
        self.assertEqual(app.store.load_state().narration, "end")


class RulesTest(support.TempHomeTest):
    def test_end_mode_asks_for_one_line_at_the_end(self):
        persona = Persona("noir", prompt="p")
        end = persona.context(with_voice=True, narration="end")
        self.assertIn("only once", end)
        self.assertNotIn("Before a batch of tool calls", end)
        self.assertNotEqual(persona.fingerprint(True, "end"), persona.fingerprint(True, "all"))

    def test_turn_limit_setting(self):
        self.assertEqual(Settings.from_sources({}, {}).max_lines_per_turn, 5)
        self.assertEqual(
            Settings.from_sources({"max_lines_per_turn": 99}, {}).max_lines_per_turn, 20
        )


class NarrateTest(support.TempHomeTest):
    def setUp(self):
        super().setUp()
        self.application = self.app()
        self.path = self.home / "t.jsonl"

    def say(self, *texts, event="PostToolUse"):
        records = [support.assistant(text) for text in texts]
        support.write_transcript(self.path, records)
        payload = {"session_id": "s", "transcript_path": str(self.path), "hook_event_name": event}
        out = io.StringIO()
        with redirect_stdout(out):
            narrate(self.application, payload)
        return [line.split("] ", 1)[1] for line in out.getvalue().splitlines()]

    def test_end_mode_is_silent_after_tools_and_speaks_last_line_on_stop(self):
        self.application.store.save_state(State("noir").with_narration("end"))
        lines = [f"{OPEN}шаг {i}{CLOSE}" for i in range(3)]
        self.assertEqual(self.say(*lines), [])
        self.assertEqual(self.say(*lines, event="Stop"), ["шаг 2"])

    def test_turn_limit_and_reset_on_new_prompt(self):
        self.write_config({"max_lines_per_turn": 2})
        self.application = self.app()
        self.application.store.save_state(State("noir"))
        lines = [f"{OPEN}реплика {i}{CLOSE}" for i in range(4)]
        self.assertEqual(len(self.say(*lines[:3])), 2)
        self.assertEqual(self.say(*lines), [])
        on_prompt(self.application, {"session_id": "s"})
        self.assertEqual(self.say(*lines, f"{OPEN}новая{CLOSE}"), ["новая"])

    def test_old_spoken_file_format_still_works(self):
        self.application.store.save_state(State("noir"))
        spoken = self.home / "spoken"
        spoken.mkdir()
        (spoken / "s.json").write_text(json.dumps({"keys": ["0:0:0"]}), encoding="utf-8")
        self.assertEqual(self.say(f"{OPEN}старая{CLOSE}", f"{OPEN}новая{CLOSE}"), ["новая"])


class CommandTest(support.TempHomeTest):
    def test_voice_mode(self):
        app = self.app()
        self.assertEqual(run_command(app, ["voice", "mode", "end"])[0], 0)
        self.assertEqual(app.store.load_state().narration, "end")
        self.assertEqual(run_command(app, ["voice", "mode", "loud"])[0], 1)
        self.assertIn("в конце хода", run_command(app, ["voice", "status"])[1])
