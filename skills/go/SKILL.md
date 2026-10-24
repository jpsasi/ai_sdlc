---
name: go
description: Take one ticket from intake to an open PR in a single command — claim it, then run spec, plan, build, review and ship in turn, stopping only where a person must decide.
disable-model-invocation: true
argument-hint: "[ticket id | bug or task description]"
---

# Go

The one command for everyday work. It runs Stages 1 to 6 for one job by following each stage skill's own instructions, and moves straight on to the next stage instead of offering it. It stops only at **gates**, where a person must decide. Each stage still owns its rules, checks and gates; this skill only sequences them.

Stage skills are read from `${CLAUDE_PLUGIN_ROOT}/skills/<stage>/SKILL.md`, and followed exactly, with `$ARGUMENTS` taken as described below. Jobs follow `${CLAUDE_PLUGIN_ROOT}/shared/JOBS.md`.

## 1. Pick the job

Find the active job, as `JOBS.md` describes. Then follow the first case that matches:

| `$ARGUMENTS` | Active job | Do |
|---|---|---|
| empty | yes | Resume it |
| empty | none | Claim the top ready ticket: follow `${CLAUDE_PLUGIN_ROOT}/skills/next/SKILL.md` |
| a ticket id (`REF-12`, `#12` or `gh-12`, `T-3`) | that ticket | Resume it |
| a ticket id whose job is `pr_open` | any | Follow `${CLAUDE_PLUGIN_ROOT}/skills/ship/SKILL.md` for it: PR feedback while the PR is open, the deploy once it has merged |
| a ticket id | another ticket | Show the active job, offer to resume it or free the slot with `/factory:job cancel`, and stop |
| a ticket id | none | Claim that ticket: follow `${CLAUDE_PLUGIN_ROOT}/skills/next/SKILL.md` with the id. Every check still applies, trust included. |
| any other text | none | It's a new bug or task: follow `${CLAUDE_PLUGIN_ROOT}/skills/task/SKILL.md` with the text, then claim the ticket it creates, as above |
| any other text | yes | Tell the user a job is active, and stop |

If nothing gets claimed (every check failed, or there's no ready ticket), report why, and stop.

## 2. Run the stages

Repeat until a stop condition below is met: read the job's status, and follow the stage skill that owns it.

| Status | Follow |
|---|---|
| `queued`, `speccing` | `${CLAUDE_PLUGIN_ROOT}/skills/spec/SKILL.md` |
| `planning` | `${CLAUDE_PLUGIN_ROOT}/skills/plan/SKILL.md` |
| `building` | `${CLAUDE_PLUGIN_ROOT}/skills/build/SKILL.md` |
| `reviewing` | `${CLAUDE_PLUGIN_ROOT}/skills/review/SKILL.md` |
| `reviewed` | `${CLAUDE_PLUGIN_ROOT}/skills/ship/SKILL.md` |

When a stage skill ends by offering the next stage, that next stage simply runs. Its gates still apply in full.

## 3. Stop

Stop, and tell the user where things stand and what to do next, when:

- **A gate needs the user**: approving the proposal, settling plan flags or a scope question, a failing step, a requirement change. Wait for their answer, then carry on with the loop.
- **The job is `pr_open`**: the PR is with a person. Next: `/factory:go <id>` (or `/factory:ship <id>`) again later, which resumes in `${CLAUDE_PLUGIN_ROOT}/skills/ship/SKILL.md`: at the PR feedback while it's open, or at the deploy once it has merged.
- **The job is `escalated`**: report its History's last entry, and point at `/factory:job retry`.
- **The user asks to pause.** Everything is committed, so `/factory:go` resumes later at the same point.

## Done check

- The job is `pr_open` with its PR link reported, or the loop stopped at a gate, an escalation or a pause, with the next step clear to the user.
- No stage's gate was skipped.
