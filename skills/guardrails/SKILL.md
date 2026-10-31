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
   - The scans' `<base>` needs the Target branch in `.factory/config.md`, which foundation sets. When it's missing, ask for it by step 3 of Setup in `${CLAUDE_PLUGIN_ROOT}/shared/CONFIG.md`, and write just that line.
   - Add the four scan rows to the Commands table of `.factory/config.md`: the defaults, or the team's own tools if the user names them. Check each one runs, and give the install command for any that's missing.
   - Check the Dependencies command sees every dependency file in the repo: osv-scanner prints a "Scanned <file> ... found <n> packages" line for each. A build file it doesn't list, or "No package sources found", means the dependencies aren't pinned: fix it by the stack table in `SECURITY.md`, which changes the project, so agree it with the user first. Write `none` only when the repo has no dependencies.
   - Run the Secrets, Dependencies and Code scan commands once over the whole repo and its history: the Secrets command without its `--log-opts`, and the Code scan without its `--baseline-commit`. Report what's already there, with counts. These are the target branch's known findings: they don't block jobs, but tell the user about every secret found, since it needs rotating.
   - Write the Security section of `.factory/config.md`. Ask for the Expert group, as step 7 of Setup in `CONFIG.md` does. Propose the sensitive paths from `docs/architecture.md`: the modules that handle sign-in, permissions, money, personal data and external input. Let the user confirm them. They decide which jobs get a security flag, so ask in either Approvals mode, together with the Expert group, in one round.
