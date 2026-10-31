# Asking the user questions

Every factory skill that puts questions or decisions to the user follows this method: a relentless interview that ends in shared understanding, with nothing left silently assumed.

## The design tree

Treat the open questions as a **design tree**: each answer settles a branch and may open new questions that hang off it. The **frontier** is every open question whose prerequisites are already answered, meaning the questions you can ask *now* without guessing at answers you haven't heard. A question that depends on another open question waits for a later round.

## Rounds

- Ask **at most 3 questions per round**. When the frontier holds more, ask the 3 that unblock the most other questions, putting `foundation` scope first where scope applies. The rest wait.
- Number each question, and give your recommended answer, in this format:

  ```
  ❓ **Q1 - <title>**: <the question, with its context and the options>

  ➡️ <your recommended answer, and why>

  ---

  ❓ **Q2 - <title>**: ...
  ```

- Wait for the answers before the next round. Each round's answers can settle, drop, or add questions: recompute the frontier, then ask again.

## Facts versus decisions

Finding **facts** is your job, never the user's. When a question needs a fact you can look up (in the code, the docs, or a tool), look it up, or dispatch a subagent to find it. Questions that depend on that fact wait for it; ask the rest of the frontier meanwhile. **Decisions** belong to the user: put each one to them and wait.

## Approvals: auto

When `.factory/config.md` says `Approvals: auto`, answer each question on the frontier yourself with your recommendation, by `${CLAUDE_PLUGIN_ROOT}/shared/AUTONOMY.md`, and record it there. Ask only the critical ones, and the ones without a clear recommendation. The rounds above still order them. Skip the final confirmation below when nothing was asked.

## Done

The questioning is done when the frontier is empty: every branch visited, and nothing assumed. Confirm with the user that you've reached a shared understanding before acting on it.
