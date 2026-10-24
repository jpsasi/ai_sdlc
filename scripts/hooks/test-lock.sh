#!/bin/sh
# Factory: runs the test command given as arguments, one run at a time per repo.
# Suites often share a test database or port, so overlapping runs fail each other.
# Every clone and worktree shares the lock; a lock left by a dead process is taken over.
#   factory-test-lock.sh make test
lock="$(git rev-parse --git-common-dir 2>/dev/null || echo .)/factory-tests.lock"
waited=0
until mkdir "$lock" 2>/dev/null; do
  pid=$(cat "$lock/pid" 2>/dev/null)
  if [ -n "$pid" ] && ! kill -0 "$pid" 2>/dev/null; then
    rm -rf "$lock"
    continue
  fi
  [ "$waited" -eq 0 ] && echo "factory: waiting for another test run (pid ${pid:-?}) to finish" >&2
  if [ "$waited" -ge "${FACTORY_TEST_LOCK_WAIT:-1800}" ]; then
    echo "factory: tests still locked after ${waited}s; if no run is active, remove $lock" >&2
    exit 1
  fi
  sleep 2
  waited=$((waited + 2))
done
echo $$ > "$lock/pid"
trap 'rm -rf "$lock"' EXIT
trap 'exit 130' INT TERM
"$@"
