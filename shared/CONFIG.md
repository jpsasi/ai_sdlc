# Delivery config

`.factory/config.md` in the product repo tells Stage 6 where code is hosted, where PRs go, and which environments exist, and tells review which security scans to run. Nothing about hosts, environments or scanners is hard-coded in the factory. foundation writes the host, repository and target branch, and `guardrails` adds the scan commands and the Security section; when a Stage 6 skill finds the file missing, or a host, branch or environment value empty, it runs **Setup** below before going on.

## Format

```markdown
# Factory config

Host: github | azure
Repository: <owner/repo> | <organization/project/repository>
Target branch: develop
PR merge: squash, delete source branch
Promotion merge: merge commit, keep source branch

## Environments
| Order | Environment | Branch | Pipeline | Ticket status after deploy |
|-------|-------------|--------|----------|----------------------------|
| 1 | dev | develop | deploy-dev | Dev testing |
| 2 | qa | qa | deploy-qa | In QA |

## Ticket statuses
| Event | Status |
|-------|--------|
| PR open | In review |
| Merged, no environment | Done |

## Commands
| Command | Run |
|---------|-----|
| Secrets (staged) | gitleaks git --pre-commit --staged --redact --no-banner |
| Secrets | gitleaks git --log-opts="<base>..HEAD" --redact --no-banner |
| Dependencies | osv-scanner scan source -r . |
| Code scan | semgrep scan --config p/default --error --baseline-commit <base> |

## Security
Expert: @acme/security

| Sensitive path | Area |
|----------------|------|
| src/payments/** | money movement |
| src/auth/** | authentication |
```

- **Target branch** is where job PRs merge. Jobs branch from it, and it is usually the first environment's branch.
- **Environments** run in order: a job's merge deploys to the environment whose branch is the target, and `/factory:promote` moves work from one environment to the next. The table may be empty; then release ends at the merge.
- **Pipeline** is a GitHub Actions workflow name or file, or an Azure Pipelines pipeline name. Leave it empty for an environment with no automated deploy.
- **Ticket status** names are the tracker's own (Jira statuses, or GitHub labels). Leave a row empty to leave the ticket as it is.
- **Commands** are the security scans, by `${CLAUDE_PLUGIN_ROOT}/shared/SECURITY.md`. `<base>` is filled in with the merge base of the job branch and the target branch. Write a `|` inside a command as `\|`. Every repo has all four rows; Dependencies may be `none` in a repo with no dependencies.
- **Security:** *Expert* is the group of security experts a job is escalated to when the security reviewer finds something the standard can't settle: an Azure DevOps group (`[<project>]\<group>`) or a GitHub team (`@<org>/<team>`). *Sensitive paths* are this repo's code in a sensitive area, as glob patterns. A job that touches one is always flagged.

## Setup

Ask only for values the file doesn't have yet: foundation already sets the host, repository and target branch. Ask by `QUESTIONS.md`, and never guess a branch or pipeline name. Propose what you can detect, and let the developer confirm.

1. **Host.** Read `git remote get-url origin`. A `github.com` URL means `github`. A `dev.azure.com/<org>/<project>/_git/<repo>` or `<org>.visualstudio.com/...` URL means `azure`. Take the repository from the URL. For any other host, tell the developer Stage 6 supports GitHub and Azure Repos, and stop.
2. **Tools.** Check the host's CLI works, as `HOSTS.md` says, and give the exact fix for anything that fails.
3. **Target branch.** Ask the developer for it, proposing the default branch, and confirm it exists with `git ls-remote --heads origin <branch>`.
4. **Merge rules.** Propose squash with delete source branch for job PRs, and a merge commit, keeping the source branch, for promotions. Squash keeps one commit per ticket, which promotion relies on to find ticket ids.
5. **Environments.** Ask which environments exist, in order. Each one needs its branch (confirm it exists), its deploy pipeline (offer the host's pipeline list from `HOSTS.md`), and the ticket status after a deploy (offer the tracker's statuses). "None" is a valid answer.
6. **Ticket statuses** for "PR open" and for "Merged, no environment".
7. **Security expert.** Ask for the group of security experts that jobs are escalated to. Check it exists, and never take a single person's name: `az devops security group list --project <project>` on Azure, `gh api orgs/<org>/teams/<team>` on GitHub.
8. **Protect** the target branch and every environment branch: `git config --add factory.protected <branch>` for each one not already listed, so the factory's git hooks guard them.
9. **Write** `.factory/config.md` on the current branch, show it to the developer, and commit it as `config: delivery setup`.
