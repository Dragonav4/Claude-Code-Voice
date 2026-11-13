"""ElevenLabs audio tags: kept for v3/v4 models, never read aloud anywhere else (#13)."""

import unittest
from unittest import mock

import support
from voice_personas.app.speak import speak_line
from voice_personas.domain import clean_spoken, strip_audio_tags, supports_audio_tags


class CleanTest(unittest.TestCase):
    def test_known_tags_survive_cleaning(self):
        self.assertEqual(
            clean_spoken("[sarcastic] Ужасно. [Laughs] Да."), "[sarcastic] Ужасно. [laughs] Да."
        )

    def test_unknown_tags_are_removed_with_their_word(self):
        self.assertEqual(clean_spoken("[blushes] Ну [smirks] ладно."), "Ну ладно.")

    def test_strip_removes_every_tag(self):
        self.assertEqual(strip_audio_tags("[sighs] Готово. [laughs]"), "Готово.")

    def test_model_support(self):
        for model in ("eleven_v3", "eleven_v4", "eleven_v4_turbo", "eleven_v3_conversational"):
            self.assertTrue(supports_audio_tags(model), model)
        for model in ("eleven_multilingual_v2", "eleven_flash_v2_5", ""):
            self.assertFalse(supports_audio_tags(model), model)


class SpeakLineTest(support.TempHomeTest):
    def run_line(self, model, synth_result):
        self.write_config({"model_id": model})
        app = self.app()
        with (
            mock.patch.object(app.synth, "audio_file", return_value=synth_result) as synth,
            mock.patch.object(app.player, "play_file"),
            mock.patch.object(app.player, "say") as say,
        ):
            speak_line(app, "[laughs] Попался.", "V")
        return synth, say

    def test_v4_gets_the_tag(self):
        synth, _ = self.run_line("eleven_v4_turbo", "/a.mp3")
        synth.assert_called_once_with("[laughs] Попался.", "V")

    def test_older_model_gets_plain_text(self):
        synth, _ = self.run_line("eleven_multilingual_v2", "/a.mp3")
        synth.assert_called_once_with("Попался.", "V")

    def test_system_voice_never_reads_a_tag(self):
        _, say = self.run_line("eleven_v4_turbo", None)
        say.assert_called_once_with("Попался.")


if __name__ == "__main__":
    unittest.main()
