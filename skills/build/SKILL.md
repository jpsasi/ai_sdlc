---
name: build
description: Stage 4 — build the active job's plan on a factory branch in a builder subagent, test first, each green step committed and ticked off in the plan.
disable-model-invocation: true
---

# Build

Stage 4 of the factory. Carry out `openspec/changes/<id>/tasks.md` one task at a time. A `factory:builder` subagent builds them in its own context, in order: **red**, then **green**, then committed and ticked off. One builder takes the whole plan, so the code and conventions are read once; a fresh one starts only after a failure or a decision. This session coordinates: it checks each result against git, keeps the job record, asks the user only what a builder can't decide, and runs the full suite at the end. It writes no code itself. Jobs follow `${CLAUDE_PLUGIN_ROOT}/shared/JOBS.md`.

## Steps

1. **Load the job.** Find the active job, and switch to its branch, as described in `${CLAUDE_PLUGIN_ROOT}/shared/JOBS.md`. If the working tree isn't clean, show `git status`, and ask the user to commit or stash their own changes first. The job must be `building`; otherwise, tell the user what to run instead, and stop.
2. **Check the approval.** Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/factory.py" validate <id> --stage plan`. If it reports that the proposal or its deltas changed after approval, nothing is built: set the job to `speccing`, and tell the user to run `/factory:spec`.
3. **Know the starting point.** Run the full suite once. Tests listed as failing in `docs/baseline.md` are **known red**, and stay known red. Any other failure on the fresh branch is the user's call before you start.
4. **Resume** at the plan's first unticked step.
5. **Build the steps.**
   1. **Dispatch** the `factory:builder` subagent with the job id, the first unticked step, the change folder, the known-red tests, the attempt number with the causes of earlier failed attempts, and any decision the user made for this step.
   2. **Check the result**, for each step the builder reports done: its box is ticked, its commits are on the branch, the working tree is clean apart from the job record, and `git diff --stat` over its commits names only files the plan lists for the step. A step that fails any of these counts as a failed attempt, whatever the builder said. Once every step is built, go to **Finish**.
   3. **On `needs decision`:** put the builder's question to the user, with its options and recommendation. Either the task is adjusted in `tasks.md` (and the change committed with the task), the answer is passed to a new builder starting at that step, or the job goes back to `planning`. Approval to change a test already on the target branch names the person and the reason; pass both to the builder.
   4. **On `failed`:** discard the step's uncommitted work first (`git checkout -- . && git clean -fd`, after checking `git status` shows only the step's files), then log the builder's attempts in the job's History, with the failing command and its one-line cause.
6. **Handle failure.** A step gets 3 attempts to reach green, inside the builder. When it reports `failed`:
   - set the job to `escalated`
   - write a History entry with what was tried, the last failure output, and the builder's view of whether the plan or the proposal is wrong
   - keep the branch as it is, and tell the user that `/factory:job retry` resumes from this step
7. **Finish.** When every box is ticked:
   - run the full suite, lint and boundary checks, saving the test output to `.factory/jobs/<id>-results.txt`. Nothing may fail beyond the known-red list. A failure here counts as an attempt on the step that caused it, under **Handle failure**: dispatch a builder to fix it, with the failing command and output, committing as `<id> fix: <what>`, and run the suite again.
   - run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/factory.py" stamp <id>`, which records the code the results came from, so review and ship can reuse them while the code is unchanged
   - run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/factory.py" validate <id> --stage build --results .factory/jobs/<id>-results.txt`, and fix until it prints OK
   - set the job to `reviewing`, and commit the job record and the results file as `build: <id> done`
   - offer to run `/factory:review`

## Done check

- Every step in the plan is ticked, with one commit each, plus any `<id> fix:` commits from the final suite run.
- No code was written in this session: every commit came from a builder, and each was checked against the plan.
- The full test suite, lint and boundary checks pass on the branch, apart from known-red tests.
- The results file is stamped, and `factory.py validate <id> --stage build` prints OK: every acceptance criterion has a test named by its id, and that test ran.
- Only files listed in the plan changed: compare `git diff --stat <target-branch>...factory/<id>` against the plan.
