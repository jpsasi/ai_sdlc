#!/usr/bin/env python3
"""Factory git guard: the checks behind the git hooks in .factory/hooks/.

  git-guard.py pre-commit                 branch rules, migration numbers, then the secrets scan
  git-guard.py pre-merge-commit           migration numbers, after merging the target branch
  git-guard.py commit-msg <message file>  banned patterns, test weakening
  git-guard.py pre-push                   branch rules for the refs being pushed (refs on stdin)

The rules come from .factory/config.md: the Target branch line, the Branches, Migrations and
Commit message bans tables, and the Secrets (staged) row of the Commands table; branches added with
git config --add factory.protected '<pattern>' are protected too. The guard fails closed: when it can't decide (no target ref in the
clone, an unreadable config, a crash), it refuses and says why. Exit 0 allows, 1 refuses.
"""
import fnmatch
import re
import subprocess
import sys
from pathlib import Path

CONFIG = Path(".factory/config.md")
APPROVAL = re.compile(r"^Test-change-approved-by: *\S", re.MULTILINE)

# Kept in step with factory.py's TEST_PATH and NOT_TESTS.
TEST_PATH = re.compile(r"(^|/)(tests?|spec|specs|__tests__)/|(^|/)test_[^/]*$|_test\.[a-z]+$|\.(test|spec)\.[a-z]+$")
NOT_TESTS = ("docs/", "openspec/", ".factory/")
NOISE = re.compile(r"^\s*(import\s|from\s\S+\simport\s|#(?!\[)|//|/?\*)")
ASSERTION = re.compile(r"\bassert|\bexpect\s*\(|\bverify\s*\(|\bfail\s*\(|\bshould\b|\.to[A-Z]\w*\s*\("
                       r"|\bt\.(Error|Fatal)|\brequire\.\w+\s*\(")
SKIP = re.compile(r"@Disabled|@Ignore\b|\bassume\w*\s*\(|Assumptions\.|\.(skip|only)\s*\(|\bx(it|describe|test)\s*\("
                  r"|pytest\.mark\.(skip|xfail)|unittest\.skip|\bt\.Skip|#\[ignore\]")
TEST_DEF = re.compile(r"@(Test|ParameterizedTest|RepeatedTest|TestFactory|TestTemplate)\b|^\s*(async\s+)?def test"
                      r"|^\s*(it|test)\s*\(|^\s*func Test|#\[test\]")


class Refuse(Exception):
    pass


