import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

HOOKS = Path(__file__).resolve().parents[1] / "hooks"

CONFIG = """# Factory config

Target branch: main

## Commands
| Command | Run |
|---------|-----|
| Secrets (staged) | {secrets} |
"""


class PreCommitTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cwd = os.getcwd()
        os.chdir(self.tmp.name)
        self.git("init", "-q", "-b", "main")
        hooks = Path(self.git("rev-parse", "--git-path", "hooks").strip())
        hooks.mkdir(parents=True, exist_ok=True)
        shutil.copy(HOOKS / "pre-commit", hooks / "pre-commit")
        shutil.copy(HOOKS / "protected.sh", hooks / "factory-protected.sh")
        (hooks / "pre-commit").chmod(0o755)
        self.git("checkout", "-qb", "factory/REF-12")

    def tearDown(self):
        os.chdir(self.cwd)
        self.tmp.cleanup()

    def git(self, *args):
        return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout

    def commit(self, config=None):
        """(exit code, stderr) of committing a new file, with the config holding this Secrets (staged) command."""
        if config is not None:
            Path(".factory").mkdir(exist_ok=True)
            Path(".factory/config.md").write_text(config, encoding="utf-8")
        Path("file.txt").write_text(str(len(os.listdir("."))) + os.urandom(4).hex(), encoding="utf-8")
        self.git("add", "-A")
        result = subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "x"],
                                capture_output=True, text=True)
        return result.returncode, result.stderr

    def test_a_clean_scan_allows_the_commit(self):
        self.assertEqual(self.commit(CONFIG.format(secrets="true"))[0], 0)

    def test_a_secret_refuses_the_commit(self):
        code, err = self.commit(CONFIG.format(secrets="echo leaked-key; exit 1"))
        self.assertEqual(code, 1)
        self.assertIn("found a secret", err)
        self.assertIn("leaked-key", err)

    def test_a_missing_scanner_or_row_refuses_the_commit(self):
        code, err = self.commit(CONFIG.format(secrets="no-such-scanner --staged"))
        self.assertEqual(code, 1)
        self.assertIn("no-such-scanner is missing", err)
        code, err = self.commit("# Factory config\n\nTarget branch: main\n")
        self.assertEqual(code, 1)
        self.assertIn("no Secrets (staged) command", err)

    def test_an_escaped_pipe_in_the_command_runs_as_a_pipe(self):
        code, err = self.commit(CONFIG.format(secrets="echo ok \\| grep -q ok"))
        self.assertEqual(code, 0, err)

    def test_a_branch_without_the_config_only_warns(self):
        code, err = self.commit()
        self.assertEqual(code, 0)
        self.assertIn("secrets scan didn't run", err)

    def test_the_default_branch_is_still_protected(self):
        self.git("symbolic-ref", "HEAD", "refs/heads/main")
        code, err = self.commit(CONFIG.format(secrets="true"))
        self.assertEqual(code, 1)
        self.assertIn("'main' is protected", err)


if __name__ == "__main__":
    unittest.main()
