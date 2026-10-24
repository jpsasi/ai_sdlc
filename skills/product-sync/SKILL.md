---
name: product-sync
description: Sync docs/product.md from the requirements sources — Confluence pages, local requirements files, or the existing code. Use when creating product.md, adding a feature's requirements, or when a source has changed.
argument-hint: "[confluence-page-url | requirements-file | requirements text | code [supplement]]"
disable-model-invocation: true
---

# Product sync

The **sources** are the source of truth for requirements, and `docs/product.md` is their in-repo snapshot. Every line of `product.md` traces to a source, or to a recorded clarification. A product usually starts with one source; each later feature can add another (a new Confluence page or a new chat brief), and every capability records the source it came from.

## Source types

| | `confluence` | `local` | `code` |
|---|---|---|---|
| Given as | A Confluence page URL | A file path, or requirements typed into the chat | The word `code`, optionally followed by a page URL or file path as a **supplement** |
| Source of truth | The page | The file (chat text is saved to `docs/requirements/<slug>.md` first) | The code for what exists; the supplement for what was intended |
| Approval | Page label `ready-for-dev` | The user's go-ahead to proceed with the text | The user confirms the derived capabilities |
| Version | Page version number | First 8 characters of `shasum -a 256 <file>` | `git rev-parse --short HEAD` |
| Answered questions | Recorded as `C-n`, and listed for the page owner to fold into the page | You fold the answer into the file directly; the user owns it | Recorded as `C-n` only |
| Outcomes | Answered, Ticket, Dropped | Answered or Dropped only | Answered or Dropped only |

Confluence is read-only: the factory never edits, comments on, or relabels a page. Questions reach the product team through Jira tickets and the lists you hand the user. Only `confluence` uses the label check, folding and Jira tickets. For `local` and `code`, every question closes in this session.

## Steps

1. **Resolve the sources.**
   - With `$ARGUMENTS`: a URL means `confluence`, a file path means `local`, and the word `code` means `code`. Any other text is requirements typed into the chat: save it to `docs/requirements/<slug>.md` and treat that file as a `local` source.
   - When `docs/product.md` already lists sources and `$ARGUMENTS` names a new one, ask whether it **adds** a feature (recommended) or **replaces** the existing sources. Add it to the `Sources:` list of `docs/foundation-status.md` accordingly.
   - Without `$ARGUMENTS`: re-sync every source on the `Sources:` list in `docs/foundation-status.md`, or ask the user if there is none.
2. **Confirm each new or changed source is approved.**
   - `confluence`: the page must carry the label `ready-for-dev`. Check with `searchConfluenceUsingCql` and the query `id = <pageId> AND label = "ready-for-dev"`. If the label is missing, stop and report the blocker "page not labeled ready-for-dev".
   - `local`: ask the user to confirm the text is what they want to build from.
   - `code`: approval comes in step 4, once the user has seen the derived capabilities.
3. **Analyse.** Dispatch the `factory:requirements-analyst` subagent once per new or changed source, with the current `docs/product.md` if it exists:
   - `confluence` or `local`: the job *draft product*, with the page id or file path. For `confluence` it also returns the page version. For `local`, compute the version yourself.
   - `code`: the job *derive product from code*, with the repo root and any supplement. It returns capabilities drafted from what the code does, and **known gaps**: places where the code and the supplement disagree.
