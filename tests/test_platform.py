import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

import support
from voice_personas.domain import detect_language
from voice_personas.infra.platform import LINUX, MACOS, WINDOWS, current_system, players, voices
from voice_personas.infra.platform.locks import exclusive_lock
from voice_personas.infra.platform.processes import command_line, spawn_detached, terminate_tree

SLEEPER = "import sys, time; time.sleep(30)"
TRY_LOCK = (
    "import sys; sys.path.insert(0, sys.argv[1]);"
    "from pathlib import Path;"
    "from voice_personas.infra.platform.locks import exclusive_lock\n"
    "try:\n"
    "    with exclusive_lock(Path(sys.argv[2]), timeout_s=0.3): print('locked')\n"
    "except TimeoutError: print('timeout')"
)


def which_only(*names):
    return lambda name: f"/usr/bin/{name}" if name in names else None


class SystemTest(unittest.TestCase):
    def test_mapping(self):
        self.assertEqual(current_system("darwin"), MACOS)
        self.assertEqual(current_system("win32"), WINDOWS)
        self.assertEqual(current_system("linux"), LINUX)
        self.assertEqual(current_system("freebsd14"), LINUX)


class LanguageTest(unittest.TestCase):
    def test_cyrillic_is_russian(self):
        self.assertEqual(detect_language("Готово, тесты зелёные"), "ru")
        self.assertIsNone(detect_language("All tests pass"))


class LockTest(support.TempHomeTest):
    def try_lock_in_child(self, path):
        return subprocess.run(
            [sys.executable, "-c", TRY_LOCK, str(support.ROOT), str(path)],
            capture_output=True,
            text=True,
            timeout=20,
        ).stdout.strip()

    def test_second_process_waits_for_the_lock(self):
        path = self.home / "x.lock"
        with exclusive_lock(path):
            self.assertEqual(self.try_lock_in_child(path), "timeout")
        self.assertEqual(self.try_lock_in_child(path), "locked")


class ProcessesTest(unittest.TestCase):
    def test_spawn_find_and_terminate(self):
        process = spawn_detached([sys.executable, "-c", SLEEPER, "--marker-flag"], b"")
        self.addCleanup(process.wait, 10)
        time.sleep(0.5)
        self.assertIn("--marker-flag", command_line(process.pid) or "")
        terminate_tree(process.pid)
        process.wait(timeout=10)
        self.assertIsNone(command_line(process.pid))


class PlayersTest(unittest.TestCase):
    def test_macos_afplay(self):
        cmd = players.file_command(MACOS, Path("/a.mp3"), 1.25, 0.5, which_only("afplay"))
        self.assertEqual(cmd.argv, ("afplay", "-r", "1.25", "-v", "0.5", str(Path("/a.mp3"))))

    def test_linux_prefers_mpv_then_ffplay(self):
        cmd = players.file_command(LINUX, Path("/a.mp3"), 1.5, 0.8, which_only("mpv", "ffplay"))
        self.assertEqual(cmd.argv[0], "mpv")
        self.assertIn("--speed=1.5", cmd.argv)
        cmd = players.file_command(LINUX, Path("/a.mp3"), 1.0, 1.0, which_only("ffplay"))
        self.assertEqual(cmd.argv[0], "ffplay")

    def test_linux_without_mp3_player(self):
        self.assertIsNone(players.file_command(LINUX, Path("/a.mp3"), 1, 1, which_only("aplay")))
        cmd = players.file_command(LINUX, Path("/a.wav"), 1, 1, which_only("aplay"))
        self.assertEqual(cmd.argv[0], "aplay")

    def test_windows_powershell_gets_path_through_env(self):
        cmd = players.file_command(WINDOWS, Path("C:/o'brien/a.mp3"), 1, 0.5, which_only())
        self.assertEqual(cmd.argv[0], "powershell")
        self.assertEqual(cmd.env["VP_FILE"], str(Path("C:/o'brien/a.mp3")))
        self.assertNotIn("o'brien", " ".join(cmd.argv))

    def test_windows_prefers_ffplay(self):
        cmd = players.file_command(WINDOWS, Path("a.mp3"), 1, 1, which_only("ffplay"))
        self.assertEqual(cmd.argv[0], "ffplay")


