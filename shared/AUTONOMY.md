# Approvals

`Approvals:` in `.factory/config.md` sets who answers the factory's questions. `manual`, the default when the line is missing, means the user, at every gate the skills describe. `auto` means the factory answers with its own recommendation, writes the answer down, and goes on. It stops only at a **critical gate**. Either way, a person merges every PR, so every answer the factory gives is seen before it ships.

## In `auto` mode

Wherever a skill says to ask, confirm, show and wait, or approve, check the question against the critical gates below.

- **Not critical, with a clear recommendation:** take the recommendation. Don't ask, and don't wait. Say what you decided in one line, and carry on.
- **Critical, or no clear recommendation:** ask, as in `manual` mode, by `QUESTIONS.md`. A recommendation isn't clear when the options are close, when it rests on a fact you couldn't check, or when you'd be guessing what the user wants. Auto mode never guesses.

## Critical gates

These always stop for a person, in either mode:

| Gate | Where |
|---|---|
| Approving a proposal that isn't `Sensitive: no` | spec. `factory.py approve --auto` refuses it. |
| Clearing a security flag, and an `expert` security finding | spec, review, by `SECURITY.md` |
| A new ADR: a new stack, data store, service, external system, dependency or pattern | decide, and any stage that needs one |
| Widening scope past the proposal's Impact table, or a change to the requirements | plan, build, review, ship |
| Changing, skipping or removing a test that's already on the target branch | build. The git hook wants a person's name in `Test-change-approved-by`. |
| Hard to undo, or seen outside the repo: creating a remote branch, creating or changing Jira or GitHub tickets the user didn't ask for, a migration that drops or rewrites data, deleting anything a person made | foundation, backlog, spec, build |
| What only the user knows: the requirements source, the product's capabilities, ticket trust, a person's name or group | foundation, product-sync, next, guardrails |
| A bug that doesn't reproduce; a step that still fails after its retries; an escalation | spec, build, review |
| A merge | Never done by the factory, in either mode |

## Record every answer

Each answer the factory gives is written down where a person will see it:

- **Jobs:** a line under `## Decisions` in the job record: `- <stage>: <question> → <answer> (auto) — <why>`. Ship copies the list into the PR description.
- **Foundation:** the step's Note in `docs/foundation-status.md`, and the step's commit message.
- **Proposals:** `factory.py approve <id> --what proposal --auto --reason "<why no gate applies>"`. It records the approval as `factory-auto for <user>`.

The user can say "ask me about <topic>" at any point. Treat that topic as critical for the rest of the session.
