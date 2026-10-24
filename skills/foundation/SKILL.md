---
name: foundation
description: Run Stage 0 of the software factory from Confluence pages, requirements files or chat text, or from the existing code — product, domain, decisions, architecture, skeleton or baseline, guardrails, backlog. Re-run it after the requirements change.
disable-model-invocation: true
argument-hint: "[confluence-page-url | requirements-file | requirements text | code [supplement]]"
---

# Foundation

Run Stage 0 one step at a time. Every step ends on its **done check** and then the user's approval. `docs/foundation-status.md` is the single record of progress: read it first, and write it on every status change, so a new session resumes exactly where the last one stopped.

## Steps

| # | Skill | Output |
|---|---|---|
| 1 | `product-sync` | `docs/product.md` |
| 2 | `domain` | `CONTEXT.md` |
| 3 | `decide` | `docs/adr/` |
| 4 | `architecture` | `docs/architecture.md` |
| 5 | `skeleton` (`new` mode) or `baseline` (`existing` mode) | Running app, tests, CI, `docs/skeleton-gaps.md`; or `docs/baseline.md` |
| 6 | `guardrails` | Boundary tests, hooks, `CLAUDE.md` |
| 7 | `backlog` | `docs/backlog.md`, plus prioritised Jira or GitHub issues |

Run a step by reading and following its skill file, `${CLAUDE_PLUGIN_ROOT}/skills/<skill>/SKILL.md`. Each step skill owns its done check: evaluate it exactly as the step skill states it.

## Modes

- **`new`**: the repo holds no application code. Steps 2–4 design, and step 5 builds the skeleton.
- **`existing`**: the repo already holds application code. Onboard **just enough**:
  - Steps 2–4 document what the code already does, at a coarse level (modules, boundaries, decisions already made). Internals are documented later, one area at a time, when a task first touches them.
  - Step 5 runs `baseline` instead of building a skeleton.
  - Step 6 ratchets existing violations and records the real conventions.

Set the mode once, when the status file is created. The `code` source always means `existing`.

## Statuses

| Status | Meaning |
|---|---|
| `pending` | Not started |
| `in_progress` | Step skill is running, or a session stopped mid-step |
| `blocked` | Waiting on someone outside this session; the Note names who and what |
| `review` | Done check passed; waiting for the user's approval |
| `done` | User approved |

## Branch

Stage 0 never commits to the target branch: `Target branch:` in `.factory/config.md`, else the repo's default branch. Its work lives on `factory/foundation`, created from the latest target branch; a re-sync uses `factory/resync-<YYYY-MM-DD>`. It reaches the target branch through a pull request, and the factory takes tasks only once it has merged, because `/factory:next` reads these documents from the target branch.

## Run

1. **Load state.** If `docs/foundation-status.md` isn't on the current branch, look for a `factory/foundation` or `factory/resync-*` branch, and switch to it. The working tree must be clean first. Read the status file, then follow the first case that matches:
   - **Missing:**
     1. Resolve the sources from `$ARGUMENTS` exactly as step 1 of `${CLAUDE_PLUGIN_ROOT}/skills/product-sync/SKILL.md` does.
     2. If `$ARGUMENTS` is empty, ask for a source. When the repo already holds application code, offer `code` as an option.
     3. Set the mode.
     4. **Target branch.** Run steps 1, 3 and 7 of Setup in `${CLAUDE_PLUGIN_ROOT}/shared/CONFIG.md`: the host, the target branch, and protecting it. When the target branch doesn't exist on the remote yet, offer to create it from the default branch (`git push origin origin/<default>:refs/heads/<target>`) and wait for a yes. It must exist before guardrails protects it, and before anything branches from it.
     5. Create `factory/foundation` from the latest target branch, and switch to it. Write `.factory/config.md` with the host, repository and target branch (the rest is filled in at the first ship), and create the status file from the template below.
   - **Present, and `$ARGUMENTS` is `code`:** keep the recorded sources. Code never replaces requirements that already exist, so tell the user why, and offer a **Drift check** (below) instead.
   - **Present, and `$ARGUMENTS` names a new source:** pass it to `product-sync`, which asks whether it adds a feature or replaces the existing sources. If every step is already `done`, continue with **Re-sync**.
   - **Present, and every step is `done`:** run **Re-sync**.
   - **Otherwise:** go on to step 2 and resume.
2. **Pick the step**: the first row that is not `done`. Act on its status:
   - `pending` or `in_progress`: set `in_progress` with the current timestamp *before* invoking the step skill. For a step that was already `in_progress`, tell the skill to continue from its existing output.
   - `blocked`: re-check the blocker in the Note. Cleared: re-run the step. Still blocked: report it and stop.
   - `review`: summarise the output and ask for approval.
