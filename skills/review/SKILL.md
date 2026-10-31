---
name: review
description: Stage 5 — independent review of the active job's branch against its spec, standards, architecture, test quality, security and release safety, sending blocking findings back to build for at most two rework cycles.
disable-model-invocation: true
---

# Review

Stage 5 of the factory. An independent reviewer checks the branch before any person sees the PR. Blocking findings go back to `/factory:build` as rework steps, at most twice. Suggestions travel to the PR description. Jobs follow `${CLAUDE_PLUGIN_ROOT}/shared/JOBS.md`.

## Steps

1. **Load the job.** Find the active job, and switch to its branch, as described in `${CLAUDE_PLUGIN_ROOT}/shared/JOBS.md`. It must be `reviewing`; otherwise, tell the user what to run instead, and stop. The review **cycle** is one more than the number of "review cycle" entries already in the History.
2. **Ready check.** Merge the latest target branch into the job branch, resolving any conflicts. Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/factory.py" fresh <id>`. When it prints OK, the merge changed no code (only docs, specs, job records or CI config), so the saved results still hold: don't run the suite, and add the History line "ready check: results current, suite not re-run". Otherwise run the full suite, saving its output to `.factory/jobs/<id>-results.txt`, and run `factory.py stamp <id>`. Then run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/factory.py" validate <id> --stage build --results .factory/jobs/<id>-results.txt`. Unless it prints OK, the job goes back to `building`: say what failed, and offer `/factory:build`.
3. **Scan.** Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/factory.py" scan <id>`. It runs the Secrets, Dependencies and Code scan commands from `.factory/config.md`, by `${CLAUDE_PLUGIN_ROOT}/shared/SECURITY.md`, and saves to `.factory/runs/<id>-scans.txt` which findings the job adds and which were already on the target branch. Exit 1 means the job adds a finding, which the reviewer reports as blocking. Exit 2 stops the review: a scanner is missing or can't run, so tell the user how to install it; or the scan rows or target branch are missing, so tell them to re-run `/factory:guardrails`. Review without the scans only when the user explicitly agrees, and then write `scans waived: <who agreed, and why>` in the Checks line of `review.md`.
4. **Review.** Dispatch the `factory:reviewer` subagent with the following, and nothing else: in particular, not the plan, and not this session's reasoning.
   - the diff range `<target-branch>...factory/<id>`
   - the change folder `openspec/changes/<id>/`: the proposal and its deltas, but not `design.md` or `tasks.md`
   - the job record, and the test results file, which the ready check has just made current, so the reviewer doesn't run the suite again
   - the scans file
   - the paths of `CLAUDE.md`, `CONTEXT.md`, `docs/architecture.md`, `docs/adr/`, `${CLAUDE_PLUGIN_ROOT}/shared/TESTING.md` and `${CLAUDE_PLUGIN_ROOT}/shared/SECURITY.md`

   When the proposal says `Sensitive: yes`, dispatch the `factory:security-reviewer` subagent at the same time, with the same diff range, change folder, job record and scans file, and the paths of `.factory/config.md`, `docs/architecture.md`, `docs/adr/` and `SECURITY.md`. Both reviewers number their findings `R-1` onwards: renumber them into one list.
5. **Record** the findings in `openspec/changes/<id>/review.md` under a heading for this cycle, in the format below. Its Checks line carries each scan's result: the scans file is never committed, so this line is the PR's record of the run.
6. **Route** on the blocking findings. A finding that the change touches a sensitive area the proposal didn't flag goes back to spec, whatever the cycle: set the job to `speccing`, with History "review: security-sensitive, not flagged", and offer `/factory:spec`. The proposal gets its flag and misuse cases, and is approved again.

   An `expert` finding with no decision in `review.md` escalates the job, whatever the cycle: set it to `escalated`, with History "needs security expert: R-n", commit as `review: <id> cycle <n>`, and tell the user what the expert must decide, and who's in the Expert group of `.factory/config.md` (run Setup in `${CLAUDE_PLUGIN_ROOT}/shared/CONFIG.md` when it's empty). `/factory:job retry` resumes once the user gives you the decision: record it by `SECURITY.md`, and treat a decision to fix as a blocking finding. A developer who wants to accept a blocking security finding rather than fix it turns it into an `expert` finding. Otherwise:
   - **None:** set the job to `reviewed`. Commit the review, the job record and the results file as `review: <id> passed`. Never push. Offer to run `/factory:ship`.
   - **Some, and this is cycle 1 or 2:** add one rework task per blocking finding to the end of `openspec/changes/<id>/tasks.md`, numbered on from the last task, with its `R-n` in the title (`- [ ] 6. <fix> (R-1)`), so the validator counts it as rework. Each task names the test that proves the fix (written first, as in any task), its files, and its verify command. Set the job to `building`, with History "review cycle <n>: <k> blocking". Commit as `review: <id> cycle <n>`, and offer to run `/factory:build`.

     A finding whose fix falls outside the proposal's Impact table can't be reworked in place. Ask the user whether to widen the proposal (the job goes back to `speccing`), accept the finding, or escalate. This is a scope change, so it stops even with `Approvals: auto`.
   - **Some, after cycle 2:** set the job to `escalated`, with History listing the open findings. Commit, and tell the user that `/factory:job retry` resumes after they've looked.

## `review.md` format

```markdown
# Review <id>

## Cycle 1 — <date>
Checks: tests pass · lint pass · boundaries pass · secrets clean · dependencies clean (2 known on target) · code scan clean
Security reviewer: run (Sensitive: yes — money movement) | not run (Sensitive: no)
Expert decisions: none | R-3 decided by <name> — <decision>

| ID | Axis | Severity | Where | Finding | Fix |
|----|------|----------|-------|---------|-----|
| R-1 | spec | blocking | src/credit/redeem.ts:40 | AC-2 untested | add test for retry with same order id |
| R-2 | standards | suggestion | src/credit/redeem.ts:12 | Mysterious name `proc` | rename to `applyCredit` |

Clean axes: architecture, security
```

On a later cycle, add a new section. Mark each earlier blocking finding `fixed` or `still open`.

## Done check

- `review.md` holds this cycle's findings, and the checks' and scans' results, or the user's waiver of the scans.
- A flagged job had the security reviewer, as well as the reviewer.
- Every `expert` finding has a security expert's decision, or the job is `escalated`.
- No blocking finding is open, or the job went back to `building`, `speccing`, or `escalated`.
