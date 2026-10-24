#!/usr/bin/env bash
set -eu
cp -R "$(dirname "$0")/files/." .
git init -q -b main
git -c user.name=fixture -c user.email=fixture@example.com add -A
git -c user.name=fixture -c user.email=fixture@example.com commit -qm "fixture: Stage 0 complete"
git switch -qc factory/T-7
mkdir -p .factory/jobs
cp "$(dirname "$0")/job-T-7.md" .factory/jobs/T-7.md
sed -i.bak 's/| T-4 | Credit history page | low | T-1 | credit, web | ready | |/&\n| T-7 | Withdraw credit as cash (bug) | high | | credit | in_progress | |/' docs/backlog.md && rm -f docs/backlog.md.bak
git -c user.name=fixture -c user.email=fixture@example.com add -A
git -c user.name=fixture -c user.email=fixture@example.com commit -qm "intake: queue T-7"
