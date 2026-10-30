# Factory

A software factory plugin for Claude Code. It turns product requirements into an architecture, a backlog, and reviewed, test-first changes, one job at a time, with a person approving at each key point. It's self-contained: nothing else needs installing.

## Install

In Claude Code, from the repo you want to use the factory in:

```
/plugin marketplace add jpsasi/ai_sdlc
/plugin install factory@jpsasi
```

The marketplace is `jpsasi` and the plugin is `factory`, so commands are `/factory:<name>`. The repo is private: `git clone git@github.com:jpsasi/ai_sdlc.git` must work on your machine first (SSH key or `gh auth login`). Pull later changes with `/plugin marketplace update jpsasi`.

From a local clone instead of GitHub: `/plugin marketplace add /path/to/ai_sdlc`, then the same install.

To try it for one session without installing: `claude --plugin-dir /path/to/ai_sdlc`.

To have a product repo offer the plugin to everyone who opens it, commit this in its `.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "jpsasi": { "source": { "source": "github", "repo": "jpsasi/ai_sdlc" } }
  },
  "enabledPlugins": { "factory@jpsasi": true }
}
```

## Needs

- `git`, in the product repo
- `gh` (GitHub) or `az` with the `azure-devops` extension (Azure Repos), signed in
- Python 3.8 or newer, for the validator (`scripts/factory.py`)
- The security scanners, or the team's own: `gitleaks`, `osv-scanner` and `semgrep` by default (`brew install gitleaks osv-scanner semgrep`)
- The Atlassian connector, only when requirements come from Confluence or tickets go to Jira

## How it works

```
foundation ─▶ backlog of tickets
                  │
       (task) ─▶ go:  next ─▶ spec ─▶ plan ─▶ build ─▶ review ─▶ ship ─▶ PR
                                                                         │
                     person merges ─▶ ship again ─▶ deployed to dev ─▶ promote ─▶ QA, …
```

1. **Once per product:** run `/factory:foundation <source>`. It works out the product, domain, decisions, architecture, skeleton (new code) or baseline (existing code), guardrails and backlog, one step at a time, each approved by you.
2. **Release tickets:** a ticket is ready for the factory when someone listed in `.factory/trusted.md` adds the `factory-ready` label (or, with the local tracker, sets the backlog row to `ready`). `/factory:task` turns a bug or task from chat into such a ticket.
3. **Per ticket:** run `/factory:go`. It claims the top ready ticket, then specs, plans, builds, reviews and ships it, ending with an open PR.
4. **After a person merges the PR:** run `/factory:ship <KEY>` again. It deletes the branch, waits for the deploy to the first environment, and moves the ticket on.
5. **When testing passes:** run `/factory:promote` to move everything from one environment to the next, such as dev to QA.

**Where it stops for a person:** approving each foundation step, approving the proposal and plan together (spec), merging the PR, and merging each promotion PR. The factory never approves or merges anything itself.

**When things change:** re-run `/factory:foundation` with the changed source when requirements change. It reopens only the affected steps. To try an idea that isn't a requirement yet, use `/factory:spike`. Its findings feed the requirements, and its code never merges.

## Commands

