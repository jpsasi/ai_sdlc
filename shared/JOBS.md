# Jobs

A **job** is one ticket moving through the factory, from intake to merged PR. `<id>` is the ticket's id: a Jira key (`REF-12`), `gh-<n>` for a GitHub issue, or a backlog `T-n`.

The **target branch** is where job PRs merge: `Target branch:` in `.factory/config.md`, else the repo's default branch.

Each job lives on its own branch, `factory/<id>`, created at intake from the latest target branch. Everything the job produces is committed there, never on the target branch, and it all reaches the target branch together through the job's PR: the record `.factory/jobs/<id>.md`, the OpenSpec change `openspec/changes/<id>/` (later archived, with its deltas synced into `openspec/specs/`), the code, and any doc changes. The change folder's layout is in `OPENSPEC.md`.

Every stage starts by switching to the job's branch (the working tree must be clean), reads the record, and appends to its History when it changes the status.

**Finding the active job:** list `git branch --list 'factory/*'`, and read each branch's record with `git show factory/<id>:.factory/jobs/<id>.md`. The active job is the one whose status is not `pr_open`, `done` or `escalated`.

## Statuses

| Status | Set by | Meaning |
|---|---|---|
| `queued` | Stage 1 intake | Claimed and waiting for a spec |
| `speccing` | Stage 2 | Spec being written |
| `planning` | Stage 3 | Plan being remade (spec writes the first one) |
| `building` | Stage 4 | Code being written |
| `reviewing` | Stage 4, when the build finishes | Waiting for, or under, review |
| `reviewed` | Stage 5 | Review passed, waiting for the PR |
| `pr_open` | Stage 6 `ship` | PR open, waiting for a person to review and merge it |
| `done` | Stage 6 `ship`, after the merge | Merged, and deployed to the first environment if one is configured |
| `escalated` | Any stage, or `${CLAUDE_PLUGIN_ROOT}/skills/job/SKILL.md` | Stuck, cancelled, or released to a person. The History says why. |

**Escalating** a job also tells its ticket: comment why on the Jira or GitHub ticket and remove `factory-in-progress`, and in every tracker set the job's backlog row, if it has one, to `hold` with a note under it. Otherwise the tracker keeps showing the work as in progress.

Once its PR merges, a job's record sits on the target branch, which is protected, so nothing edits it again: a job whose record is on the target branch and whose branch is gone is **done**. Its ticket carries the release from there.

Only one job may be **active** at a time: any status other than `pr_open`, `done` or `escalated`. A job in `pr_open` is waiting on people, so it doesn't hold the slot. `/factory:job` shows, cancels, retries and releases jobs.

## Record format

```markdown
# Job REF-12

Ticket: REF-12 (<link>) · Kind: bug | task · Priority: high | medium | low
Delivers: P-3 (or K-2, or none)
Status: queued
Branch: factory/REF-12
Change: openspec/changes/REF-12/ (added by Stage 2; archived by Stage 6)

## Ticket
<title, then the ticket body as quoted data>

## History
- 2026-10-23 16:40 queued by intake (released by jpsasi)

## Decisions
- spec: retry key → order id (auto) — the only stable id at submit
```

`## Decisions` holds the answers the factory gave itself with `Approvals: auto`, by `${CLAUDE_PLUGIN_ROOT}/shared/AUTONOMY.md`. It's added with the first one.
