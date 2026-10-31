---
name: backlog
description: Turn the product's capabilities into an approved, prioritised backlog of small tasks, in docs/backlog.md and as Jira or GitHub issues. Use at the end of foundation, or after a re-sync adds or changes capabilities.
disable-model-invocation: true
---

# Backlog

Turn each capability in `docs/product.md` into prioritised **tasks** the factory can build one at a time. The planner drafts, and the user approves. `docs/backlog.md` is the single map from capabilities to tasks, whatever the tracker.

## Task shape

A task is a **vertical slice**: it is user-visible or testable on its own, fits in one PR, and takes about a day or less. Each task carries:

- a title and a one-line goal
- the `P-n`s it delivers, plus any `C-n` clarifications it relies on
- acceptance criteria: testable statements drawn from the acceptance hints and clarifications
- the modules it touches, from `docs/architecture.md`
- "depends on": other tasks that must ship first
- a **priority**: `high`, `medium` or `low`

## Priority

Priority decides the order Stage 1 picks tasks up: highest priority first, then backlog order, and only once a task's dependencies are `done`. The planner proposes a priority for each task from:

- the product's goals, and what a first usable release needs
- how many other tasks it unblocks
- risk: tasks that exercise skeleton gaps or stubs go early

The user has the final say.

## Trackers

The `Tracker:` line in `docs/foundation-status.md` names where tickets go. Ask the user once, recommending `jira` for `confluence` sources and `local` for `local` sources, and record the answer there.

| | `jira` | `github` | `local` |
|---|---|---|---|
| Where | The project on the `Jira project:` line (ask once and record it) | This repo's issues, through `gh` | `docs/backlog.md` only |
| Epic | Epic `[P-n] <capability>` | Issue `[P-n] <capability>` labeled `epic`, listing its tasks as a checklist | The `## P-n` section |
| Task | Story in its epic | Issue labeled `capability:P-n` | A row |
| Dependency | "blocks" link, created with `createIssueLink` | A `Depends on #<n>` line in the body | The "Depends on" column |
| Priority | The Priority field: High, Medium or Low | The label `priority:high`, `priority:medium` or `priority:low` | The Priority column |
| Ready signal | The label `factory-ready` | The label `factory-ready` | Status `ready` |

For `github`, create any missing label with `gh label create` before using it.

## Steps

1. **Find the capabilities to plan.** Plan every `P-n` that has no tasks in `docs/backlog.md` yet, or whose text changed since its tasks were planned. Skip a `P-n` that is:
   - marked `Blocked by`: list it under Waiting instead
   - already delivered by the skeleton, or by existing code in `existing` mode: record it as delivered

   Also plan one fix task for every `K-n` under Known gaps that has no task yet.

   After a re-sync, also work through its in-flight list, as the Re-sync section of `${CLAUDE_PLUGIN_ROOT}/skills/foundation/SKILL.md` describes.
2. **Draft.** Dispatch the `factory:planner` subagent with the job *plan tasks*, those capabilities, and the paths of `docs/product.md`, `CONTEXT.md`, `docs/architecture.md`, `docs/skeleton-gaps.md` (or `docs/baseline.md` in `existing` mode), and the current `docs/backlog.md`. For a changed capability, have it revise the existing tasks that haven't started, rather than duplicating them.
3. **Review with the user**, one epic (capability) at a time, priorities included. The user can reorder, reprioritise, merge, split or drop tasks. Ask any questions in rounds, by the rules in `${CLAUDE_PLUGIN_ROOT}/shared/QUESTIONS.md`. With `Approvals: auto`, take the planner's draft and priorities without the per-epic review, by `${CLAUDE_PLUGIN_ROOT}/shared/AUTONOMY.md`. The user sees the whole backlog once, at step 5, before any ticket is created.
4. **Write** `docs/backlog.md` in the format below.
5. **Create the tickets** in the tracker (skip this step for `local`). Use the tracker's form from the table above:
   1. the epic, if it doesn't already exist
   2. each task, with the goal, acceptance criteria, `P-n`s, modules and a link to the source in its description, and with its priority set
   3. the dependencies
   4. the ready signal on every approved task

   List the tickets you are about to create, and create them once the user agrees. This stops in either Approvals mode: with `auto`, it's where the user reviews the backlog, so show it by epic with priorities, and apply any changes before creating anything. For `local`, with `auto`, show the backlog and stop here instead. Record each ticket's key or number in `docs/backlog.md`.

## `backlog.md` format

```markdown
# Backlog

Tracker: jira | github | local

## P-1 <capability>
| Task | Title | Priority | Depends on | Modules | Status | Ticket |
|------|-------|----------|------------|---------|--------|--------|
| T-1 | Sign-up creates a referral code | high | | identity, referrals | ready | REF-12 |
| T-2 | Share link page | medium | T-1 | referrals, web | ready | REF-13 |

Acceptance criteria
- T-1: a new user has a unique referral code ...

## Waiting
- P-4 — blocked by REF-7

## Delivered
- P-1 sign-up slice — skeleton
```

Task statuses: `ready`, `in_progress`, `done`, `hold` (cancelled, waiting to be released again), `manual` (handed to a person), and `needs-info` (intake found it incomplete; local tracker only). Later stages and `${CLAUDE_PLUGIN_ROOT}/skills/job/SKILL.md` update them. Task ids are stable: new tasks take the next free `T-n`. The Ticket column holds a Jira key, a GitHub `#n`, or is empty for `local`.

## Done check

- Every `P-n` is planned, waiting, or delivered, and every `K-n` has a fix task.
- Every task has a goal, acceptance criteria, `P-n`s, modules and a priority.
- `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/factory.py" check-docs` prints OK: ids are unique, every section matches a capability, and the dependency graph has no cycles.
- For `jira` and `github`: every task has a ticket carrying its priority and the ready signal.
- The user approved every epic.
