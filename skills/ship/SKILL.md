---
name: ship
description: Stage 6 — take a reviewed job to a pull request on GitHub or Azure Repos: sync its spec deltas into the living specs, archive the change, push, and open the PR for a person to merge. Re-run to act on PR review comments, and again after the merge to delete the branch, follow the deploy and move the ticket.
disable-model-invocation: true
argument-hint: "[job id]"
---

# Ship

Stage 6 of the factory. A person reviews and merges every PR; this skill prepares the branch, opens the PR, brings review comments back into the factory, and, once the PR has merged, follows it to the first environment. Read first:
- `.factory/config.md`, or run its Setup, by `${CLAUDE_PLUGIN_ROOT}/shared/CONFIG.md`
- `${CLAUDE_PLUGIN_ROOT}/shared/HOSTS.md`, for every host command
- `${CLAUDE_PLUGIN_ROOT}/shared/JOBS.md` and `${CLAUDE_PLUGIN_ROOT}/shared/OPENSPEC.md`

The change folder is `openspec/changes/<id>/` until this skill archives it, and `openspec/changes/archive/<date>-<id>/` afterwards.

## Steps

1. **Load the job:** the one named in `$ARGUMENTS`, else the active job, else the most recent job in `pr_open`. Switch to its branch, as `JOBS.md` describes. If the branch is already gone, read the record from the target branch instead.
   - `reviewed`: go on to step 2.
   - `pr_open`: read the PR's state. Merged: go to **After the merge** below. Otherwise: go to **PR feedback** below.
   - Anything else: tell the user what to run instead, and stop.
2. **Ready check.** Merge the latest target branch into the job branch, and resolve any conflicts. In `openspec/specs/`, keep both sides' requirements, then run `check-specs`. Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/factory.py" fresh <id>`. When it prints OK, the merge changed no code (only docs, specs, job records or CI config), so the saved results still hold: don't run the suite, and add the History line "ready check: results current, suite not re-run". Otherwise run the full suite, saving its output to `.factory/jobs/<id>-results.txt`, and run `factory.py stamp <id>`. Then run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/factory.py" validate <id> --stage build --results .factory/jobs/<id>-results.txt`. Unless it prints OK, the job goes back to `building`.
3. **Sync and archive**, so the PR carries the final state. Skip this on a re-ship, when the change is already archived.
   1. Run `factory.py sync <id>` when the change has deltas, then `factory.py check-specs`. Both must print OK.
   2. Run `factory.py archive <id>`, and update the `Change:` line of the job record to the archive path.
   3. With a `local` tracker, set the job's backlog row to `done`, so it takes effect when the PR merges.
   4. Commit, with any new results file from the ready check, as `<id>: sync specs and archive`.
4. **Push** the job branch, as `HOSTS.md` says.
5. **Open the PR** into the target branch, or update the open one on a re-ship.
   - **Title:** `<ticket id> <ticket title>`.
   - **Description:**
     - the ticket link, and the proposal's Why
     - each acceptance criterion, with the test that proves it and its result
     - the living-spec capabilities changed, and how many requirements were added, modified or removed
     - the review summary, with the suggestions not taken, from `review.md`
     - **migrations and config changes**, from the proposal's Release section, or "none"
     - the approvals, from the job record
   - **Merge message to use:** the PR title, so `/factory:promote` can find the ticket id.

   Add `PR: <link>` to the job record, set the job to `pr_open`, and commit and push. Move the ticket to the "PR open" status from the config, if one is set.
6. **Hand over.** Give the user:
   - the PR link
   - any failing checks or policies
   - how the person merging must complete it: the `PR merge` rule from the config
   - next: `/factory:ship <id>` again once it has merged

   Stop. The job no longer holds the active slot, so `/factory:next` can take the next ticket.

## PR feedback

Re-running `/factory:ship` on a job in `pr_open` brings review comments back into the factory.

1. Read the unresolved review comments, as `HOSTS.md` says. Show them, and settle each one with the user by `QUESTIONS.md`: act on it, answer it without changing code, or decline it with a reason.
2. If any comment is to be acted on:
   - When another job holds the active slot, tell the user. The rework waits until that job reaches `pr_open`, or the user frees the slot with `/factory:job`.
   - Otherwise, add one rework task per comment to the change's `tasks.md`, numbered on from the last task with `(PR-n)` in the title, each with its test first, its files and its verify command.
   - A comment that changes required behaviour also changes the archived delta and the living spec: edit both the same way, run `check-specs`, and record a new approval with `factory.py approve <id> --what proposal --by "<name>"` after the user's explicit yes.
   - Set the job to `building`, commit, and offer `/factory:build`. The job then goes through review again, and comes back here as a re-ship.
3. Draft replies for the comments answered without code changes, for the user to post.

## After the merge

Re-running `/factory:ship` on a merged job confirms it reached its first environment, cleans up its branch, and updates its ticket. A merge isn't a delivery: the ticket moves only once the deploy has actually succeeded, so testers never pick up work that isn't there yet.

The merged job record is on the target branch, which is protected, so this section doesn't edit the record. The ticket and its comments carry the job from here on: a job whose record is on the target branch, and whose branch is gone, is **done**.

1. **Check the merge.** If the PR was closed without merging, ask the user whether to retry it (`/factory:job retry`) or cancel it (`/factory:job cancel`), and stop.
2. **Delete the branch** on the remote and locally, as `HOSTS.md` says, unless it's already gone. Then switch to the target branch, and pull.
3. **Follow the deploy.** Find the environment whose branch is the target branch.
   - **None configured:** go to step 4.
   - **No pipeline** for it: go to step 4.
   - **Otherwise:** find the run that deploys the merge commit, and wait for it, as `HOSTS.md` says.
     - **Succeeded:** go to step 4.
     - **Failed or cancelled:** give the user the result and the run link, and stop. A fix is new work: a bug through `/factory:task`, or a pipeline fix as a task. Re-run `/factory:ship <id>` afterwards, and it picks up the later run.
     - **Roll back instead,** if the user asks: create `factory/revert-<id>` from the target branch, `git revert <merge commit>`, push it, and open a PR titled `Revert <ticket id>` for a person to merge. Move the ticket back to In Progress, with a comment saying why.
4. **Update the ticket.** Move it to the environment's "ticket status after deploy", or, with no environment, to the "Merged, no environment" status. Comment: "Deployed to <environment>: run <run number>, commit <short sha>, PR <link>", or "Merged: commit <short sha>, PR <link>".
5. **Report**, and point at what comes next: dev testing, then `/factory:promote` when the developer asks for it.

## Done check

- The PR is open into the target branch, with a description a reviewer can approve from.
- The change is archived, and its deltas are synced into `openspec/specs/`, with `check-specs` printing OK.
- The job is `pr_open`, and the user knows how the PR must be completed.
- Nothing in this skill approved, completed or merged the PR.
- After the merge: the job's branch is gone, locally and on the remote, and the deploy run succeeded (or there's no pipeline), with the ticket carrying its new status and the deploy comment. Or the user has the failure and its link.
