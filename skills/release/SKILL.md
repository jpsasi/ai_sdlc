---
name: release
description: Stage 6 — after a person merges a job's PR, delete its branch, follow the deploy pipeline of the first environment, and move the ticket on. Works with GitHub and Azure Repos.
disable-model-invocation: true
argument-hint: "<job id>"
---

# Release

Confirm that a merged job reached its first environment, clean up its branch, and update its ticket. A merge isn't a delivery: the ticket moves only once the deploy has actually succeeded, so testers never pick up work that isn't there yet. Read `.factory/config.md` (or run Setup, by `${CLAUDE_PLUGIN_ROOT}/shared/CONFIG.md`) and `${CLAUDE_PLUGIN_ROOT}/shared/HOSTS.md` first.

Once a PR merges, its job record is on the target branch, which is protected, so this skill doesn't edit the record. The ticket and its comments carry the release from here on: a job whose record is on the target branch, and whose branch is gone, is **done**.

## Steps

1. **Find the merge.** Take the job's `PR:` line, from its branch or from the target branch, and read the PR's state.
   - Not merged yet: report its state and checks, and stop. It's with the reviewer.
   - Closed without merging: ask the user whether to retry it (`/factory:job retry`) or cancel it (`/factory:job cancel`), and stop.
2. **Delete the branch** on the remote and locally, as `HOSTS.md` says. Then switch to the target branch, and pull.
3. **Follow the deploy.** Find the environment whose branch is the target branch.
   - **None configured:** go to step 4.
   - **No pipeline** for it: go to step 4.
   - **Otherwise:** find the run that deploys the merge commit, and wait for it, as `HOSTS.md` says.
     - **Succeeded:** go to step 4.
     - **Failed or cancelled:** give the user the result and the run link, and stop. A fix is new work: a bug through `/factory:task`, or a pipeline fix as a task. Re-run `/factory:release <id>` afterwards, and it picks up the later run.
     - **Roll back instead,** if the user asks: create `factory/revert-<id>` from the target branch, `git revert <merge commit>`, push it, and open a PR titled `Revert <ticket id>` for a person to merge. Move the ticket back to In Progress, with a comment saying why.
4. **Update the ticket.** Move it to the environment's "ticket status after deploy", or, with no environment, to the "Merged, no environment" status. Comment: "Deployed to <environment>: run <run number>, commit <short sha>, PR <link>", or "Merged: commit <short sha>, PR <link>".
5. **Report**, and point at what comes next: dev testing, then `/factory:promote` when the developer asks for it.

## Done check

- The job's branch is gone, locally and on the remote.
- The deploy run succeeded (or there's no pipeline), and the ticket carries its new status and the deploy comment. Or the user has the failure and its link.