def git(*args, check=True):
    result = subprocess.run(["git", *args], capture_output=True, text=True)
    if check and result.returncode != 0:
        raise Refuse(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


# ---------- config ----------

def config_text():
    try:
        return CONFIG.read_text(encoding="utf-8") if CONFIG.is_file() else ""
    except (OSError, UnicodeDecodeError) as e:
        raise Refuse(f"can't read {CONFIG}: {e}") from None


def table(text, heading):
    """Rows of the table under '## <heading>', as lists of cells, without the header row."""
    rows, inside = [], False
    for line in text.split("\n"):
        if line.startswith("## "):
            inside = line[3:].strip().lower() == heading.lower()
            continue
        if inside and line.startswith("|") and not re.match(r"^\|[\s|:-]+\|?$", line):
            cells = re.split(r"(?<!\\)\|", line.strip().strip("|"))  # a cell writes | as \|
            rows.append([c.strip().strip("`").replace("\\|", "|") for c in cells])
    return rows[1:]


def strip_prefix(text, prefix):
    """str.removeprefix, which needs Python 3.9; the README promises 3.8."""
    return text[len(prefix):] if text.startswith(prefix) else text


def target_branch(text):
    m = re.search(r"^Target branch: *(\S+)", text, re.MULTILINE)
    if m:
        return m.group(1)
    head = git("symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD", check=False).strip()
    return strip_prefix(head, "origin/") or None


def default_branch():
    head = git("symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD", check=False).strip()
    return strip_prefix(head, "origin/") or git("config", "--get", "init.defaultBranch", check=False).strip() or "main"


def branch_rules(text):
    """{pattern: rule}. The default and target branches are always at least protected."""
    rules = {}
    for row in table(text, "Branches"):
        if len(row) >= 2 and row[0] and row[1].lower() in ("protected", "frozen", "retired"):
            rules[row[0]] = row[1].lower()
    extra = git("config", "--get-all", "factory.protected", check=False).split("\n")
    for name in (default_branch(), target_branch(text), *extra):
        if name.strip():
            rules.setdefault(name.strip(), "protected")
    return rules


def rule_for(branch, rules):
    found = [rules[p] for p in rules if fnmatch.fnmatchcase(branch, p)]
    for rule in ("retired", "frozen", "protected"):
        if rule in found:
            return rule
    return None


def target_ref(text):
    target = target_branch(text)
    if not target:
        raise Refuse("no Target branch in .factory/config.md, and no origin/HEAD: can't tell what to check against")
    ref = f"refs/remotes/origin/{target}"
    if git("rev-parse", "--verify", "--quiet", ref, check=False).strip() == "":
        raise Refuse(f"origin/{target} isn't in this clone, so the check can't run. Run: git fetch origin {target}")
    return ref, f"origin/{target}"


# ---------- branch rules ----------

WHY = {
    "protected": "changes only through a pull request",
    "frozen": "is frozen: nothing new goes on it",
    "retired": "is retired: don't use it",
}


def check_branch(text):
    branch = git("symbolic-ref", "--quiet", "--short", "HEAD", check=False).strip()
    if not branch:
        return  # detached HEAD: a rebase or bisect in progress
    rule = rule_for(branch, branch_rules(text))
    if rule == "protected" and branch == default_branch() and \
            git("config", "--get", "factory.allowDefaultBranch", check=False).strip() == "true":
        return
    if rule:
        raise Refuse(f"'{branch}' {WHY[rule]}. Commit on a work branch: git switch -c factory/<name>")


def check_push(text, lines):
    rules = branch_rules(text)
    for line in lines:
        parts = line.split()
        if len(parts) != 4:
            continue
        local_sha, remote_ref, remote_sha = parts[1], parts[2], parts[3]
        branch = strip_prefix(remote_ref, "refs/heads/")
        rule = rule_for(branch, rules)
        if not rule:
            continue
        creating = set(remote_sha) == {"0"} and set(local_sha) != {"0"}
        if rule == "protected" and creating and git("branch", "-r", "--contains", local_sha, check=False).strip():
            continue  # creates the branch on the remote, with no unpushed commits
        raise Refuse(f"push to '{branch}' is blocked: it {WHY[rule]}. Open a pull request instead.")


# ---------- migrations ----------

def version_pattern(name):
    """'V<n>__*.sql' -> a regex capturing the version."""
    out = ""
    for part in re.split(r"(<n>|\*)", name):
        out += r"(\d+(?:[._]\d+)*)" if part == "<n>" else ".*" if part == "*" else re.escape(part)
    return re.compile(f"^{out}$")


def version_key(v):
    return tuple(int(x) for x in re.split(r"[._]", v))


def check_migrations(text):
    folders = [(r[0].rstrip("/"), r[1]) for r in table(text, "Migrations") if len(r) >= 2 and r[0] and r[1]]
    if not folders:
        return
    ref, shown = target_ref(text)
    problems = []
    for folder, name in folders:
        pattern = version_pattern(name)
        shipped = set(git("ls-tree", "--name-only", f"{ref}:{folder}", check=False).split("\n")) - {""}
        staged = {Path(p).name for p in git("ls-files", "--", f"{folder}/").split("\n") if p}
        for line in git("diff", "--cached", "--name-status", "--no-renames", ref, "--", f"{folder}/").splitlines():
            status, path = line.split("\t", 1)
            if Path(path).name in shipped and status in ("M", "D"):
                problems.append(f"{path} is already on {shown}. Shipped migrations never change: add a new one instead.")
        versions = {}
        for f in shipped:
            m = pattern.match(f)
            if m:
                versions.setdefault(m.group(1), []).append(f)
        top = max((version_key(v) for v in versions), default=None)
        top_name = ".".join(map(str, top)) if top else "none"
        for f in sorted(staged - shipped):
            m = pattern.match(f)
            if not m:
                problems.append(f"{folder}/{f} doesn't match the migration name {name}.")
                continue
            v = m.group(1)
            if top is not None and version_key(v) <= top:
                problems.append(f"{folder}/{f} has version {v}, but {shown} is already at {top_name}. "
                                f"Renumber it above {top_name}.")
            versions.setdefault(v, []).append(f)
        for v, files in sorted(versions.items()):
            if len(files) > 1:
                problems.append(f"version {v} is used by more than one migration: {', '.join(sorted(files))}")
    if problems:
        raise Refuse("migrations:\n  - " + "\n  - ".join(problems) +
                     f"\n  ({shown} is the local ref; run git fetch first if it may be stale)")


# ---------- commit message ----------

def check_message(text, message):
    body = "\n".join(line for line in message.split("\n") if not line.startswith("#"))
    lines = [line for line in body.split("\n") if line.strip()]
    if not lines:
        return  # git refuses an empty message itself
    merging = git("rev-parse", "-q", "--verify", "MERGE_HEAD", check=False).strip()
    problems = []
    for row in table(text, "Commit message bans"):
        if row and row[0]:
            try:
                hit = re.search(row[0], body)
            except re.error as e:
                raise Refuse(f"bad pattern '{row[0]}' in the Commit message bans table: {e}") from None
            if hit:
                why = row[1] if len(row) > 1 and row[1] else "banned in this repo"
                problems.append(f"'{hit.group(0)}' is not allowed in commit messages: {why}")
    if problems:
        raise Refuse("commit message:\n  - " + "\n  - ".join(problems))
    if not merging and not APPROVAL.search(body):
        weakened = weakened_tests(text)
        if weakened:
            raise Refuse("this commit weakens tests that are already on the target branch:\n  - " +
                         "\n  - ".join(weakened) +
                         "\nOnly a person can approve that. Ask them, then add the trailer "
                         "'Test-change-approved-by: <their name>' with the reason in the message body.")


def on_ref(ref, path):
    return subprocess.run(["git", "cat-file", "-e", f"{ref}:{path}"], capture_output=True).returncode == 0


def is_test(path):
    return not path.startswith(NOT_TESTS) and bool(TEST_PATH.search(path))


def weakened_tests(text):
    if not git("rev-parse", "-q", "--verify", "HEAD", check=False).strip():
        return []
    ref, _ = target_ref(text)
    found = []
    for line in git("diff", "--cached", "--name-status", "-M", "HEAD").splitlines():
        status, *paths = line.split("\t")
        path = paths[0]
        if not is_test(path) or not on_ref(ref, path):
            continue  # not a test, or written on this branch: still the job's own work
        if status == "D":
            found.append(f"{path}: deleted")
            continue
        diff = git("diff", "--cached", "-U0", "-M", "HEAD", "--", *paths)
        removed = [l[1:] for l in diff.split("\n") if l.startswith("-") and not l.startswith("---")]
        added = [l[1:] for l in diff.split("\n") if l.startswith("+") and not l.startswith("+++")]
        removed = [l for l in removed if not NOISE.match(l)]
        added = [l for l in added if not NOISE.match(l)]
        if any(ASSERTION.search(l) for l in removed):
            found.append(f"{path}: changes or removes an assertion")
        if any(SKIP.search(l) for l in added):
            found.append(f"{path}: skips, disables or narrows tests")
        if sum(bool(TEST_DEF.search(l)) for l in removed) > sum(bool(TEST_DEF.search(l)) for l in added):
            found.append(f"{path}: removes a test")
    return found


# ---------- secrets ----------

def check_secrets(text):
    """The Commands table's Secrets (staged) command, run on what is about to be committed."""
    run = next((row[1] for row in table(text, "Commands")
                if len(row) > 1 and row[0].lower() == "secrets (staged)" and row[1]), None)
    if not run:
        raise Refuse("the Commands table of .factory/config.md has no Secrets (staged) command, so the commit "
                     "is refused. Run /factory:guardrails to add the scans.")
    result = subprocess.run(run, shell=True, capture_output=True, text=True)
    if result.returncode == 127:
        raise Refuse(f"the secrets scan can't run ({run.split()[0]} is missing), so the commit is refused. "
                     f"Install it, or ask a person.")
    if result.returncode != 0:
        found = (result.stdout + result.stderr).strip()
        raise Refuse(f"the secrets scan found a secret in the staged changes. Remove it, and rotate it if it "
                     f"was ever real.\n{found}")


# ---------- entry ----------

def main(argv):
    hook = argv[1] if len(argv) > 1 else ""
    try:
        text = config_text()
        if hook == "pre-commit":
            check_branch(text)
            check_migrations(text)
            check_secrets(text)
        elif hook == "pre-merge-commit":
            check_migrations(text)
        elif hook == "commit-msg":
            check_message(text, Path(argv[2]).read_text(encoding="utf-8", errors="replace"))
        elif hook == "pre-push":
            check_push(text, sys.stdin.read().splitlines())
        else:
            raise Refuse(f"unknown hook '{hook}'")
    except Refuse as e:
        print(f"factory: {e}", file=sys.stderr)
        return 1
    except Exception as e:  # fail closed: a guard that can't decide refuses
        print(f"factory: the {hook} guard couldn't run ({type(e).__name__}: {e}), so it refuses. "
              f"Fix the cause, or ask a person.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
