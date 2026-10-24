---
name: skeleton
description: Build the walking skeleton, a thin end-to-end slice through every module, integration and cross-cutting concern, with tests, CI and one deploy. Use once during foundation, after docs/architecture.md is approved.
disable-model-invocation: true
---

# Skeleton

Build a **walking skeleton**: the thinnest slices that exercise every risky part of the architecture, built with the stack the ADRs chose, tested, wired into CI, and deployed once. Its job is to surface architecture and integration **gaps** now, while fixing them means changing one thin slice, rather than every task built on top of them. It also sets the patterns every later task copies, so build it cleanly and keep its features minimal.

## Steps

1. **Build the coverage checklist** in `docs/skeleton-gaps.md` (format below). It has one row for each of these:
   - every accepted ADR
   - every module in `docs/architecture.md`
   - every external system: payment provider, email, identity provider, third-party API
   - every cross-cutting concern: authentication and authorization, configuration and secrets, logging, error handling, database migrations, deployment
2. **Pick slices by risk.** Choose the fewest `P-n` slices (usually one or two) that together tick every checklist row, and favour the rows most likely to fail. Confirm the slices with the user.
3. **Lay out the project** so its directories match the modules in `docs/architecture.md`.
4. **Build the slices test-first**, following `${CLAUDE_PLUGIN_ROOT}/shared/TESTING.md`. Each slice gets one test per layer and one end-to-end test. Reach every external system for real, through its sandbox or test mode. Where that isn't possible, use a stub named `*Stub`, and mark that row `stubbed` with the reason.
5. **Log gaps as you go.** Whenever something turns out harder than the ADRs or `docs/architecture.md` assumed, or doesn't work at all, add it to the gap log and route it:
   - a gap that changes a choice goes to `${CLAUDE_PLUGIN_ROOT}/skills/decide/SKILL.md`
   - a gap that changes structure goes to `${CLAUDE_PLUGIN_ROOT}/skills/architecture/SKILL.md`

   Resolve each routed gap before finishing.
6. **Add commands** for build, lint and test, using the stack's standard tooling.
7. **Add CI** in `.github/workflows/ci.yml`, running the build, lint and test commands.
8. **Deploy once** to the target in the hosting ADR. If no target is available yet, run the production build locally the way it will run in production (for example, in its container), and log the missing target as a gap.
9. **Document** in `README.md` how to install, run, test and deploy the app.

## `skeleton-gaps.md` format

```markdown
# Skeleton coverage

| Item | Kind | Slice | Status | Test |
|------|------|-------|--------|------|
| ADR-0002 PostgreSQL | adr | P-1 | exercised | tests/e2e/signup.test.ts |
| Payments (Stripe) | external | P-3 | stubbed: no sandbox keys yet | tests/payments.test.ts |

# Gaps

| # | Found | Impact | Routed to | Resolution |
|---|-------|--------|-----------|------------|
| G-1 | Kysely lacks X | ADR-0001 | decide → ADR-0007 | resolved |
```

Coverage statuses: `pending`, `exercised`, `stubbed: <reason>`.

## Done check

- Every coverage row is `exercised` or `stubbed`, and each row names the test that exercises it. The user has accepted every stub.
- Every gap is resolved, or explicitly accepted by the user as a known risk.
- From a clean checkout, the build, lint and test commands all pass. Run them; don't infer.
- The CI workflow exists. If the repo has a remote, the latest run on the branch is green (`gh run list --limit 1`).
- The app has deployed once to its target, or its production build has run locally, with the missing target logged as a gap.
