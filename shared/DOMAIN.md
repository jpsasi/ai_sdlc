# Domain glossary

`CONTEXT.md` holds the product's **ubiquitous language**: one agreed name and meaning for each business concept. Every agent writes specs, code and tests in these terms.

## Resolving terms with the user

Work actively, not just by transcription:

- **Challenge conflicts.** When a word is used in a way that clashes with the glossary, say so at once: "The glossary defines *cancellation* as X, but this reads as Y. Which is it?"
- **Sharpen fuzzy words.** When a word is vague or overloaded, propose one precise canonical term: "By *account*, do you mean the Customer or the User? Those are different things."
- **Stress-test with scenarios.** Invent concrete edge cases that force the boundary between two concepts into the open.
- **Cross-check the code.** In an existing codebase, compare what is said with what the code does, and surface contradictions.
- **Write as you go.** Add each term to `CONTEXT.md` the moment it is resolved. Don't batch them.

Ask these questions by the rules in `QUESTIONS.md`.

## `CONTEXT.md` format

```markdown
# <Context name>

<One or two sentences: what this context is and why it exists.>

## Language

**Order**:
A customer's request to buy one or more products.
_Avoid_: Purchase, transaction

**Invoice**:
A request for payment sent to a customer after delivery.
_Avoid_: Bill, payment request
```

## Rules

- **Pick one word.** When several words exist for one concept, choose the best, and list the rest under `_Avoid_`.
- **Define what it is**, in one or two sentences, not what it does.
- **Domain terms only.** General programming concepts (timeouts, retries, error types) don't belong, even when the code uses them heavily.
- **A glossary, nothing else.** No implementation details, specs or decisions: those live in specs, `docs/architecture.md` and ADRs.
- **Group** terms under subheadings when natural clusters appear.

## More than one context

Most repos have one root `CONTEXT.md`. When the product has several distinct contexts (say ordering, billing and fulfilment, each with its own language), put a `CONTEXT.md` in each context's directory, and a root `CONTEXT-MAP.md` that lists them and how they relate:

```markdown
# Context map

## Contexts
- [Ordering](./src/ordering/CONTEXT.md): receives and tracks customer orders
- [Billing](./src/billing/CONTEXT.md): invoices and payments

## Relationships
- **Ordering → Billing**: Ordering emits `OrderPlaced`; Billing consumes it to raise an invoice
```

When `CONTEXT-MAP.md` exists, work out which context a term belongs to, and ask if it's unclear.
