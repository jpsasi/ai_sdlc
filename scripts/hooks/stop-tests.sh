#!/bin/sh
# Factory: Stop hook that runs the test command given as arguments, and returns failures to Claude.
#   factory-stop-tests.sh make test
# Skips the run while the active job is `building`: build's red steps fail on purpose, and its
# own gate runs the suite. Runs through factory-test-lock.sh, so it never overlaps another run.
input=$(cat)
case "$input" in *'"stop_hook_active":true'*|*'"stop_hook_active": true'*) exit 0 ;; esac
branch=$(git symbolic-ref --short HEAD 2>/dev/null)
case "$branch" in
  factory/*)
    record=".factory/jobs/${branch#factory/}.md"
    grep -q '^Status: building' "$record" 2>/dev/null && exit 0 ;;
esac
out=$("$(dirname "$0")/factory-test-lock.sh" "$@" 2>&1) && exit 0
printf 'Tests failed (%s):\n%s\n' "$*" "$(printf '%s\n' "$out" | tail -n 80)" >&2
exit 2
