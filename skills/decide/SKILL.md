---
name: decide
description: Make an architecture decision and record it as an ADR in docs/adr/. Use for the foundation's baseline decisions, or when a task needs a new stack, data store, service, dependency or pattern.
argument-hint: "[decision topic]"
disable-model-invocation: true
---

# Decide

Each hard-to-reverse choice becomes one ADR. The architect proposes options, and the user makes the choice: these decisions carry context only the team has (budget, skills, where the product is heading), and every later task is built on them, so a guess here is expensive everywhere. Decisions are asked in dependency order because a later choice's options depend on earlier answers (hosting depends on the language and the database).

## Decision backlog

`docs/adr/README.md` lists every decision:

```markdown
| ID | Decision | Depends on | Status | ADR |
|----|----------|------------|--------|-----|
| 0001 | Language and framework | | accepted | [0001](0001-language-and-framework.md) |
| 0002 | Data storage | | open | |
| 0005 | Hosting and deployment | 0001, 0002 | open | |
```

Statuses: `open`, `accepted`, `superseded`. "Depends on" lists the decisions whose answers change this one's options.

## Steps

1. **Build or extend the backlog.**
   - With a topic in `$ARGUMENTS`, add it as an `open` row.
   - With no topic and no backlog file yet, seed the backlog with the baseline decisions: language and framework, data storage, authentication and authorization, API and integration style, hosting and deployment. Add any decision the `factory:architect` subagent derives from the NFRs and constraints in `docs/product.md`.
   - In `existing` mode, record decisions already embodied in the code as `accepted` ADRs marked "pre-existing", after the user confirms each one.
   - Fill "Depends on" for every new row.
2. **Grill the decisions** by the method in `${CLAUDE_PLUGIN_ROOT}/shared/QUESTIONS.md`. The backlog is the design tree, and the frontier is every `open` row whose "Depends on" rows are all `accepted`. Each round:
   1. Dispatch the `factory:architect` subagent with the frontier decisions, `docs/product.md`, `CONTEXT.md`, and the accepted ADRs. Its options build on the answers already given.
   2. Ask the round by the rules in `${CLAUDE_PLUGIN_ROOT}/shared/QUESTIONS.md`. Each question gives:
      - two or three options, each with its trade-offs against the cited `P-n`, `NFR-n` and constraint ids
      - the cost to reverse
      - the architect's recommendation
   3. When the user is unsure whether an option is viable, offer a prototype to spike it, following `${CLAUDE_PLUGIN_ROOT}/shared/PROTOTYPE.md`, before they answer.
   4. For each answered decision, write its ADR in the format of `${CLAUDE_PLUGIN_ROOT}/shared/ADR.md`, naming the ids that drove the choice. Mark the row `accepted` and link it.
   5. When an answer raises a new decision, add it as an `open` row with its dependencies.
   6. Recompute the frontier, and ask the next round.

   The session is done when no `open` row remains.
3. **Supersede, never rewrite.** When a choice reverses an accepted ADR, write a new ADR and mark the old row `superseded`.

## Done check

- Every row in `docs/adr/README.md` is `accepted` or `superseded`.
- Every accepted ADR names the chosen option and the reason for it.
