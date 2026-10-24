---
name: guardrails
description: Turn docs/architecture.md into executable guardrails — boundary tests (with a ratchet for existing violations), Claude Code hooks and permissions, and CLAUDE.md with the codebase's real conventions. Use after the skeleton or baseline, or after the architecture changes.
disable-model-invocation: true
---

# Guardrails

Architecture that lives only in a document drifts. Encode every rule as a check that goes **red** when broken, so agent-written PRs stay inside the architecture.

## Steps

1. **Boundary tests.** Encode every rule under "Dependency rules" in `docs/architecture.md` with the stack's tool: dependency-cruiser or eslint-plugin-boundaries for TypeScript, import-linter for Python, ArchUnit for the JVM, depguard for Go. Wire it into the lint or test command so CI runs it.
2. **Ratchet existing violations** (`existing` mode). Existing code usually breaks some rules already. Record today's violations as a baseline file the tool reads: dependency-cruiser's known-violations, import-linter's `ignore_imports`, ArchUnit's `FreezingArchRule`, or the equivalent. The check then fails only on **new** violations. Record the count in `docs/architecture.md` under "Known violations". The count may only go down: when a change removes a violation, remove it from the baseline file too.
3. **Prove each rule red.** Add a temporary import that breaks the rule in a new place, confirm the check fails, then remove the import and confirm it passes.
4. **Claude Code hooks** in `.claude/settings.json`, with their scripts in `.claude/hooks/`. Merge into any existing settings.
   - `PostToolUse` on `Edit|Write`: format and lint the edited file, and return the errors to Claude.
   - `PreToolUse` on `Bash`: `python3 -I .claude/hooks/factory-env-guard.py`. Read denies don't cover Bash, so this refuses commands that name a `.env` file, and recursive searches through a tree holding one unless they exclude it.
   - `Stop`: `.claude/hooks/factory-stop-tests.sh <test command>`. It returns failures to Claude, skips the run when `stop_hook_active` is set or the active job is `building` (build's red steps fail on purpose, and its own gate runs the suite), and waits for any other test run first. Set the hook's `timeout` in seconds above the suite's run time. When `docs/baseline.md` lists flaky tests, exclude the quarantined ones in the test command.

   Copy the scripts from `${CLAUDE_PLUGIN_ROOT}/scripts/hooks/` into `.claude/hooks/` with a `factory-` prefix: `env-guard.py`, `stop-tests.sh` and `test-lock.sh`. Write the test command in `CLAUDE.md` as `.claude/hooks/factory-test-lock.sh <test command>`, so every run takes the same lock: suites that share a test database or port fail when two runs overlap.
5. **Permissions** in the same file. Allow the build, lint, test and `git` commands. Show the user the result before writing it. Deny:
   - force pushes and hard resets: `Bash(git push --force:*)`, `Bash(git push -f:*)`, `Bash(git reset --hard:*)`
   - skipping hooks: `Bash(git commit --no-verify:*)`, `Bash(git push --no-verify:*)`
   - reading secrets: `Read(./**/.env)`, `Read(./**/.env.local)`, `Read(./**/.env.*.local)`, `Read(./**/.env.production)`, `Read(./**/*.pem)`, `Read(./**/*.key)`, plus `Read(./**/.env.<name>)` for each other `.env.<name>` in the repo (`git ls-files -co --exclude-standard` and `find . -name '.env.*'`).
     Never deny `.env.*` as a whole: it hides `.env.example`, `.env.sample` and `.env.template`, which document the variables without values, and a deny can't be overridden by an allow.
   - `Bash(rm -rf:*)`, plus anything the team adds
5a. **Git hooks.** Install `${CLAUDE_PLUGIN_ROOT}/scripts/hooks/pre-commit` and `pre-push` into the repo's hooks directory (`git rev-parse --git-path hooks`), with `${CLAUDE_PLUGIN_ROOT}/scripts/hooks/protected.sh` beside them as `factory-protected.sh`. They block commits and pushes on the default branch, and on any branch added with `git config --add factory.protected '<pattern>'`, which includes the target branch from `.factory/config.md`. Creating a protected branch on the remote is allowed when it adds no unpushed commits. Ask the user which other branches to protect, such as `release/*`.
   - If a hook of that name already exists, or `core.hooksPath` points at a hook manager (husky, lefthook), show the factory hook and ask how to combine them, rather than overwriting.
   - For a solo repo where the user wants to commit straight to the default branch, they can opt out with `git config factory.allowDefaultBranch true`.
   - Hooks guard one clone, and `--no-verify` skips them, so the real control is branch protection on the hosting service. Check whether the target branch requires a pull request, a reviewer, and a passing CI build (for GitHub, `gh api repos/{owner}/{repo}/branches/<branch>/protection`). Report any gaps, with the exact settings to add. Changing them is the user's call.
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
- `grep -rn PASSWORD .` is refused by the env guard when the repo holds a `.env` file.
- A trial commit on the default branch is refused by the pre-commit hook (unless the user opted out), and branch-protection gaps are reported.
- `existing` mode: the user has reviewed the conventions in `CLAUDE.md`.
- Every command listed in `CLAUDE.md` runs successfully.
