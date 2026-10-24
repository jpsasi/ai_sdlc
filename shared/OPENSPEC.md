# OpenSpec layout

The factory keeps work and behaviour in the OpenSpec layout, so the OpenSpec CLI (`openspec list`, `openspec validate`) also works on it.

```
openspec/
├── specs/<capability>/spec.md          living specs: what the system does today
└── changes/
    ├── <id>/                           one change per job, <id> = the job id
    │   ├── proposal.md                 why, what, acceptance criteria, impact, release, test plan
    │   ├── design.md                   how: approach, decisions, migrations, risks
    │   ├── tasks.md                    the test-first steps, ticked as they land
    │   ├── review.md                   review findings, one section per cycle
    │   └── specs/<capability>/spec.md  deltas: how this change alters the living specs
    └── archive/YYYY-MM-DD-<id>/        the change, once shipped
```

The **living specs** are the single source of truth for current behaviour. A change touches them only through its **deltas**, which `factory.py sync` merges at ship time. The one exception is **baselining**: writing a spec for a capability that has none yet (below).

## Capabilities

A capability is named by business area, in kebab case (`referral-credit`, `identity/user-auth`), never by code module. One capability may span several modules. Reuse an existing capability before inventing one.

## Living spec format

```markdown
# Referral Credit Specification

## Purpose
How referral credit is earned, held and spent.

## Requirements

### Requirement: Credit applies once per order
The checkout SHALL apply referral credit to an order at most once. `P-3` `REF-12 AC-1`

#### Scenario: Cart updated, then submitted
- **WHEN** a cart holding credit is updated, then submitted
- **THEN** the credit is deducted once
```

- Every requirement has a normative sentence using **SHALL** or **MUST**, and at least one `#### Scenario:` written as **WHEN** / **THEN** bullets (optionally **GIVEN** and **AND**).
- Requirement names are unique within a capability.
- Every requirement is **traceable**: at least one **tag** (an id in backticks: a capability `` `P-n` ``, or a job criterion `` `<id> AC-n` ``), or a **Source** line.

## Delta format

`openspec/changes/<id>/specs/<capability>/spec.md` holds one or more of these sections:

```markdown
## ADDED Requirements

### Requirement: Credit expires after 90 days
Referral credit SHALL expire 90 days after it is issued. `P-3` `REF-20 AC-1`

#### Scenario: Expired credit at checkout
- **WHEN** a customer checks out with credit issued 91 days ago
- **THEN** the credit is not applied

## MODIFIED Requirements

### Requirement: <exact name from the living spec>
<The complete new block, scenarios included. It replaces the old one entirely.>

## REMOVED Requirements

### Requirement: <exact existing name>
**Reason**: <why> · **Migration**: <what replaces it>

## RENAMED Requirements

- FROM: `### Requirement: <old name>`
- TO: `### Requirement: <new name>`
```

Every ADDED or MODIFIED requirement follows the living-spec rules above, and carries the job's `<id> AC-n` tags for the criteria it delivers. Sync applies RENAMED, then REMOVED, then MODIFIED, then ADDED.

**Which changes need deltas:** a change that alters observable behaviour needs a delta. A bug fix that restores behaviour the living spec already states needs none. A bug that exposes a wrong living spec MODIFIES it. A refactor or other chore never has deltas.

## Baselining a capability

A capability that a change touches, but that has no living spec yet, gets one first, describing **today's** behaviour before the change. It is written straight into `openspec/specs/`, and reviewed in the same PR as the change. Stage 0's `baseline` step does the same for the capabilities the user picks.

1. Read the capability's code and its tests, and any old docs for it.
2. Write one requirement per observable behaviour (inputs, outputs, rules, errors), each with a scenario.
3. Trace every requirement with a **Source** line instead of a tag:

   ```markdown
   ### Requirement: Symbol rate wins over group rate
   The engine SHALL use a rate set for the exact symbol before one set for its group.
   Source: test `tests/engine/rates.test.ts:88` · code `src/engine/rates.ts:41-57`
   ```

   A Source line has one or more parts joined by ` · `. Each part is a kind, followed by a backticked path:

   | Kind | Means |
   |---|---|
   | `test <path:line>` | A passing test asserts it. This is the strongest; prefer it. |
   | `code <path:lines>` | Read from the code, with no test pinning it. Also list it as a test gap. |
   | `imported <path>` | Carried over from an older spec, and checked against the code. Always pair it with `test` or `code`. |

4. **The code wins.** When old docs and the code disagree, write what the code does, and record the mismatch. When the code looks wrong, still write what it does, and record it as a suspected defect: a `K-n` known gap in `docs/product.md`.
5. Run `factory.py check-specs` until it prints OK.

When a later change MODIFIES a baselined requirement, it adds its tags; the Source line may stay.

**Specs that predate the factory.** When a repo already has OpenSpec specs, tagging every requirement is busywork. A capability tag under `## Purpose` (`` `P-3` ``) traces every requirement in that spec at once. Requirements added later by a change still carry their own `<id> AC-n` tags.

## The tool

`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/factory.py" <command>`, run from the repo root:

| Command | Does |
|---|---|
| `validate <id> --stage spec` | The proposal's criteria, test plan and capability. Deltas are well formed, consistent with the living specs, and tagged. |
| `validate <id> --stage plan` | The above, plus: the approval is current, the design has an approach, and every criterion is covered by a task |
| `validate <id> --stage build [--results <file>]` | The above, plus: every task is ticked, and every criterion has a test named `<id> AC-n …` that ran |
| `approve <id> --what proposal [--by <name>]` | Records who approved the proposal and its deltas, with a hash, so any later edit voids the approval |
| `sync <id>` | Merges the change's deltas into `openspec/specs/`, or writes nothing if any delta fails to apply |
| `archive <id>` | Moves the change to `openspec/changes/archive/YYYY-MM-DD-<id>/` |
| `check-specs` | Every living spec is well formed, and every requirement is traceable, with every Source path existing |
| `check-docs` | Unique ids in `docs/product.md` and `docs/backlog.md`, valid dependencies, no cycles |
