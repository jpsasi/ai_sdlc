---
name: guardrails
description: Turn docs/architecture.md into executable guardrails — boundary tests (with a ratchet for existing violations), security scans, git and Claude Code hooks, permissions, and CLAUDE.md with the codebase's real conventions. Use after the skeleton or baseline, or after the architecture changes.
disable-model-invocation: true
---

# Guardrails

Architecture that lives only in a document drifts. Encode every rule as a check that goes **red** when broken, so agent-written PRs stay inside the architecture.

## Steps

1. **Boundary tests.** Encode every rule under "Dependency rules" in `docs/architecture.md` with the stack's tool: dependency-cruiser or eslint-plugin-boundaries for TypeScript, import-linter for Python, ArchUnit for the JVM, depguard for Go. Wire it into the lint or test command so CI runs it.
2. **Ratchet existing violations** (`existing` mode). Existing code usually breaks some rules already. Record today's violations as a baseline file the tool reads: dependency-cruiser's known-violations, import-linter's `ignore_imports`, ArchUnit's `FreezingArchRule`, or the equivalent. The check then fails only on **new** violations. Record the count in `docs/architecture.md` under "Known violations". The count may only go down: when a change removes a violation, remove it from the baseline file too.
3. **Prove each rule red.** Add a temporary import that breaks the rule in a new place, confirm the check fails, then remove the import and confirm it passes.
3a. **Security scans**, by `${CLAUDE_PLUGIN_ROOT}/shared/SECURITY.md`. Every repo gets them, with or without a remote: the scanners run locally, and review needs them on every job.
   - `.factory/config.md` needs its Target branch for the scans' `<base>`: when the file or the line is missing, ask for it by step 3 of Setup in `${CLAUDE_PLUGIN_ROOT}/shared/CONFIG.md`, and write just that line. The rest of Setup waits for the first ship.
   - Add the four scan rows to the Commands table of `.factory/config.md`: the defaults, or the team's own tools if the user names them. Check each one runs, and give the install command for any that's missing.
   - Check the Dependencies command sees every dependency file in the repo: osv-scanner prints a "Scanned <file> ... found <n> packages" line for each. A build file it doesn't list, or "No package sources found", means the dependencies aren't pinned: fix it by the stack table in `SECURITY.md`, which changes the project, so agree it with the user first. Write `none` only when the repo has no dependencies.
   - Run the Secrets, Dependencies and Code scan commands once over the whole repo and its history: the Secrets command without its `--log-opts`, and the Code scan without its `--baseline-commit`. Report what's already there, with counts. These are the target branch's known findings: they don't block jobs, but tell the user about every secret found, since it needs rotating.
   - Write the Security section of `.factory/config.md`. Ask for the Expert group, as step 7 of Setup in `CONFIG.md` does. Propose the sensitive paths from `docs/architecture.md`: the modules that handle sign-in, permissions, money, personal data and external input. Let the user confirm them.
4. **Claude Code hooks** in `.claude/settings.json`, with their scripts in `.claude/hooks/`. Merge into any existing settings.
   - `PostToolUse` on `Edit|Write`: format and lint the edited file, and return the errors to Claude.
   - `Stop`: run the test command, and exit 2 with the failure output when it fails. Exit 0 when the input's `stop_hook_active` is true, so a failure can't loop forever. When `docs/baseline.md` lists flaky tests, exclude the quarantined ones.
5. **Permissions** in the same file. Allow the build, lint, test and `git` commands. Show the user the result before writing it. Deny:
   - force pushes and hard resets: `Bash(git push --force:*)`, `Bash(git push -f:*)`, `Bash(git reset --hard:*)`
   - skipping hooks: `Bash(git commit --no-verify:*)`, `Bash(git push --no-verify:*)`
   - reading secrets: `Read(./.env)`, `Read(./.env.*)`, `Read(./**/*.pem)`, `Read(./**/*.key)`
   - `Bash(rm -rf:*)`, plus anything the team adds
5a. **Git hooks.** Install `${CLAUDE_PLUGIN_ROOT}/scripts/hooks/pre-commit` and `pre-push` into the repo's hooks directory (`git rev-parse --git-path hooks`), with `${CLAUDE_PLUGIN_ROOT}/scripts/hooks/protected.sh` beside them as `factory-protected.sh`. They block commits and pushes on the default branch, and on any branch added with `git config --add factory.protected '<pattern>'`. Ask the user which other branches to protect, such as `release/*`. The pre-commit hook also runs the Secrets (staged) command from `.factory/config.md`, and refuses a commit it finds a secret in, or when the scanner or its row is missing. On a branch without the config, it only warns.
   - If a hook of that name already exists, or `core.hooksPath` points at a hook manager (husky, lefthook), show the factory hook and ask how to combine them, rather than overwriting.
   - For a solo repo where the user wants to commit straight to the default branch, they can opt out with `git config factory.allowDefaultBranch true`.
   - Hooks guard one clone, and `--no-verify` skips them, so the real control is branch protection on the hosting service. Check whether the default branch requires a pull request, a reviewer, and a passing CI build (for GitHub, `gh api repos/{owner}/{repo}/branches/<branch>/protection`). Report any gaps, with the exact settings to add. Changing them is the user's call.
6. **Conventions** (`existing` mode). Dispatch the `factory:architect` subagent to describe how the code is *actually* written, each item with one or two example file paths:
   - naming of files, types and functions
   - folder patterns inside a module
   - error handling and logging
   - test style and test locations
   - how config and dependencies are wired

   Where the codebase is inconsistent, record the pattern used in the most recently changed code as the one to follow. Review the list with the user.
7. **`CLAUDE.md`.** Keep it short and point rather than copy. Merge with any existing `CLAUDE.md` rather than replacing it.
   - the build, lint and test commands
   - one-line pointers to `docs/product.md`, `CONTEXT.md`, `docs/architecture.md`, `docs/adr/` and `openspec/specs/` (current behaviour; changed only through a change's deltas), plus `docs/baseline.md` in `existing` mode
   - the conventions from step 6, in `existing` mode: "write code the way the surrounding code is written"
   - in `existing` mode, a module rated `bare` gets characterization tests before it is changed
   - the definition of done: tests, lint and boundary checks green, with no new violations; capability traced to its `P-n`

## Done check

- Every dependency rule has been demonstrated red on a new violation, then green.
- `existing` mode: the violation baseline exists, and its count is recorded in `docs/architecture.md`.
- An edit triggers the formatter hook. A deliberately failing test blocks the Stop hook. Revert both.
- A trial commit on the default branch is refused by the pre-commit hook (unless the user opted out), and branch-protection gaps are reported.
- The scan rows run, and the user has the repo's known findings. The Dependencies command lists every dependency file, or is `none` in a repo with no dependencies. A trial commit holding a fake key (`AWS_ACCESS_KEY_ID = "AKIAZ3MPLQ7RT4XW2NV6"`; gitleaks ignores AWS's documented example key) is refused by the pre-commit hook. Revert it.
- The Security section names an Expert group that exists, and the sensitive paths the user confirmed.
- `existing` mode: the user has reviewed the conventions in `CLAUDE.md`.
- Every command listed in `CLAUDE.md` runs successfully.