4. **Claude Code hooks** in `.claude/settings.json`, with their scripts in `.claude/hooks/`. Merge into any existing settings.
   - `PostToolUse` on `Edit|Write`: format and lint the edited file, and return the errors to Claude.
   - `PreToolUse` on `Bash`: `python3 -I .claude/hooks/factory-env-guard.py`. Read denies don't cover Bash, so this refuses commands that name a `.env` file, and recursive searches through a tree holding one unless they exclude it.
   - `Stop`: `.claude/hooks/factory-stop-tests.sh <test command>`. It returns failures to Claude, skips the run when `stop_hook_active` is set or the active job is `building`, `reviewing` or `reviewed` (build's red steps fail on purpose, and those stages run the suite at their own gates), and waits for any other test run first. Set the hook's `timeout` in seconds above the suite's run time. When `docs/baseline.md` lists flaky tests, exclude the quarantined ones in the test command.

   Copy the scripts from `${CLAUDE_PLUGIN_ROOT}/scripts/hooks/` into `.claude/hooks/` with a `factory-` prefix: `env-guard.py`, `stop-tests.sh` and `test-lock.sh`. Write the test command in `CLAUDE.md` as `.claude/hooks/factory-test-lock.sh <test command>`, so every run takes the same lock: suites that share a test database or port fail when two runs overlap.
5. **Permissions** in the same file. Allow the build, lint, test and `git` commands. Show the user the result before writing it (with `Approvals: auto`, write it, and list what you allowed). Deny:
   - force pushes and hard resets: `Bash(git push --force:*)`, `Bash(git push -f:*)`, `Bash(git reset --hard:*)`
   - skipping hooks: `Bash(git commit --no-verify:*)`, `Bash(git push --no-verify:*)`
   - reading secrets: `Read(./**/.env)`, `Read(./**/.env.local)`, `Read(./**/.env.*.local)`, `Read(./**/.env.production)`, `Read(./**/*.pem)`, `Read(./**/*.key)`, plus `Read(./**/.env.<name>)` for each other `.env.<name>` in the repo (`git ls-files -co --exclude-standard` and `find . -name '.env.*'`).
     Never deny `.env.*` as a whole: it hides `.env.example`, `.env.sample` and `.env.template`, which document the variables without values, and a deny can't be overridden by an allow.
   - `Bash(rm -rf:*)`, plus anything the team adds
5a. **Git hooks**, committed in `.factory/hooks/`, so every clone runs the same ones. Copy `pre-commit`, `pre-merge-commit`, `commit-msg` and `pre-push` from `${CLAUDE_PLUGIN_ROOT}/scripts/hooks/`, with `git-guard.py` beside them as `factory-git-guard.py`. Then run `git config core.hooksPath .factory/hooks`. That setting lives in each clone; the plugin's SessionStart hook sets it in any clone where it's missing, and `CLAUDE.md` tells people without the plugin. The rules come from `.factory/config.md`, by `${CLAUDE_PLUGIN_ROOT}/shared/CONFIG.md`:
   - **Branches:** no commits on, and no pushes to, the default branch, the target branch, any branch in the Branches table, whether `protected`, `frozen` or `retired`, or any branch added with `git config --add factory.protected '<pattern>'`. Creating a protected branch on the remote is allowed when it adds no unpushed commits. Ask the user which other branches to list, such as `release/*`, and which are frozen or retired. A solo repo that commits straight to the default branch can opt out with `git config factory.allowDefaultBranch true`.
   - **Migrations**, for each folder in the Migrations table: a new file matches its name pattern and takes a version above the highest on the target branch, no two files share a version, and a migration already on the target branch never changes. The check runs again when a merge brings in the target branch.
   - **Tests:** a commit that changes an assertion in, skips, or removes a test already on the target branch needs the trailer `Test-change-approved-by: <name>`. Tests written on the job's own branch change freely.
   - **Commit message bans:** nothing in the Commit message bans table, such as a ticket system's id the team mustn't leak.
   - **Secrets:** the pre-commit hook runs the Secrets (staged) command, and refuses a commit it finds a secret in, or when the scanner or its row is missing.
   - **Fail closed:** when a hook can't decide, because the target branch isn't fetched, the config can't be read, or `python3` is missing, it refuses and says why.
   - **Moving from per-clone hooks:** a repo set up before this has factory hooks in `git rev-parse --git-path hooks` (`pre-commit`, `pre-push`, `factory-protected.sh`). Setting `core.hooksPath` makes git ignore them: delete them, and write each `git config factory.protected` pattern into the Branches table, so every clone gets it.
   - If `core.hooksPath` already points at a hook manager (husky, lefthook), or the repo has other git hooks, show the factory hooks and ask how to combine them, rather than overwriting. The SessionStart hook never overrides another `core.hooksPath`; it only says so.
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
   - one line for anyone working without the plugin: run `git config core.hooksPath .factory/hooks` once per clone, so the git hooks run
   - one-line pointers to `docs/product.md`, `CONTEXT.md`, `docs/architecture.md`, `docs/adr/` and `openspec/specs/` (current behaviour; changed only through a change's deltas), plus `docs/baseline.md` in `existing` mode
   - the conventions from step 6, in `existing` mode: "write code the way the surrounding code is written"
   - in `existing` mode, a module rated `bare` gets characterization tests before it is changed
   - the definition of done: tests, lint and boundary checks green, with no new violations; capability traced to its `P-n`

## Done check

- Every dependency rule has been demonstrated red on a new violation, then green.
- `existing` mode: the violation baseline exists, and its count is recorded in `docs/architecture.md`.
- An edit triggers the formatter hook. A deliberately failing test blocks the Stop hook. Revert both.
- `grep -rn PASSWORD .` is refused by the env guard when the repo holds a `.env` file.
- With `core.hooksPath` set to `.factory/hooks`: a trial commit on the target branch is refused (unless the user opted out), and so is a migration numbered at or below the target branch's highest. Revert them. Branch-protection gaps are reported.
- The scan rows run, and the user has the repo's known findings. The Dependencies command lists every dependency file, or is `none` in a repo with no dependencies. A trial commit holding a fake key (`AWS_ACCESS_KEY_ID = "AKIAZ3MPLQ7RT4XW2NV6"`; gitleaks ignores AWS's documented example key) is refused by the pre-commit hook. Revert it.
- The Security section names an Expert group that exists, and the sensitive paths the user confirmed.
- `existing` mode: the user has reviewed the conventions in `CLAUDE.md`.
- Every command listed in `CLAUDE.md` runs successfully.
