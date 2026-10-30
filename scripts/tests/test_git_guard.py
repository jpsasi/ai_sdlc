import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

HOOKS = Path(__file__).resolve().parents[1] / "hooks"

CONFIG = """# Factory config

Host: github
Target branch: dev

## Branches
| Branch | Rule |
|--------|------|
| qa | protected |
| release/* | protected |
| dev_staging | frozen |
| staging | retired |

## Migrations
| Folder | File name |
|--------|-----------|
| db/migration | V<n>__*.sql |

## Commit message bans
| Pattern | Why |
|---------|-----|
| `\\bM([1-9]\\|1[0-2])\\b` | name modules, don't number them |

## Commands
| Command | Run |
|---------|-----|
| Secrets (staged) | true |
"""

TEST = """class CreditTest {
    @Test
    void appliesOnce() {
        assertEquals(1, credit.apply());
    }

    @Test
    void retryIsIdempotent() {
        assertEquals(0, credit.retry());
    }
}
"""


@unittest.skipUnless(shutil.which("git"), "needs git")
class GitGuardTest(unittest.TestCase):
    """The installed hooks, run by real git commands in a clone of a throwaway origin."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.origin = base / "origin.git"
        self.root = base / "work"
        self.git_in(base, "init", "-q", "--bare", "-b", "dev", str(self.origin))
        self.git_in(base, "clone", "-q", str(self.origin), str(self.root))
        self.git("config", "user.email", "t@example.com")
        self.git("config", "user.name", "t")
        hooks = self.root / ".factory/hooks"
        hooks.mkdir(parents=True)
        for name in ("pre-commit", "pre-merge-commit", "commit-msg", "pre-push"):
            shutil.copy(HOOKS / name, hooks / name)
        shutil.copy(HOOKS / "git-guard.py", hooks / "factory-git-guard.py")
        self.write(".factory/config.md", CONFIG)
        self.write("db/migration/V1__init.sql", "create table a;\n")
        self.write("db/migration/V2__credit.sql", "create table b;\n")
        self.write("src/test/CreditTest.java", TEST)
        self.git("switch", "-qc", "dev")
        self.git("add", ".")
        self.git("commit", "-qm", "init")  # hooks not enabled yet
        self.git("push", "-q", "origin", "dev")
        self.git("config", "core.hooksPath", ".factory/hooks")
        self.git("switch", "-qc", "factory/IE-12")

    def tearDown(self):
        self.tmp.cleanup()

    def git_in(self, cwd, *args):
        return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)

    def git(self, *args):
        result = self.git_in(self.root, *args)
        if result.returncode != 0:
            raise AssertionError(f"git {' '.join(args)}: {result.stderr}")
        return result

    def write(self, path, text):
        (self.root / path).parent.mkdir(parents=True, exist_ok=True)
        (self.root / path).write_text(text)

    def commit(self, message="IE-12 step 1: split the fee"):
        """Stages everything and commits; returns (ok, stderr)."""
        self.git("add", "-A")
        result = self.git_in(self.root, "commit", "-qm", message)
        return result.returncode == 0, result.stderr

    def assertRefused(self, outcome, words):
        ok, err = outcome
        self.assertFalse(ok, "expected the hook to refuse")
        self.assertIn(words, err)

    # branches

    def test_work_branch_commit_is_allowed(self):
        self.write("src/Fee.java", "class Fee {}\n")
        self.assertEqual(self.commit(), (True, ""))

    def test_commits_on_protected_frozen_and_retired_branches_are_refused(self):
        for branch, words in (("dev", "pull request"), ("qa", "pull request"), ("release/1.2", "pull request"),
                              ("dev_staging", "frozen"), ("staging", "retired")):
            self.git("switch", "-qC", branch)
            self.write("src/Fee.java", f"class Fee {{}} // {branch}\n")
            self.assertRefused(self.commit(), words)

    def test_push_to_protected_branch_is_refused(self):
        self.write("src/Fee.java", "class Fee {}\n")
        self.commit()
        result = self.git_in(self.root, "push", "-q", "origin", "HEAD:dev")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("push to 'dev' is blocked", result.stderr)
        self.assertEqual(self.git_in(self.root, "push", "-q", "origin", "HEAD").returncode, 0)

    def test_creating_a_protected_branch_without_new_commits_is_allowed(self):
        self.assertEqual(self.git_in(self.root, "push", "-q", "origin", "origin/dev:refs/heads/qa").returncode, 0)

    # commit messages

    def test_banned_words_are_refused(self):
        self.write("src/Fee.java", "class Fee {}\n")
        self.assertRefused(self.commit("IE-12 step 1: split the fee in M4"), "name modules")

    def test_any_message_style_and_attribution_are_allowed(self):
        self.write("src/Fee.java", "class Fee {}\n")
        self.assertEqual(self.commit("review: IE-12 passed\n\nCo-Authored-By: Bot <b@x>"), (True, ""))

    # migrations

    def test_new_migration_must_be_above_the_target_branch(self):
        self.write("db/migration/V2__fee.sql", "alter table b;\n")
        self.assertRefused(self.commit(), "used by more than one migration")
        os.remove(self.root / "db/migration/V2__fee.sql")
        self.write("db/migration/V1_5__fee.sql", "alter table b;\n")
        self.assertRefused(self.commit(), "Renumber it above 2")
        os.remove(self.root / "db/migration/V1_5__fee.sql")
        self.write("db/migration/V3__fee.sql", "alter table b;\n")
        self.assertEqual(self.commit(), (True, ""))

    def test_misnamed_migration_is_refused(self):
        self.write("db/migration/fee.sql", "alter table b;\n")
        self.assertRefused(self.commit(), "doesn't match the migration name")

    def test_shipped_migration_never_changes(self):
        self.write("db/migration/V2__credit.sql", "create table b2;\n")
        self.assertRefused(self.commit(), "already on origin/dev")

    def test_merging_a_clashing_migration_from_the_target_is_refused(self):
        self.write("db/migration/V3__fee.sql", "alter table b;\n")
        self.commit()
        other = Path(self.tmp.name) / "other"
        self.git_in(self.tmp.name, "clone", "-q", "-b", "dev", str(self.origin), str(other))
        (other / "db/migration/V3__rate.sql").write_text("alter table c;\n")
        self.git_in(other, "add", ".")
        self.git_in(other, "-c", "user.name=o", "-c", "user.email=o@x", "commit", "-qm", "IE-9 step 1: rate")
        self.git_in(other, "push", "-q", "origin", "dev")
        self.git("fetch", "-q", "origin")
        result = self.git_in(self.root, "merge", "--no-edit", "origin/dev")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Renumber it above 3", result.stderr)

    def test_missing_target_ref_fails_closed(self):
        self.git("update-ref", "-d", "refs/remotes/origin/dev")
        self.write("db/migration/V3__fee.sql", "alter table b;\n")
        self.assertRefused(self.commit(), "git fetch origin dev")

    def test_branches_protected_in_git_config_stay_protected(self):
        self.git("config", "--add", "factory.protected", "hotfix/*")
        self.git("switch", "-qc", "hotfix/1")
        self.write("src/Fee.java", "class Fee {}\n")
        self.assertRefused(self.commit(), "pull request")

    def test_a_solo_repo_may_commit_to_the_default_branch(self):
        self.git("remote", "set-head", "origin", "dev")  # dev is the default branch
        self.git("config", "factory.allowDefaultBranch", "true")
        self.git("switch", "-q", "dev")
        self.write("src/Fee.java", "class Fee {}\n")
        self.assertEqual(self.commit(), (True, ""))

    # tests

    def test_changing_a_shipped_assertion_needs_a_persons_approval(self):
        self.write("src/test/CreditTest.java", TEST.replace("assertEquals(1,", "assertEquals(2,"))
        self.assertRefused(self.commit("IE-12 step 2: adjust"), "changes or removes an assertion")
        self.assertEqual(self.commit("IE-12 step 2: adjust\n\nThe fee rule changed in IE-12.\n\n"
                                     "Test-change-approved-by: Priya"), (True, ""))

    def test_skipping_or_deleting_a_shipped_test_is_refused(self):
        self.write("src/test/CreditTest.java", TEST.replace("    @Test\n    void retry", "    @Disabled\n    @Test\n    void retry"))
        self.assertRefused(self.commit("IE-12 step 2: skip"), "skips, disables or narrows")
        self.git("checkout", "--", ".")
        self.write("src/test/CreditTest.java", TEST.split("\n    @Test\n    void retry")[0] + "\n}\n")
        self.assertRefused(self.commit("IE-12 step 2: drop"), "removes a test")
        self.git("reset", "-q", "--hard")
        os.remove(self.root / "src/test/CreditTest.java")
        self.assertRefused(self.commit("IE-12 step 2: drop"), "deleted")

    def test_adding_tests_and_editing_the_branchs_own_tests_is_free(self):
        self.write("src/test/CreditTest.java", TEST.replace("}\n}\n", "}\n\n    @Test\n    void splits() {\n"
                                                             "        assertEquals(3, fee.split());\n    }\n}\n"))
        self.write("src/test/FeeTest.java", "class FeeTest { @Test void a() { assertTrue(x); } }\n")
        self.assertEqual(self.commit("IE-12 step 2: add"), (True, ""))
        self.write("src/test/FeeTest.java", "class FeeTest { @Test void a() { assertFalse(x); } }\n")
        self.assertEqual(self.commit("IE-12 step 3: fix own test"), (True, ""))


    # secrets

    def scan_with(self, run):
        self.write(".factory/config.md", CONFIG.replace("| Secrets (staged) | true |", f"| Secrets (staged) | {run} |"))

    def test_a_staged_secret_is_refused(self):
        self.write("scan.sh", "git diff --cached | grep -q 'AK[I]A' && { echo 'leak: access key'; exit 1; }; exit 0\n")
        self.scan_with("sh scan.sh")
        self.assertEqual(self.commit(), (True, ""))
        self.write("src/Fee.java", 'class Fee { String key = "AKIA1234"; }\n')
        self.assertRefused(self.commit(), "leak: access key")

    def test_a_missing_secrets_row_fails_closed(self):
        self.write(".factory/config.md", CONFIG.replace("| Secrets (staged) | true |\n", ""))
        self.assertRefused(self.commit(), "no Secrets (staged) command")

    def test_an_escaped_pipe_in_the_secrets_command_runs_as_a_pipe(self):
        self.write(".factory/config.md", CONFIG.replace("| Secrets (staged) | true |", "| Secrets (staged) | echo ok \\| grep -q ok |"))
        self.assertEqual(self.commit(), (True, ""))

    def test_a_missing_secrets_scanner_fails_closed(self):
        self.scan_with("no-such-scanner --staged")
        self.assertRefused(self.commit(), "the secrets scan can't run")

    # enabling the hooks in a clone

    def enable(self):
        return subprocess.run(["sh", str(HOOKS / "enable-git-hooks.sh")], cwd=self.root,
                              capture_output=True, text=True).stdout

    def test_session_start_enables_the_hooks_in_a_fresh_clone(self):
        self.git("config", "--unset", "core.hooksPath")
        self.assertIn("enabled this repo's git hooks", self.enable())
        self.assertEqual(self.git("config", "core.hooksPath").stdout.strip(), ".factory/hooks")
        self.assertEqual(self.enable(), "")

    def test_session_start_never_overrides_another_hook_manager(self):
        self.git("config", "core.hooksPath", ".husky")
        self.assertIn("don't run in this clone", self.enable())
        self.assertEqual(self.git("config", "core.hooksPath").stdout.strip(), ".husky")

    def test_session_start_is_silent_where_the_factory_isnt_set_up(self):
        os.remove(self.root / ".factory/hooks/factory-git-guard.py")
        self.git("config", "--unset", "core.hooksPath")
        self.assertEqual(self.enable(), "")
        self.assertNotEqual(self.git_in(self.root, "config", "core.hooksPath").returncode, 0)


if __name__ == "__main__":
    unittest.main()
