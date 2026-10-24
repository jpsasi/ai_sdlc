#!/usr/bin/env python3
"""Factory: PreToolUse hook on Bash that keeps .env secrets out of the transcript.

Read(./.env) permissions don't cover Bash, so this refuses a command that names a
secrets file (.env, .env.local, deploy/.env ...; not .env.example), or that searches
recursively through a tree holding one without excluding it. Exit 2 blocks the call.
"""
import json
import os
import re
import sys

SAFE_SUFFIXES = ("example", "sample", "template", "dist")
SECRET = re.compile(r"(?<![\w.-])(?:[\w./~-]*/)?\.env(?:\.[\w.-]+)?(?![\w.-])")
# Arguments that exclude files from a search: --exclude=.env*, -g '!.env*', -not -name .env ...
EXCLUSION = re.compile(r"""(?:--exclude(?:-dir)?[=\s]|--glob[=\s]+['"]?!|-g\s*['"]?!|(?:-not|!)\s+-i?(?:name|path)\s+)['"]?[^\s'"]*['"]?""")
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build", ".next", "target"}


def is_secret(name):
    return name == ".env" or (name.startswith(".env.") and name.rsplit(".", 1)[-1] not in SAFE_SUFFIXES)


def names_secret(command):
    return any(is_secret(m.group(0).rsplit("/", 1)[-1]) for m in SECRET.finditer(command))


def recursive_search(command):
    for part in re.split(r"[|;&]+", command):
        words = part.split()
        if not words:
            continue
        tool, flags = os.path.basename(words[0]), words[1:]
        if tool in ("grep", "egrep", "fgrep") and any(
                f == "--recursive" or re.fullmatch(r"-[A-Za-z]*[rR][A-Za-z]*", f) for f in flags):
            return True
        if tool in ("rg", "ag") and any(f in ("--hidden", "-uu", "-uuu", "-.") for f in flags):
            return True  # both skip dotfiles unless told otherwise
        if tool == "find" and re.search(r"-exec|-ok\b", part) and not re.search(r"-i?(name|path|regex)\b", part):
            return True
    return tool_after_find_pipe(command)


def tool_after_find_pipe(command):
    m = re.search(r"\bfind\b([^|]*)\|\s*xargs\b", command)
    return bool(m) and not re.search(r"-i?(name|path|regex)\b", m.group(1))


def secret_file_under(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            if is_secret(name):
                return os.path.relpath(os.path.join(dirpath, name), root)
    return None


def main():
    try:
        command = json.load(sys.stdin).get("tool_input", {}).get("command", "")
    except (ValueError, AttributeError):
        return 0
    searched = EXCLUSION.sub(" ", command)
    if names_secret(searched):
        print("factory: this command names a .env secrets file, and its output would land in the transcript. "
              "Use .env.example for the variable names; if the values are really needed, ask the user to run it.",
              file=sys.stderr)
        return 2
    excludes_secrets = any(".env" in m.group(0) for m in EXCLUSION.finditer(command))
    if recursive_search(command) and not excludes_secrets:
        found = secret_file_under(".")
        if found:
            print(f"factory: this recursive search would read {found}, which holds secrets. "
                  "Exclude it: grep --exclude='.env*', rg -g '!.env*', or find ... -not -name '.env*'.",
                  file=sys.stderr)
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
