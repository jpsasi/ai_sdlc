# While a subagent works

When a stage dispatches a subagent, this session would otherwise sit idle until it returns. Dispatch it in the background where the harness allows, then use the wait for the side work below. The subagent's result always comes first: when it returns, finish the action in hand, and go back to the stage.

The investigator, builder and reviewers share this checkout with you. Anything that changes what they see, or takes a lock they need, can corrupt their work. So, whatever the stage:

- **Never** edit a tracked file, or run a git command that writes: `commit`, `add`, `checkout`, `switch`, `merge`, `stash`, `reset`, `clean`, `rebase`. Read with `git --no-optional-locks status`, `log` and `diff`, which don't touch the index lock.
- **Never** run the test suite, a scan, a build or an install. They compete with the subagent's own runs for the test database, ports and CPU, and a scan of half-built code means nothing.
- **Never** claim, branch or relabel another ticket. Only one job is active at a time, by `JOBS.md`.
- **Write drafts** only to `.factory/runs/`, which is never committed. Check first that `git check-ignore -q .factory/runs/x` succeeds; if it doesn't, keep the drafts in the conversation instead.
- Skip a side task rather than guess. A draft is a starting point the stage checks against the final state, never a result.

## Side work, by stage

**Spec, while the investigator runs:**
- Read what step 3 resolves against: `docs/product.md` and its clarifications, the living specs of the capabilities the ticket names, and the ADR titles.
- Draft the parts of the proposal that the ticket alone decides into `.factory/runs/<id>-proposal.md`: the header, Why, the acceptance criteria as the ticket states them, and Out of scope. Step 5 starts from it, and brings it in line with what the investigator found.
- Find the ticket's own gaps: a criterion that isn't testable, two readings of one sentence. Ask the user about the ones that are decisions, not code facts, by `QUESTIONS.md`, so their answers arrive while the investigator works. With `Approvals: auto`, settle them by `AUTONOMY.md` instead, and ask only at a critical gate. Leave anything the code can answer to the investigator.

**Build, while the builder runs:**
- Check each finished step as its commit lands, by step 5.2 of the build skill, so a bad step is caught while later steps are still building, and the final check only covers the last ones.
- Draft the PR description into `.factory/runs/<id>-pr.md`, by step 5 of the ship skill, from what doesn't depend on the code: the ticket link and Why, the acceptance criteria, the capabilities and requirement counts from the deltas, migrations and config, the Security section, the approvals and the decisions. Leave the test results and the review summary to ship.
- Check what ship will need: `gh auth status` (or `az account show`), and the `PR merge` rule in `.factory/config.md`.

**Review, while the reviewers run:**
- Draft or finish the PR description, as for build.
- Send the reviewers nothing beyond what review step 4 lists, so they stay independent of this session.

**Any stage, once the above is done: look ahead.** Run steps 2 and 3 of `${CLAUDE_PLUGIN_ROOT}/skills/next/SKILL.md` to see which ticket it would pick next, but take none of its "On failure" actions: no relabeling, no comments, no backlog edits. When the likely next ticket is missing something only the user knows, tell the user now, so the ticket is ready when this job reaches `pr_open`.