3. **Check.** When the step skill finishes, evaluate its done check.
   - Pass: set `review`, show a summary with file paths, and ask the user to approve or request changes.
   - Pass with open Jira tickets (`confluence` sources only): list the tickets with their scope, and ask whether to proceed with them still open.
     - Yes: treat it as approval, and write "proceeding with open <KEYS>" in the Note.
     - No: set `blocked` with "waiting on <KEYS>" in the Note, and stop.
   - Fails otherwise: fix the gap and check again.
4. **Approve.** On approval, set `done`, and commit the step's outputs together with the status file as `foundation: step N <skill> done` (the approval covers this commit; never push). Continue to the next step unless the user wants to stop. When the user requests changes, apply them, re-run the done check, and ask again.
5. **Share back.** When every step is `done`, draft a summary for the product and tech teams:
   - each accepted ADR: the decision, the chosen option, and the reason
   - a module overview from `docs/architecture.md`
   - the backlog: epics and task counts by priority, linked to the tracker
   - open Jira tickets, with the capabilities they block
   - links to `docs/` in the repo

   Show the draft to the user. Once they agree, write it to `docs/foundation-summary.md`, and tell the user it's ready to share with the product and tech teams. Confluence stays read-only. After a re-sync, update the same file rather than creating a new one.
6. **Finish.** Tell the user Stage 0 is complete. Next, they open a pull request from the Stage 0 branch into the target branch, and the factory takes tasks once it has merged.

## Re-sync

Run this when requirements change after Stage 0 is complete: a source page was edited, or a new feature's page or brief was added. Only the steps the change affects run again.

1. **Sync.** Create `factory/resync-<YYYY-MM-DD>` from the latest target branch, and switch to it. Follow `${CLAUDE_PLUGIN_ROOT}/skills/product-sync/SKILL.md`. If `docs/product.md` didn't change, report that, delete the branch, and stop.
2. **Assess impact.** Dispatch the `factory:architect` subagent with the diff of `docs/product.md` and the current Stage 0 documents. It reports, for each later step, whether that step must reopen, and why:

   | Step | Reopens when the change |
   |---|---|
   | `domain` | Introduces or changes business terms |
   | `decide` | Adds an NFR, a constraint or an external system, or needs a choice no accepted ADR covers |
   | `architecture` | Adds a capability no existing module can own, or changes a module's responsibility or dependencies |
   | `skeleton` | Adds an external system or an ADR that needs exercising. Extend the coverage; never rebuild. |
   | `baseline` | Touches a module whose coverage was rated `bare` or `thin`. Re-measure that module. |
   | `guardrails` | Changes the dependency rules in `docs/architecture.md` |
   | `backlog` | Always: new or changed capabilities need tasks |

3. **Confirm.** Show the reopen list with the reasons, and let the user add or remove steps.
4. **Find work already in flight.** For every changed or removed `P-n`, `NFR-n` and `C-n`, list everything that carries it, with an entry for each id, even if the entry is "nothing yet":
   - tasks in `docs/backlog.md`, and their tickets
   - active jobs (`factory/*` branches), with their specs and plans
   - living-spec requirements in `openspec/specs/` tagged with it, archived changes in `openspec/changes/archive/` that delivered it, and the tests named by their criteria
5. **Reopen.** Set each confirmed step to `pending`, with the Note "reopened: <reason>". Then continue with **Run** from step 2: the reopened steps run in Steps-table order, each with its done check and approval. The `factory:backlog` step then reworks the in-flight list:
   - a task not yet started: revise it in place
   - an active job: comment on its ticket, and set the job back to `speccing`, so its spec is revised and approved again
   - work already merged: a new rework task, linked to the original ticket, that reworks the tagged code and tests
   - a removed capability: a comment on each of its tickets, with their status left to the user

## Drift check

Run this on request, or when `/factory:foundation code` is given after the status file exists. It changes no source of truth. It reports where the code and the Stage 0 documents have drifted apart.

1. Dispatch the `factory:architect` subagent with the job *drift check*.
2. Write its findings to `docs/drift-report.md`, with the commit and date.
3. Walk the user through the findings, by the rules in `${CLAUDE_PLUGIN_ROOT}/shared/QUESTIONS.md`. Route each one:
   - **The document is out of date:** reopen the step that owns it, as in Re-sync step 5.
   - **The code is wrong:** add a `K-n` under Known gaps in `docs/product.md`, and reopen `backlog` so it gets a fix task.
   - **Accepted as is:** record it in the report.

Timestamps come from `date "+%Y-%m-%d %H:%M"`.

## Status file template

```markdown
# Foundation status

Sources:
- <confluence | local | code>: <page url | file path | repo> (supplement: <url or path, if any>)
Mode: new | existing
Jira project: <KEY, set on first ticket>
Tracker: <jira | github | local, set by the backlog step>

| Step | Skill | Status | Updated | Note |
|------|-------|--------|---------|------|
```

Add one `pending` row per step in the Steps table, in its order. For step 5, use the skill that matches the mode.
