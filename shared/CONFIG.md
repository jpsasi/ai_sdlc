# Delivery config

`.factory/config.md` in the product repo tells Stage 6 where code is hosted, where PRs go, and which environments exist. Nothing about hosts or environments is hard-coded in the factory. When a Stage 6 skill finds the file missing, or a value empty, it runs **Setup** below before going on.

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
```

- **Target branch** is where job PRs merge. Jobs branch from it, and it is usually the first environment's branch.
- **Environments** run in order: a job's merge deploys to the environment whose branch is the target, and `/factory:promote` moves work from one environment to the next. The table may be empty; then release ends at the merge.
- **Pipeline** is a GitHub Actions workflow name or file, or an Azure Pipelines pipeline name. Leave it empty for an environment with no automated deploy.
- **Ticket status** names are the tracker's own (Jira statuses, or GitHub labels). Leave a row empty to leave the ticket as it is.

## Setup

Ask by `QUESTIONS.md`, and never guess a branch or pipeline name. Propose what you can detect, and let the developer confirm.

1. **Host.** Read `git remote get-url origin`. A `github.com` URL means `github`. A `dev.azure.com/<org>/<project>/_git/<repo>` or `<org>.visualstudio.com/...` URL means `azure`. Take the repository from the URL. For any other host, tell the developer Stage 6 supports GitHub and Azure Repos, and stop.
2. **Tools.** Check the host's CLI works, as `HOSTS.md` says, and give the exact fix for anything that fails.
3. **Target branch.** Ask the developer for it, and confirm it exists with `git ls-remote --heads origin <branch>`.
4. **Merge rules.** Propose squash with delete source branch for job PRs, and a merge commit, keeping the source branch, for promotions. Squash keeps one commit per ticket, which promotion relies on to find ticket ids.
5. **Environments.** Ask which environments exist, in order. Each one needs its branch (confirm it exists), its deploy pipeline (offer the host's pipeline list from `HOSTS.md`), and the ticket status after a deploy (offer the tracker's statuses). "None" is a valid answer.
6. **Ticket statuses** for "PR open" and for "Merged, no environment".
7. **Protect** the target branch and every environment branch: `git config --add factory.protected <branch>` for each one not already listed, so the factory's git hooks guard them.
8. **Write** `.factory/config.md` on the current job branch, show it to the developer, and commit it as `config: delivery setup`.
