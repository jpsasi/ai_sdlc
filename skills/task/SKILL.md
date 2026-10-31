---
name: task
description: Turn a bug or task described in chat into a complete, released ticket in the factory's tracker, ready for /next.
disable-model-invocation: true
argument-hint: "<description of the bug or task>"
---

# Task

Turn the description in `$ARGUMENTS` into a ticket that passes every check in `${CLAUDE_PLUGIN_ROOT}/skills/next/SKILL.md`. All work enters the factory through the tracker, including chat.

With `Approvals: auto`, by `${CLAUDE_PLUGIN_ROOT}/shared/AUTONOMY.md`, don't confirm the classification, the proposed `P-n` and priority, or the ticket before creating it: the user asked for this ticket. Still ask for facts only the user has (steps to reproduce, expected behaviour), and still stop at **Check scope**.

## Steps

1. **Classify** the description as a bug or a task, and confirm with the user.
2. **Fill the gaps.** Collect what `${CLAUDE_PLUGIN_ROOT}/skills/next/SKILL.md`'s Complete check needs:
   - bug: steps to reproduce, expected vs actual behaviour
   - task: acceptance criteria, and the `P-n` it belongs to

   Also collect a priority (`high`, `medium` or `low`). Search `docs/product.md` for the matching `P-n`, and propose it. Ask for whatever is still missing by the rules in `${CLAUDE_PLUGIN_ROOT}/shared/QUESTIONS.md`, with a recommended answer for each question.
3. **Check scope.** If the work is a new capability rather than a change to an existing one, recommend adding it as a new source through `/factory:foundation`, so that domain, decisions and architecture are checked first. Continue only if the user still wants a single ticket.
4. **Create the ticket** in the tracker on the `Tracker:` line of `docs/foundation-status.md`. Show it to the user first, and create it once they agree.
   - `jira`: `createJiraIssue`, as a Bug or a Story, with the Priority field set and the label `factory-ready`
   - `github`: `gh issue create`, with the labels `factory-ready`, `priority:<level>`, `capability:P-n`, and `bug` for bugs
   - `local`: a new `T-n` row in `docs/backlog.md` under its `P-n` (or under `## Ad hoc` for bugs with no `P-n`), with status `ready`
5. **Offer** to run `/factory:next` now.