| Command | Stage | Does |
|---|---|---|
| **`/factory:go [ticket \| description]`** | 1–6 | **The everyday command.** Claims a ticket (or creates one from a description), then runs spec, plan, build, review and ship, stopping only where a person decides. Re-run to resume. |
| `/factory:foundation <source>` | 0 | Product, domain, decisions, architecture, skeleton or baseline, guardrails, backlog. The source is a Confluence URL, a file, chat text, or `code` for an existing codebase. |
| `/factory:task <description>` | 1 | Turns a bug or task described in chat into a complete ticket |
| `/factory:next` | 1 | Picks, checks and claims the next ready ticket |
| `/factory:job [cancel\|retry\|release]` | 1 | Shows or controls the active job |
| `/factory:spec` | 2 | Writes the OpenSpec proposal, spec deltas and plan, approved together: acceptance criteria, impact, release, reproduction for bugs, test-first tasks |
| `/factory:plan` | 3 | Redoes `design.md` and test-first `tasks.md` for a job sent back to planning |
| `/factory:build` | 4 | Builds the plan in a builder subagent, one commit per step: red, green, commit |
| `/factory:review` | 5 | Independent review, with security scans on every job and a second, security-only reviewer for security-sensitive ones, which brings in a security expert only for what the standard can't settle; blocking findings go back to build, at most twice |
| `/factory:ship [job]` | 6 | Syncs spec deltas into the living specs, archives the change, opens the PR (GitHub or Azure); re-run for PR comments, and after the merge to delete the branch, follow the deploy and move the ticket |
| `/factory:promote [from] [to]` | 6 | On request: promotes one environment's branch to the next, follows the deploy, moves the tickets |
| `/factory:spike <idea>` | — | A time-boxed experiment that never merges; only its findings do |

A bug fix is usually just `/factory:go <KEY>`, then `/factory:ship <KEY>` after the PR merges. The stage commands below `go` stay available for resuming or redoing a single stage.

The other step skills (`product-sync`, `domain`, `decide`, `architecture`, `skeleton`, `baseline`, `guardrails`, `backlog`) run from `foundation`, and can also be run on their own.

## What it writes in your repo

- `docs/`: product, architecture, ADRs, backlog, baseline
- `CONTEXT.md`: the domain glossary
- `openspec/specs/`: living specs, the current behaviour of each capability
- `openspec/changes/<job>/`: each job's proposal, deltas, design, tasks and review, archived once shipped
- `.factory/config.md`: the target branch, security scan commands and security expert group (set by `guardrails`), and the host and environments (asked once at the first ship)
- `.factory/runs/`: local scan output, never committed
- `.factory/jobs/`: job records
- `.factory/trusted.md`: who may release tickets to the factory

Each job lives on its own `factory/<id>` branch, and Stage 0 on `factory/foundation`. The factory commits there, never on the default branch. Only `ship` pushes, and only `factory/` branches (the job branch, or a revert branch for a rollback). Git hooks that `guardrails` commits in `.factory/hooks/` enforce this, with the branch rules, migration numbering and test-change approvals from `.factory/config.md`; they refuse when they can't decide. The plugin's SessionStart hook enables them in each clone.

## Checks done by code, not by the model

`scripts/factory.py` (tests in `scripts/tests/`):
- `validate <job> --stage spec|plan|build`: deltas are well formed and fit the living specs; every acceptance criterion is in the test plan, covered by a task, and proven by a test named `<job> AC-n …` that actually ran
- `approve <job> --what proposal [--by <name>]`: records who approved the proposal and deltas, with a hash, so any later edit voids the approval
- `sync` / `archive <job>`: merge a change's deltas into the living specs, and archive the change
- `check-specs`: every living-spec requirement has SHALL/MUST, a scenario, and a tag or a Source that exists
- `check-docs`: unique ids in the product and backlog, valid dependencies, no cycles
- `stamp` / `fresh <job>`: record which code the saved test results came from, so review and ship re-run the suite only when the code changed
- `scan <job>`: runs the security scans (gitleaks, osv-scanner and semgrep by default), and records which findings the job adds and which were already on the target branch
- `validate --stage spec` also checks the proposal's Security section: a sensitive proposal names its areas and misuse cases, and a cleared flag names who cleared it and why

## Layout

```
.claude-plugin/   plugin.json, marketplace.json
skills/           one directory per skill
agents/           requirements-analyst, architect, planner, investigator, builder, reviewer, security-reviewer
hooks/            hooks.json: the SessionStart hook that enables the committed git hooks in each clone
scripts/          factory.py validator and its tests; git hooks (the git guard: branches, migrations, test changes, staged secrets) and Claude Code hooks (env guard, Stop tests, test lock)
shared/           rules every skill follows: questions, jobs, OpenSpec, config, hosts, security, domain, ADRs, design, testing, prototypes
```
