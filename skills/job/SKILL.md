---
name: job
description: Show or control the factory's active job — status, cancel, retry, or release it to a person.
disable-model-invocation: true
argument-hint: "[cancel | retry [id] | release] [reason]"
---

# Job

Control factory jobs. Records, statuses and the active-job lookup follow `${CLAUDE_PLUGIN_ROOT}/shared/JOBS.md`. A job's record lives on its branch, so switch to the branch before changing the record. Every action appends a timestamped line to the job's History, and is committed as `job: <action> <id>`. Never push.

The tracker is the one on the `Tracker:` line of `docs/foundation-status.md`. "The backlog row" means the job's row in `docs/backlog.md`, if it has one.

## Actions

**No argument: status.** Show the active job, or else the most recent one: its ticket, kind, priority, status, and History. Point out when it has sat in one status since a previous session.

**`cancel [reason]`**: stop the active job and return the ticket to the queue, **unreleased**, so it isn't picked up again straight away.
1. Show what will change, and ask the user to confirm.
2. Tracker:
   - `jira`: move the ticket back to a To Do status with `transitionJiraIssue`, remove `factory-ready`, and comment with the reason
   - `github`: remove `factory-in-progress` and `factory-ready`, and comment with the reason
   - `local`, and the backlog row in every tracker: set its status to `hold`
3. On the job branch, set the job to `escalated`, with History "cancelled: <reason>", and commit.
4. Ask whether to keep the `factory/<id>` branch or delete it. Show what it holds first, with `git log <target-branch>..factory/<id>`. Deleting it also deletes the job record and the `hold` status. With a `local` tracker, that returns the ticket to `ready`, so tell the user before deleting.

To release the ticket again later, re-add `factory-ready`, or set the row back to `ready`.

**`retry [id]`**: resume an `escalated` job, by default the most recent one.
1. Refuse if another job is active.
2. From the History, find the status the job held before `escalated`, and set the job back to that status.
3. If it was cancelled, restore the tracker state that cancel undid: In Progress, or `factory-in-progress`. Set the backlog row to `in_progress`.
4. Tell the user which stage picks the job up from here.

**`release [reason]`**: hand the active job to a person, who finishes it outside the factory.
1. Confirm with the user.
2. Tracker: remove `factory-ready` and `factory-in-progress`, keep the status In Progress, and comment "Released from the factory to a person: <reason>". Set the backlog row to `manual`.
3. Keep the `factory/<id>` branch, so the person can continue from it.
4. Set the job to `escalated`, with History "released: <reason>".
