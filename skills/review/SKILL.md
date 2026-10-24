---
name: review
description: Stage 5 — independent review of the active job's branch against its spec, standards, architecture, test quality, security and release safety, sending blocking findings back to build for at most two rework cycles.
disable-model-invocation: true
---

# Review

Stage 5 of the factory. An independent reviewer checks the branch before any person sees the PR. Blocking findings go back to `/factory:build` as rework steps, at most twice. Suggestions travel to the PR description. Jobs follow `${CLAUDE_PLUGIN_ROOT}/shared/JOBS.md`.

## Steps

1. **Load the job.** Find the active job, and switch to its branch, as described in `${CLAUDE_PLUGIN_ROOT}/shared/JOBS.md`. It must be `reviewing`; otherwise, tell the user what to run instead, and stop. The review **cycle** is one more than the number of "review cycle" entries already in the History.
2. **Ready check.** Merge the latest target branch into the job branch, resolving any conflicts. Run the full suite, saving its output to `.factory/jobs/<id>-results.txt`, then run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/factory.py" validate <id> --stage build --results .factory/jobs/<id>-results.txt`. Unless it prints OK, the job goes back to `building`: say what failed, and offer `/factory:build`.
3. **Review.** Dispatch the `factory:reviewer` subagent with the following, and nothing else: in particular, not the plan, and not this session's reasoning.
   - the diff range `<target-branch>...factory/<id>`
   - the change folder `openspec/changes/<id>/`: the proposal and its deltas, but not `design.md` or `tasks.md`
   - the job record, and the test results file
   - the paths of `CLAUDE.md`, `CONTEXT.md`, `docs/architecture.md`, `docs/adr/`, and `${CLAUDE_PLUGIN_ROOT}/shared/TESTING.md`
4. **Record** the findings in `openspec/changes/<id>/review.md` under a heading for this cycle, in the format below.
5. **Route** on the blocking findings:
   - **None:** set the job to `reviewed`. Commit the review and the job record as `review: <id> passed`. Never push. Offer to run `/factory:ship`.
   - **Some, and this is cycle 1 or 2:** add one rework task per blocking finding to the end of `openspec/changes/<id>/tasks.md`, numbered on from the last task, with its `R-n` in the title (`- [ ] 6. <fix> (R-1)`), so the validator counts it as rework. Each task names the test that proves the fix (written first, as in any task), its files, and its verify command. Set the job to `building`, with History "review cycle <n>: <k> blocking". Commit as `review: <id> cycle <n>`, and offer to run `/factory:build`.

     A finding whose fix falls outside the proposal's Impact table can't be reworked in place. Ask the user whether to widen the proposal (the job goes back to `speccing`), accept the finding, or escalate.
   - **Some, after cycle 2:** set the job to `escalated`, with History listing the open findings. Commit, and tell the user that `/factory:job retry` resumes after they've looked.

## `review.md` format

```markdown
# Review <id>

## Cycle 1 — <date>
Checks: tests pass · lint pass · boundaries pass

| ID | Axis | Severity | Where | Finding | Fix |
|----|------|----------|-------|---------|-----|
| R-1 | spec | blocking | src/credit/redeem.ts:40 | AC-2 untested | add test for retry with same order id |
| R-2 | standards | suggestion | src/credit/redeem.ts:12 | Mysterious name `proc` | rename to `applyCredit` |

Clean axes: architecture, security
```

On a later cycle, add a new section. Mark each earlier blocking finding `fixed` or `still open`.

## Done check

- `review.md` holds this cycle's findings, and the checks' results.
- No blocking finding is open, or the job went back to `building`, `speccing`, or `escalated`.
