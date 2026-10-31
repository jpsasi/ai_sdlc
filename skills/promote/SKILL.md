---
name: promote
description: Stage 6 — on the developer's request, promote everything in one environment's branch to the next (for example dev to QA), opening the PR for a person to merge, then following the deploy and moving the tickets. Works with GitHub and Azure Repos.
disable-model-invocation: true
argument-hint: "[from-environment] [to-environment]"
---

# Promote

Move what has passed testing in one environment into the next. Promotion happens **only when the developer asks for it**. A person merges the PR; this skill opens it, and follows the deploy once it has merged. Read `.factory/config.md` (or run Setup, by `${CLAUDE_PLUGIN_ROOT}/shared/CONFIG.md`) and `${CLAUDE_PLUGIN_ROOT}/shared/HOSTS.md` first.

## Steps

1. **Which environments.** Use the ones named in `$ARGUMENTS`. Otherwise, use the first environment and the one after it in the config's order. Confirm both with the developer (with `Approvals: auto`, only when they weren't named and the config's order leaves a choice), and confirm both branches exist on the remote. With fewer than two environments configured, there is nothing to promote: say so, and stop.
2. **Resume first.** Look for a recent PR from the *from* branch into the *to* branch.
   - **Open:** it's with the reviewer. Report its state and checks, and stop.
   - **Merged, and its tickets not yet moved:** go to step 6.
3. **What would go.** List the commits the promotion carries, as `HOSTS.md` says. Take the ticket ids from the commit subjects (each job's squash commit starts with its ticket id), and read each ticket's status. Commits with no ticket id are **untracked changes**: name each one with the area it touched, so testers can regression-test it. If there's nothing to promote, say so, and stop.
4. **Check readiness.** Show the developer one line per ticket: id, title, status, commit. Flag every ticket not yet at the *from* environment's "ticket status after deploy" status: still in progress, never released, or not yet tested. **The PR carries every commit in the branch**, so a flagged ticket can't be left behind. The developer either confirms it is safe to go, or holds the whole promotion. This stops in either Approvals mode; with `Approvals: auto` and nothing flagged, go straight on.
5. **Open the PR** from the *from* branch into the *to* branch, titled `Promote <from> → <to> <date>`. Its description lists:
   - each ticket: id, title, and link
   - each untracked change, with the area to regression-test
   - the commit range
   - every **migration and config change** the included jobs listed, from the Release sections of their archived proposals in `openspec/changes/archive/`, since the *to* environment needs its config in place before the deploy

   Report any failing check or policy. Give the developer the link, and the `Promotion merge` rule from the config for the person merging it. A merge commit keeps the *to* branch sharing history with the *from* branch, so later promotions apply cleanly. Stop. The developer runs `/factory:promote` again once it has merged.
6. **Follow the deploy.** Find the *to* environment's pipeline run that carries the promotion's merge commit, and wait for it, as `HOSTS.md` says. If it failed, give the developer the result and the link, and stop.
7. **Update the tickets.** Move each promoted ticket to the *to* environment's "ticket status after deploy", and comment: "Deployed to <to>: run <run number>, PR <link>".

## Done check

- Either the promotion PR is open and the developer knows how it must be merged, or, after the merge, the deploy succeeded and every promoted ticket carries its new status and the deploy comment.
- If the deploy failed, the developer has the failure and its link.