class VoicesTest(unittest.TestCase):
    MAC_LISTING = (
        "Milena (Русский (Россия)) ru_RU    # Здравствуйте!\n"
        "Samantha            en_US    # Hello!\n"
        "Good News           en_US    # Hello!\n"
    )

    def test_mac_listing(self):
        self.assertEqual(
            voices.parse_say_listing(self.MAC_LISTING),
            {"Milena": "ru_RU", "Samantha": "en_US", "Good News": "en_US"},
        )

    def test_macos_picks_russian_voice_for_cyrillic(self):
        cmd = voices.say_command(MACOS, "привет", None, 1.0, which_only("say"), self.MAC_LISTING)
        self.assertEqual(cmd.argv, ("say", "-r", "175", "-v", "Milena", "--", "привет"))

    def test_macos_default_voice_for_english(self):
        cmd = voices.say_command(MACOS, "hello", None, 1.0, which_only("say"), self.MAC_LISTING)
        self.assertNotIn("-v", cmd.argv)

    def test_macos_explicit_voice_wins_if_installed(self):
        cmd = voices.say_command(
            MACOS, "привет", "Samantha", 1.0, which_only("say"), self.MAC_LISTING
        )
        self.assertIn("Samantha", cmd.argv)
        cmd = voices.say_command(MACOS, "-v hack", "Nope", 1.0, which_only("say"), self.MAC_LISTING)
        self.assertEqual(cmd.argv[-2:], ("--", "-v hack"))

    def test_linux_espeak_reads_text_from_stdin(self):
        cmd = voices.say_command(LINUX, "привет", None, 1.0, which_only("espeak-ng"), "")
        self.assertEqual(cmd.argv, ("espeak-ng", "-v", "ru", "-s", "175", "--stdin"))
        self.assertEqual(cmd.stdin, "привет")

    def test_windows_text_never_in_the_script(self):
        cmd = voices.say_command(WINDOWS, "'; rm -rf /", None, 1.5, which_only(), "")
        self.assertEqual(cmd.argv[0], "powershell")
        self.assertEqual(cmd.stdin, "'; rm -rf /")
        self.assertNotIn("rm -rf", " ".join(cmd.argv))
        self.assertEqual(cmd.env["VP_RATE"], "5")

    def test_no_tool_no_command(self):
        self.assertIsNone(voices.say_command(LINUX, "hi", None, 1.0, which_only(), ""))


@unittest.skipUnless(shutil.which("sh"), "needs a POSIX sh (Git Bash on Windows)")
class LauncherTest(unittest.TestCase):
    RUN = str(support.ROOT / "bin" / "run.sh")
    CTL = str(support.ROOT / "bin" / "ctl.py")

    def run_launcher(self, env):
        return subprocess.run(
            ["sh", self.RUN, self.CTL, "persona", "list"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=env,
            timeout=30,
        )

    def test_runs_python_script(self):
        result = self.run_launcher({**os.environ, "VOICE_PERSONAS_HOME": tempfile.mkdtemp()})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("warrior", result.stdout)

    @unittest.skipIf(os.name == "nt", "the stub is a POSIX script")
    def test_skips_a_python3_stub(self):
        stub_dir = Path(tempfile.mkdtemp())
        (stub_dir / "python3").write_text("#!/bin/sh\nexit 49\n", encoding="utf-8")
        (stub_dir / "python3").chmod(0o755)
        (stub_dir / "python").symlink_to(sys.executable)
        env = {
            **os.environ,
            "PATH": f"{stub_dir}{os.pathsep}/usr/bin{os.pathsep}/bin",
            "VOICE_PERSONAS_HOME": tempfile.mkdtemp(),
        }
        result = self.run_launcher(env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("warrior", result.stdout)


if __name__ == "__main__":
    unittest.main()
