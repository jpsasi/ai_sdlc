---
name: domain
description: Build the product's domain glossary (CONTEXT.md) from docs/product.md. Use when creating CONTEXT.md from requirements, or when product.md introduces new business terms.
disable-model-invocation: true
---

# Domain

Turn the business language in `docs/product.md` into the glossary in `CONTEXT.md`, so every later agent uses the product team's terms with one meaning each. Agents copy the words they're given, so an overloaded word in the requirements turns into two meanings in the code, the tests and the specs.

## Steps

1. **Extract.** Dispatch the `factory:requirements-analyst` subagent with the job *extract domain terms* and `docs/product.md`. It returns candidate terms, entities and their relationships, and **overloaded** terms (one word used with two meanings, or two words for one meaning), each with quotes.
2. **Resolve with the user**, following `${CLAUDE_PLUGIN_ROOT}/shared/DOMAIN.md`. Settle each overloaded term on one canonical name, and stress-test relationships with concrete scenarios. Write `CONTEXT.md` in that file's format as each term resolves.
3. **Escalate product gaps.** When a term can only be settled by the product team, close it with the outcomes `${CLAUDE_PLUGIN_ROOT}/skills/product-sync/SKILL.md` allows for the source type. For `local`, that means Answered or Dropped within this session.

In `existing` mode, also cross-reference the names the code already uses, and record each place where the code and `product.md` disagree.

## Done check

- Every domain noun in the capabilities and NFRs of `docs/product.md` is defined in `CONTEXT.md`.
- Every overloaded term is resolved to one canonical name.
- Open tickets raised by this step don't fail the check. List them for the user's proceed decision.
