# Security

Every job is checked twice for security. Scanners check every job, and their results are facts, not judgement. A job that touches a sensitive area is also **flagged**: it gets misuse cases in its proposal, and a second reviewer that looks only at security. The developer running the factory approves security as they approve everything else. A security expert, from the group named in `.factory/config.md`, is brought in only when the security reviewer finds something that needs one.

## Sensitive areas

A change is security-sensitive when it touches any of these, or any path in the Sensitive paths table of `.factory/config.md`:

| Area | For example |
|---|---|
| Authentication and sessions | login, tokens, password reset, MFA |
| Authorization | roles, permissions, who can see or change which records |
| Money movement | payments, refunds, transfers, balances, fees, payouts |
| Personal data | identity, identity documents, contact details, account numbers |
| External input | a new or changed API endpoint, webhook, file upload or import |
| Secrets and cryptography | keys, signing, encryption, the secret store |
| Dependencies | a new dependency, or a major version upgrade |

## The flag

- **Agents only raise it.** The investigator raises it at spec. The reviewer raises it at review, when the diff touches an area the proposal didn't flag. No agent clears it.
- **The proposal records it**, in its Security section, by the format in `${CLAUDE_PLUGIN_ROOT}/skills/spec/SKILL.md`: `Sensitive: no`, or `Sensitive: yes — <areas>` with its misuse cases.
- **The developer may clear it.** When the developer thinks a flag is wrong, the proposal records `Sensitive: cleared by <their name> — <their reason>`. Ask for both, and never clear a flag on your own judgement. Clearing edits the proposal, so it voids the approval: approve again.
- A cleared flag stays visible: the PR description says who cleared it and why.

## Misuse cases

A flagged proposal adds **misuse cases** to its acceptance criteria: what an attacker or a careless user tries, and what the product does instead. For example: `AC-3 Given a customer signed in as A, when they request B's invoice, then the request is refused and nothing about B is returned`. Write at least one for each flagged area. They're tested like any other criterion, and the Security section lists them as `Misuse cases: AC-3, AC-4`. `factory.py validate` checks each one is a real criterion.

## Scanners

`guardrails` writes these rows into the Commands table of `.factory/config.md`. The defaults are free tools. Swap in the team's own tool, but keep the row names and its exit codes: 0 when clean, 1 on a finding, anything else when it can't run. `review` runs them through `factory.py scan <id>`:

| Command | Default | Runs in |
|---|---|---|
| Secrets (staged) | `gitleaks git --pre-commit --staged --redact --no-banner` | the pre-commit git hook, on what's about to be committed |
| Secrets | `gitleaks git --log-opts="<base>..HEAD" --redact --no-banner` | review, CI |
| Dependencies | `osv-scanner scan source -r .` | review, CI |
| Code scan | `semgrep scan --config p/default --error --baseline-commit <base>` | review, CI |

The secrets and code scans read any repo. The dependency scan reads only manifests and lockfiles, so it sees a repo's dependencies only when they're pinned:

| Stack | Read | Not read, so fix it first |
|---|---|---|
| Python | `requirements.txt` with pinned versions, `poetry.lock`, `Pipfile.lock`, `uv.lock` | a bare `pyproject.toml` or unpinned requirements: add a lockfile (`uv lock`, `poetry lock`, `pip-compile`) |
| JVM | Maven `pom.xml`, resolved with its transitive dependencies; Gradle `gradle.lockfile` | Gradle without a lockfile: turn on dependency locking and run `./gradlew dependencies --write-locks`, or use the team's own scanner |
| JavaScript | `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml` | no lockfile: commit the one the package manager writes |
| Go, Rust | `go.mod`, `Cargo.lock` | — |

A repo with no dependencies at all writes `none` as its Dependencies command, and `factory.py scan` skips that scan. The other two are never `none`.

`<base>` is `git merge-base <target-branch> HEAD`, so the secrets and code scans report only what the job's own commits add. The dependency scan sees the whole tree, so `factory.py scan` also runs it on the merge base, and only advisories missing there are the job's. The scan output goes to `.factory/runs/`, which is never committed.

- **Only new findings block.** A finding the job introduces is a blocking review finding: a secret, an advisory on a dependency the job adds or upgrades, or a code-scan finding in the diff. An advisory or finding that was already on the target branch goes in the review as a suggestion, with the count, so it stays visible without holding up every job.
- **A scan never gets skipped silently.** When a scanner is missing or can't run, stop, and tell the user how to install it (`brew install gitleaks osv-scanner semgrep`, or the team's own way). The pre-commit hook refuses the commit for the same reason. Only the user can waive the scans for one review, and `review.md` records who and why.
- **A secret that reached a commit counts as leaked**, even if it was never pushed: remove it, and tell the user to rotate it.

## When a security expert is needed

The security reviewer applies the standard in its checks. Most of what it finds, the build fixes, and the developer approves as usual. It marks a finding `expert` when the standard can't settle it, and only then is a security expert brought in:

- a design choice the checks don't cover: a new way of signing in, of granting access, or of handling keys or cryptography;
- a misuse case that can't be proven by a test;
- a risk the developer wants to accept rather than fix: a blocking security finding, or a new scan finding judged a false positive.

An `expert` finding escalates the job. The developer takes it to someone in the **Expert** group of `.factory/config.md`: an Azure DevOps group or a GitHub team, so one person's leave doesn't hold anything up. Their decision goes in `review.md` as `R-n decided by <name> — <decision>`: ask the user for both. A decision to fix becomes rework like any blocking finding. The job's PR then gets the Expert group as a required reviewer, as `HOSTS.md` says, so the expert confirms on the PR what was decided in their name. The factory never approves for them.