4. **Write** `docs/product.md` from the drafts, in the format below. Merge each source's capabilities in, keeping existing ids and tagging each capability with its source. When updating, tell the user which requirements changed. For `code`, walk the user through the derived capabilities and correct them together.
5. **Check folding** (`confluence` only). Every `C-n` is meant to end up in the page body. Mark each one `folded` or `unfolded` from the analyst's report, and give the user the list of unfolded ones to chase with the page owner. Unfolded clarifications stay valid, so they never block the step.
6. **Close the questions** by grilling the user, by the method in `${CLAUDE_PLUGIN_ROOT}/shared/QUESTIONS.md`. The analyst's questions are the first frontier, and their "depends on" links order the rounds. Ask the rounds by the rules in `${CLAUDE_PLUGIN_ROOT}/shared/QUESTIONS.md`. For each question, show the quoted text, why it blocks, and your recommended answer. Every question ends in one of the outcomes its source type allows:
   - **Answered**: the user settles it now. Record it as `C-n` under Clarifications in `product.md`.
     - `confluence`: record who agreed it and when. At the end of the step, give the user the list of new `C-n`s to send to the page owner, who folds them into the page.
     - `local`: fold the answer into the source file, and mark the `C-n` `folded`.
     - `code`, for a known gap: the user rules which side is right. If the code is right, record it. If the supplement is right, record the gap as `K-n` under Known gaps, so the backlog plans a fix.
   - **Ticket** (`confluence` only): the user can't settle it now, because it needs the product team. Create a Jira Task with `createJiraIssue` in the project on the `Jira project:` line of `docs/foundation-status.md` (ask once and record it there).
     - Use the summary `[factory question] <title>`.
     - In the description, put the quote, the source link, the question, the options discussed, your recommendation, the scope, and the affected ids.
     - List it under Open questions in `product.md`, and give the user the ticket links to share with the product team.
   - **Dropped**: the user rules it non-blocking. Record nothing.

   After each round, list the tickets you are about to create, and create them once the user agrees.

   For `local` and `code`, the user owns the answers, so keep grilling until every question is Answered or Dropped. When the user is unsure, narrow the choice with your recommendation and its trade-offs; a choice can always be revisited later. If the session ends mid-grilling, the step stays `in_progress`, and the next run raises only the questions still open.
7. **Apply ticket scope** (`confluence` only). A ticket's scope is `foundation` when the answer could change domain terms, NFRs or architecture, and `capability` when it only affects specific `P-n`s. Mark each `capability`-scope capability in `product.md` with `Blocked by <KEY>`, and the factory takes no tasks for those capabilities until the ticket closes. Open tickets never halt Stage 0 on their own: the user decides whether to proceed with them open.
8. **Harvest closed tickets** (`confluence` only). On every run, check each ticket under Open questions with `getJiraIssue`. For a ticket whose status category is Done, take the resolution from its comments and record it as Answered, as above. Then remove it from Open questions and clear any `Blocked by` marks it caused.

## `product.md` format

```markdown
# Product: <name>

Synced: <date>

## Sources
| Ref | Type | Location | Version |
|-----|------|----------|---------|
| S-1 | code | repo | a1b2c3d |
| S-2 | confluence | <page url> | 14 |

## Problem and goals
## Users
## Capabilities
### P-1 <capability> · S-1
<what it does>
Acceptance hints:
- ...
## Non-functional requirements
NFR-1 <requirement with its number: latency, availability, volume, compliance...>
## Constraints
## Out of scope
## Clarifications
C-1 <question> → <answer> (<session | JIRA-KEY>, <who>, <date>) · folded | unfolded
## Known gaps
K-1 <where the code differs from the intent> → fix to <intended behaviour> (S-n)
## Open questions
- <question> — <JIRA-KEY> — scope: foundation | capability (P-n, ...)
```

Give every capability a stable `P-n` id, every non-functional requirement an `NFR-n` id, and every known gap a `K-n` id. Later stages trace their work to these ids. On re-sync, keep existing ids and give new items the next free number. Open questions are only ever non-empty for `confluence` sources.

## Done check

- `docs/product.md` exists, and every source's recorded version matches its current version.
- Every capability has a `P-n` id, a source, and at least one acceptance hint.
- `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/factory.py" check-docs` prints OK.
- `local` and `code` sources: every question is Answered or Dropped. For `code`, the user has confirmed the derived capabilities.
- `confluence` sources: every question is Answered, Ticketed, or Dropped. Open tickets don't fail the check. List each one, with its scope, for the user's proceed decision.
