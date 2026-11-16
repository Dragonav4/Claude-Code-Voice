import os
import unittest
from pathlib import Path

import support
from voice_personas.app.container import build_app
from voice_personas.domain import parse_dotenv
from voice_personas.infra.environment import load_environment

SAMPLE = """
# comment
ELEVENLABS_API_KEY=sk_plain
export ELEVENLABS_VOICE_ID="quoted value"
ELEVENLABS_MODEL_ID='single'  # trailing comment
EMPTY=
not a variable line
lower_case=ignored
URL=https://example.com/#anchor
"""


class ParseTest(unittest.TestCase):
    def test_parses_common_forms(self):
        self.assertEqual(
            dict(parse_dotenv(SAMPLE)),
            {
                "ELEVENLABS_API_KEY": "sk_plain",
                "ELEVENLABS_VOICE_ID": "quoted value",
                "ELEVENLABS_MODEL_ID": "single",
                "URL": "https://example.com/#anchor",
            },
        )

    def test_empty_values_are_unset(self):
        self.assertNotIn("EMPTY", parse_dotenv("EMPTY=\nEMPTY2=''\n"))


class LoadTest(support.TempHomeTest):
    def setUp(self):
        super().setUp()
        self.plugin = self.home / "plugin"
        self.plugin.mkdir()
        self.state = self.home / "state"

    def write(self, path, text):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        path.chmod(0o600)

    def test_precedence_env_then_home_then_plugin(self):
        self.write(self.plugin / ".env", "A=plugin\nB=plugin\nC=plugin\n")
        self.write(self.state / ".env", "A=home\nB=home\n")
        env = {"VOICE_PERSONAS_HOME": str(self.state), "A": "process"}
        result = load_environment(env, self.plugin)
        self.assertEqual(
            (result.env["A"], result.env["B"], result.env["C"]), ("process", "home", "plugin")
        )

    def test_home_from_plugin_env_with_tilde(self):
        self.write(self.plugin / ".env", "VOICE_PERSONAS_HOME=~/vp-test-home\n")
        result = load_environment({}, self.plugin)
        self.assertEqual(Path(result.env["VOICE_PERSONAS_HOME"]), Path.home() / "vp-test-home")

    def test_missing_files_are_fine(self):
        result = load_environment({"X": "1", "VOICE_PERSONAS_HOME": str(self.state)}, self.plugin)
        # Compare names only: a failing assertion must never print real values.
        self.assertEqual(sorted(result.env), ["VOICE_PERSONAS_HOME", "X"])
        self.assertEqual(result.warnings, ())

    def test_tests_never_see_the_real_home(self):
        from voice_personas.infra import environment

        self.assertTrue(str(environment.default_home()).startswith(str(self.home)))

    @unittest.skipIf(os.name == "nt", "POSIX permissions")
    def test_warns_about_readable_file(self):
        self.write(self.plugin / ".env", "A=1\n")
        (self.plugin / ".env").chmod(0o644)
        result = load_environment({}, self.plugin)
        self.assertTrue(any("chmod 600" in w for w in result.warnings))

    def test_key_only_in_dotenv_reaches_settings(self):
        self.write(self.plugin / ".env", "ELEVENLABS_API_KEY=sk_from_dotenv\n")
        app = build_app(self.env(), env_dir=self.plugin)
        self.assertEqual(app.settings.api_key, "sk_from_dotenv")
        self.assertEqual(app.paths.home, self.home)


if __name__ == "__main__":
    unittest.main()
