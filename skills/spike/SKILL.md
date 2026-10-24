---
name: spike
description: Try an idea before it becomes requirements — a time-boxed experiment on a prototype branch that never merges, ending in a findings note the product team can turn into requirements.
disable-model-invocation: true
argument-hint: "<idea> | <spike name> (to continue or finish)"
---

# Spike

Answer one question about an idea with working code, fast, and leave a findings note behind. A spike is an **experiment**, not a delivery. Its code never merges; only its findings do. If the idea is worth building, it becomes requirements, then goes through `/factory:foundation` (re-sync) and the backlog like any other feature. Build the spike by `${CLAUDE_PLUGIN_ROOT}/shared/PROTOTYPE.md`.

With the name of a spike whose branch exists, switch to it and continue at the step it has reached, from its `docs/spikes/<name>.md`. Otherwise start at step 1.

## Steps

1. **Frame.** Agree with the user, by `${CLAUDE_PLUGIN_ROOT}/shared/QUESTIONS.md`:
   - **the question**, in one sentence ("Can we compute credit per account type without a schema change?")
   - **what counts as an answer**: the evidence that settles it, such as a working path, a measurement, or a prototype screen
   - **the time-box**: the user's call; suggest 1 to 3 days
   - **what's out of scope**: production quality, full tests, edge cases

   When the idea is already clear enough to write as requirements, say so: it can skip the spike.
2. **Start.** Create `prototype/<name>` from the latest target branch. Write `docs/spikes/<name>.md` with the question, the answer criteria, the time-box and a Log section, and commit it.
3. **Explore.** Build the smallest thing that answers the question, by the prototype's shape in `PROTOTYPE.md`. Shortcuts in the code are fine. These still hold:
   - touch only local or development resources, never shared or production data or configuration
   - no secrets in the code
   - commit as you go

   Log what you tried and what happened, with numbers where there are any. When the time-box runs out, stop, and ask the user whether to extend it (by how much) or finish.
4. **Findings.** Complete `docs/spikes/<name>.md`:

   ```markdown
   # Spike: <question>

   Branch: prototype/<name> · <dates> · <who>

   ## Answer
   Yes / No / Partly, in one paragraph.

   ## Evidence
   What was built and what it showed: measurements, screenshots, the commits that matter.

   ## What it means for users
   In business words, for the product team. No tables, classes or endpoints.

   ## Draft requirements
   Possible capabilities, rules and edge cases to start from, marked as a draft. The product team owns the requirements.

   ## Notes for engineering
   Approach, reusable pieces, technical risks, and what a real build needs that the spike skipped.

   ## Recommendation
   Build it (as requirements) / do it as a small task / drop it, and why.
   ```

   Commit it on the spike branch.
5. **Publish the findings.** Create `factory/spike-<name>-findings` from the latest target branch, and copy `docs/spikes/<name>.md` onto it, with nothing else. Commit it. Tell the user to open a pull request for that branch. Leave `prototype/<name>` unmerged as the reference for whoever builds the feature, and delete it only when the user asks.

## Done check

- The findings note answers the question, with evidence, and gives a recommendation.
- The findings are on their own branch, ready for a pull request. The spike's code is only on `prototype/<name>`.
