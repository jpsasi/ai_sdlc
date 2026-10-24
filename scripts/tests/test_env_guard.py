import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "hooks"))
env_guard = __import__("env-guard")


class EnvGuardTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cwd = os.getcwd()
        os.chdir(self.tmp.name)
        Path("deploy").mkdir()
        Path("deploy/.env").write_text("DB_PASSWORD=hunter2\n")
        Path(".env.example").write_text("DB_PASSWORD=\n")

    def tearDown(self):
        os.chdir(self.cwd)
        self.tmp.cleanup()

    def run_guard(self, command):
        stdin = io.StringIO(json.dumps({"tool_name": "Bash", "tool_input": {"command": command}}))
        with mock.patch("sys.stdin", stdin), mock.patch("sys.stderr", io.StringIO()):
            return env_guard.main()

    def test_refuses_commands_naming_a_secrets_file(self):
        for command in ("cat .env", "cat deploy/.env", "less ./.env.local", "source .env.production && make",
                        "head -5 ~/app/.env"):
            self.assertEqual(self.run_guard(command), 2, command)

    def test_allows_example_files_and_lookalikes(self):
        for command in ("cat .env.example", "cp .env.sample .env.template", "direnv allow .envrc",
                        "grep -n DB_ deploy/settings.py", "ls -la"):
            self.assertEqual(self.run_guard(command), 0, command)

    def test_refuses_recursive_search_over_a_tree_with_secrets(self):
        for command in ("grep -rn PASSWORD deploy/", "grep -R token .", "rg --hidden PASSWORD",
                        "find . -type f -exec cat {} +", "find deploy | xargs grep PASSWORD"):
            self.assertEqual(self.run_guard(command), 2, command)

    def test_allows_recursive_search_that_excludes_secrets(self):
        for command in ("grep -rn --exclude='.env*' PASSWORD deploy/", "grep -rn --exclude .env PASSWORD .",
                        "rg --hidden -g '!.env*' PASSWORD", "rg PASSWORD", "find . -name '*.py' -exec grep x {} +"):
            self.assertEqual(self.run_guard(command), 0, command)

    def test_allows_recursive_search_when_no_secrets_exist(self):
        Path("deploy/.env").unlink()
        self.assertEqual(self.run_guard("grep -rn PASSWORD ."), 0)


if __name__ == "__main__":
    unittest.main()
