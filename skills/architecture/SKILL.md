---
name: architecture
description: Write or update docs/architecture.md (modules, boundaries, data flow) from the product, domain and ADRs. Use when creating the architecture doc, or after a new ADR changes the module structure.
disable-model-invocation: true
---

# Architecture

`docs/architecture.md` is the map every builder and reviewer works from: the planner places each task in a module from it, and the reviewer checks boundaries against it. A vague map produces tasks that sprawl across modules. Its dependency rules become executable in the `guardrails` step, so write each one precisely enough to test.

## Steps

1. **Draft.** Dispatch the `factory:architect` subagent with `docs/product.md`, `CONTEXT.md`, every accepted ADR in `docs/adr/`, and the format below. Ask it to shape modules with the vocabulary in `${CLAUDE_PLUGIN_ROOT}/shared/DESIGN.md`: deep modules behind small interfaces. In `existing` mode, ask it to describe the code as it is, citing file paths. Keep it **coarse**: modules, their boundaries and their dependencies. Internals are documented later, one area at a time, when a task first touches them. Dependency rules describe the intended structure; where today's code breaks them, list the breaks under "Known violations", for the `guardrails` ratchet.
2. **Review with the user**, section by section, and revise. Ask any questions the review raises in rounds, by the rules in `${CLAUDE_PLUGIN_ROOT}/shared/QUESTIONS.md`. With `Approvals: auto`, skip the section-by-section review: the architecture follows from the accepted ADRs, which the user already decided. Ask only what the ADRs don't settle, by `${CLAUDE_PLUGIN_ROOT}/shared/AUTONOMY.md`.
3. **Route conflicts to decisions.** A draft that contradicts an accepted ADR, or needs a choice no ADR covers, goes back through `${CLAUDE_PLUGIN_ROOT}/skills/decide/SKILL.md`. Never resolve it inside this document.

## `architecture.md` format

```markdown
# Architecture

## Overview
<mermaid diagram of modules and external systems>

## Modules
### <module>
- Responsibility:
- Owns terms: <CONTEXT.md terms>
- Interface: <what other modules may call>
- May depend on: <modules>

## Dependency rules
- <module> → <module> allowed; everything else forbidden

## Known violations
<existing mode: current breaks of the rules above, with their count>

## Key flows
<request/data flow for 2–3 central capabilities, by P-id>

## Cross-cutting
Errors · logging · configuration · security · testing strategy

## Capability map
| Capability | Modules |
|---|---|
| P-1 | ... |
```

## Done check

- Every `P-n` in `docs/product.md` appears in the capability map.
- Every module has a responsibility, an interface and an allowed-dependency list.
- The document is consistent with every accepted ADR.
