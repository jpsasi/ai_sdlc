# Hosting operations

Every Stage 6 operation, per host. The host, repository and pipelines come from `.factory/config.md`. To support another host, add a column.

**People own every merge.** The factory opens and updates pull requests, and follows pipelines. It never approves, votes on, completes or merges a PR, and never bypasses a branch policy or check. Tell the person completing a PR which merge option the config names.

## Tools

| | GitHub | Azure Repos |
|---|---|---|
| CLI works | `gh auth status` | `az --version` with the `azure-devops` extension (`az extension add --name azure-devops`), then `az devops project show --project <project> --organization https://dev.azure.com/<org>` |
| Sign in | `! gh auth login` | `! az login` |
| Defaults | (none needed) | `az devops configure --defaults organization=https://dev.azure.com/<org> project=<project>` |

## Pull requests

| Do | GitHub | Azure Repos |
|---|---|---|
| Create | `gh pr create --base <target> --head <branch> --title "<title>" --body-file <file>` | `az repos pr create --repository <repo> --source-branch <branch> --target-branch <target> --title "<title>" --description "<markdown>"` |
| Require the security expert | add `--reviewer <org/team>` to Create. GitHub can't require a reviewer on one PR: say in the description that their approval is required before merging | add `--required-reviewers "<group>"` to Create (`--reviewers` only adds optional ones) |
| Update the description | `gh pr edit <n> --body-file <file>` | `az repos pr update --id <id> --description "<markdown>"` |
| State and merge commit | `gh pr view <n> --json state,mergeCommit,mergedAt,url` (`MERGED` means completed) | `az repos pr show --id <id> --query "{status: status, merge: lastMergeCommit.commitId}"` (`completed` means merged) |
| Checks and policies | `gh pr checks <n>` | `az repos pr policy list --id <id>` |
| Review comments | `gh pr view <n> --json reviews,comments`, plus inline comments from `gh api repos/{owner}/{repo}/pulls/<n>/comments` | `az devops invoke --area git --resource pullRequestThreads --route-parameters project=<project> repositoryId=<repo> pullRequestId=<id> --http-method GET` (threads whose `status` is `active`) |
| PRs between two branches | `gh pr list --head <source> --base <target> --state all --limit 5 --json number,state,url,mergeCommit` | `az repos pr list --source-branch <source> --target-branch <target> --status all --top 5` |
| Web link | `url` from `gh pr view` | `https://dev.azure.com/<org>/<project>/_git/<repo>/pullrequest/<id>` |

Ticket keys go in the PR title and description. With Jira, skip Azure's `--work-items` flag, which takes Azure Boards ids.

## Pipelines

| Do | GitHub Actions | Azure Pipelines |
|---|---|---|
| List pipelines | `gh workflow list` | `az pipelines list --query "[].name"` |
| Runs for a branch | `gh run list --workflow <workflow> --branch <branch> --limit 10 --json databaseId,headSha,status,conclusion,url` | `az pipelines runs list --pipeline-ids <id> --branch <branch> --top 10` (pipeline id from `az pipelines show --name <name> --query id`) |
| Wait for a run | `gh run watch <run-id> --exit-status` | Re-check `az pipelines runs show --id <run>` until `status` is `completed`, then read `result` |
| Result and link | `conclusion` (`success`, `failure`, `cancelled`) and `url` | `result` (`succeeded`, `failed`, `canceled`) and `_links.web.href` |

**Finding the run that deploys a commit:** take the newest run on the environment's branch whose commit contains the merge, meaning `git merge-base --is-ancestor <merge> <run commit>` succeeds. A later run counts too, so after a failed deploy is fixed, re-running picks up the run that carries both. If no run appears within a few minutes of the merge, the pipeline isn't triggered on that branch: report it rather than waiting.

## Branches

| Do | Command (both hosts) |
|---|---|
| Push a job branch | `git push -u origin factory/<id>` (the git hooks refuse protected branches) |
| Delete a merged branch | `git push origin --delete <branch>`, then `git fetch --prune` and `git branch -D <branch>` |
| What a promotion carries | `git fetch origin`, then `git log --format='%H %s%n%b' origin/<to>..origin/<from>` |
