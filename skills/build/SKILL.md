---
name: build
description: Stage 4 — build the active job's plan step by step on a factory branch, test first, committing each green step and ticking it off in the plan.
disable-model-invocation: true
---

# Build

Stage 4 of the factory. Carry out `openspec/changes/<id>/tasks.md` one task at a time, following the approach in `design.md`, in this session, with the user able to watch and steer. Every step goes **red** then **green**, then gets committed and ticked off. Jobs follow `${CLAUDE_PLUGIN_ROOT}/shared/JOBS.md`. Write code the way `CLAUDE.md` says the surrounding code is written. Write tests by `${CLAUDE_PLUGIN_ROOT}/shared/TESTING.md`, and shape any new module by `${CLAUDE_PLUGIN_ROOT}/shared/DESIGN.md`.

## Steps

1. **Load the job.** Find the active job, and switch to its branch, as described in `${CLAUDE_PLUGIN_ROOT}/shared/JOBS.md`. If the working tree isn't clean, show `git status`, and ask the user to commit or stash their own changes first. The job must be `building`; otherwise, tell the user what to run instead, and stop.
2. **Check the approval.** Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/factory.py" validate <id> --stage plan`. If it reports that the proposal or its deltas changed after approval, nothing is built: set the job to `speccing`, and tell the user to run `/factory:spec`.
3. **Know the starting point.** Run the full suite once. Tests listed as failing in `docs/baseline.md` are **known red**, and stay known red. Any other failure on the fresh branch is the user's call before you start.
4. **Resume** at the plan's first unticked step.
5. **Build each step**, in order:
   1. **Red.** Write the step's test first, named as the plan says (`<id> AC-n <behaviour>`), and run it. It must fail, and fail because the behaviour is missing, not because of a typo or an import error. A test that passes before the code is written proves nothing: rewrite it. One exception: a **characterization test** pins current behaviour, so it must pass at once. For a **bug**, commit the failing test on its own first, as `<id> reproduce: <symptom>`, so the history shows red before green.
   2. **Green.** Write the least code that makes the test pass, and run the step's verify command.
   3. **Whole build.** Run the full test suite, lint and boundary checks. Nothing may fail beyond the known-red list, and there are no new architecture violations. A failing test is fixed in the code. Skipping, deleting or weakening a test to get green is never the fix; only the user's explicit approval changes a test's assertions. Tidy the code while it is green, if needed.
   4. **Commit** the task's files and `tasks.md`, with its box ticked, as `<id> step <n>: <goal>`. Never push.

   **Scope guard:** touch only the files the plan lists for the step. If the step needs another file, a new dependency, or a change the plan doesn't describe, stop and ask the user. Either the task is adjusted in `tasks.md` (and the change committed with the task), or the job goes back to `planning`.
6. **Handle failure.** A step gets 3 attempts to reach green with the whole build passing. Log every failed attempt in the job's History, with the failing command and a one-line cause. After the third failure:
   - set the job to `escalated`
   - write a History entry with what was tried, the last failure output, and your best guess at whether the plan or the proposal is wrong
   - keep the branch as it is, and tell the user that `/factory:job retry` resumes from this step
7. **Finish.** When every box is ticked:
   - run the full suite, lint and boundary checks one last time, saving the test output to `.factory/jobs/<id>-results.txt`
   - run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/factory.py" validate <id> --stage build --results .factory/jobs/<id>-results.txt`, and fix until it prints OK
   - set the job to `reviewing`, and commit the job record and the results file as `build: <id> done`
   - offer to run `/factory:review`

## Done check

- Every step in the plan is ticked, with one commit each.
- The full test suite, lint and boundary checks pass on the branch, apart from known-red tests.
- `factory.py validate <id> --stage build` prints OK: every acceptance criterion has a test named by its id, and that test ran.
- Only files listed in the plan changed: compare `git diff --stat <target-branch>...factory/<id>` against the plan.
