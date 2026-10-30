---
name: plan
description: Stage 3 — redo the plan (design.md and test-first tasks.md) for a job sent back to planning; spec drafts the first plan with the proposal.
disable-model-invocation: true
---

# Plan

Stage 3 of the factory. The proposal and its deltas say *what* must be true; the plan says *how*. Spec writes the first plan from the investigator's draft and has it approved with the proposal, so this stage runs only for a job sent back to `planning`, such as a build that found the plan wrong. Spec also uses its checks and formats. Write `design.md` and `tasks.md` in the job's change folder, `openspec/changes/<id>/`. Stage 4 builds `tasks.md` one task at a time, ticking each off. The formats follow `${CLAUDE_PLUGIN_ROOT}/shared/OPENSPEC.md`, and jobs follow `${CLAUDE_PLUGIN_ROOT}/shared/JOBS.md`.

## Steps

1. **Load the job.** Find the active job, and switch to its branch, as described in `JOBS.md`. It must be `planning`. Resume from any existing `design.md` and `tasks.md`. Otherwise, tell the user what to run instead, and stop.
2. **Draft.** Dispatch the `factory:planner` subagent with the job *plan a spec*, the change folder (proposal and deltas), the job record, and the formats below.
3. **Check the draft** against these rules. Each rule that fails is a **flag**:
   - every acceptance criterion in the proposal is covered by at least one task
   - every file is in the proposal's Impact table
   - 8 tasks or fewer
   - every task has a test to write first and a verify command
   - no new dependency, and no choice outside the accepted ADRs

   Add every flag the planner raised.
4. **Decide.**
   - **No flags:** proceed without asking. Show the user the approach and the task titles in a few lines.
   - **Flags:** walk the user through them, by the rules in `${CLAUDE_PLUGIN_ROOT}/shared/QUESTIONS.md`. Each one ends one of four ways:
     - the plan is adjusted
     - the proposal needs changing: set the job back to `speccing`, and tell the user to run `/factory:spec`
     - a choice needs an ADR: follow `${CLAUDE_PLUGIN_ROOT}/skills/decide/SKILL.md`
     - a risk needs its own work: offer to create a ticket with `/factory:task`
5. **Write** `design.md` and `tasks.md` in the formats below. Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/factory.py" validate <id> --stage plan`, and fix them until it prints OK.
   - If it reports that the proposal or its deltas changed after approval, they go back for approval: set the job to `speccing`, and tell the user to run `/factory:spec`.
   - Otherwise, set the job to `building`, and commit the plan and the job record as `plan: <id>`. Never push. Offer to run `/factory:build`.

## `design.md` format

```markdown
# Design <id>: <title>

## Approach
<How the change is made: the functions and types that change or are added. For bugs, the confirmed root cause (file:line), and how the fix removes it.>
Alternative rejected: <option> — <why>

## Decisions
<Only choices worth recording here; anything hard to reverse is an ADR instead.>

## Migrations
<Each one, how the previous release keeps working against it, and its rollback. Or: none.>

## Risks
- <risk> → <mitigation>
```

## `tasks.md` format

```markdown
# Tasks <id>: <title>

- [ ] 1. <goal> (AC-n)
        Test first: <test file> — "<id> AC-n <behaviour>"
        Files: <paths>
        Verify: <command>
- [ ] 2. ...
```

Stage 4 ticks a task's box when its commit lands, so a build that stops mid-way resumes at the first unticked task. When the proposal lists migrations or config changes, each one gets its own task, including how it is rolled back.

## Done check

- Every acceptance criterion is covered by a task.
- Every task has a test first, its files, and a verify command.
- Every flag is resolved, or the job went back to `speccing`.
- `factory.py validate <id> --stage plan` prints OK.
