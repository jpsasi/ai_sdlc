# Architecture decision records

An ADR records **that** a decision was made, and **why**, so nobody later "fixes" something that was deliberate, or reopens a settled question without knowing its history.

## Where

`docs/adr/NNNN-<slug>.md`, numbered in sequence: find the highest existing number and add one. `docs/adr/README.md` is the decision backlog (see the `decide` skill).

## Format

```markdown
---
status: accepted | superseded by ADR-NNNN
---

# <Short title of the decision>

<One to three sentences: the context, what was decided, and why. Cite the requirement ids (P-n, NFR-n, constraints) that drove it.>

## Considered options
<Only when the rejected alternatives are worth remembering.>

## Consequences
<Only when there are non-obvious downstream effects.>
```

One paragraph is often enough. Add the optional sections only when they carry real information.

## What deserves an ADR

A decision deserves one when all three hold:

1. **Hard to reverse**: changing course later would cost real effort.
2. **Surprising without context**: a future reader would wonder "why on earth is it done this way?"
3. **A real trade-off**: there were genuine alternatives, and one was picked for specific reasons.

Typical examples:

- architectural shape (a modular monolith, an event-sourced write model)
- how contexts integrate (events, not synchronous calls)
- technology with lock-in: database, message bus, auth provider, hosting
- boundary and ownership rules ("only the Customer context writes customer data")
- deliberate deviations from the obvious path ("hand-written SQL, not an ORM, because…")
- constraints invisible in the code (compliance, partner SLAs)
- non-obvious rejections ("REST over GraphQL, because…")

The foundation's baseline decisions (language and framework, data storage, auth, API style, hosting) always qualify. Smaller choices that are easy to reverse don't need one.
