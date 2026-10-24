---
name: baseline
description: Prove an existing codebase is workable for agents — build, test, lint, CI, flaky tests and per-module test coverage — and record it in docs/baseline.md. Use during foundation on an existing codebase, in place of the skeleton.
disable-model-invocation: true
---

# Baseline

An existing app needs no skeleton. It needs proof that agents can change it safely. Measure where it stands today, so later stages know where changes are safe and where they must add tests first.

## Steps

1. **Find the commands** for install, build, lint and test, from the repo's scripts, Makefile, CI config and README. Record them.
2. **Run them** from a clean checkout. When one fails, fix the environment with the user (missing tool, service or env var), and record what it took in `README.md`. A command that can't be made to pass is a gap.
3. **Find known-red and flaky tests.** Run the full test suite three times. A test that fails every time is **known red**: later jobs aren't blamed for it, and it stays known red until a job fixes it. A test whose result differs between runs is **flaky**.
4. **Map coverage per module.** Run the stack's coverage tool, and map the results onto the modules in `docs/architecture.md`. Rate each module:
   - `safe`: well covered, so change it directly
   - `thin`: some coverage, so add tests near any change
   - `bare`: little or no coverage, so pin its behaviour with **characterization tests** before changing it
5. **Check CI.** Confirm that CI runs the build, lint and test commands. If the repo has a remote, confirm the latest run on the default branch is green (`gh run list --limit 1`). If CI doesn't exist, add `.github/workflows/ci.yml`.
6. **Map and baseline capabilities.** List the capabilities: the business areas the system serves, from its routes, screens, modules and `docs/product.md`. Propose which to baseline now: those with work coming soon, plus the user's own picks. The rest get baselined by `/factory:spec` the first time a job touches them. Write a living spec for each chosen capability, by *Baselining a capability* in `${CLAUDE_PLUGIN_ROOT}/shared/OPENSPEC.md`, and commit each capability on its own, so it can be reviewed one area at a time. Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/factory.py" check-specs` until it prints OK.
7. **Record** everything in `docs/baseline.md`, in the format below.

## `baseline.md` format

```markdown
# Baseline

Commit: <short hash> · Date: <date>

## Commands
| Purpose | Command | Result |
|---------|---------|--------|
| test | npm test | pass (412 tests, 3m10s) |

## Known red
- tests/reports/export.test.ts — "exports CSV" — fails on every run

## Flaky tests
- tests/payments/retry.test.ts — passed 2 of 3 runs

## Coverage by module
| Module | Line coverage | Rating |
|--------|---------------|--------|
| billing | 81% | safe |
| legacy-reports | 4% | bare |

## Gaps
| # | Found | Routed to | Resolution |
|---|-------|-----------|------------|
| G-1 | e2e tests need a local Redis | README | documented |
```

## Done check

- The build, lint and test commands pass from a clean checkout, or each failure is a gap the user accepted as a known risk.
- Every module in `docs/architecture.md` has a coverage rating.
- Every chosen capability has a living spec, and `check-specs` prints OK. Mismatches and suspected defects are recorded as `K-n` known gaps.
- Known-red and flaky tests are listed. The user decides whether to fix or quarantine each flaky one.
- CI runs the commands, and its latest run is green, or the failure is a gap the user accepted.
