#!/bin/sh
# Factory SessionStart hook: a repo's git hooks are committed in .factory/hooks/, but git runs
# them only once core.hooksPath points there, and that setting lives in each clone. Turn it on
# for this clone, or say why not. Prints nothing in repos the factory hasn't set up.
root=$(git rev-parse --show-toplevel 2>/dev/null) || exit 0
[ -f "$root/.factory/hooks/factory-git-guard.py" ] || exit 0
current=$(git -C "$root" config --get core.hooksPath)
case "$current" in
  .factory/hooks) exit 0 ;;
  "")
    git -C "$root" config core.hooksPath .factory/hooks &&
      echo "factory: enabled this repo's git hooks in this clone (git config core.hooksPath .factory/hooks)." ;;
  *)
    echo "factory: core.hooksPath is '$current', so the factory's git hooks in .factory/hooks/ don't run in this clone. Tell the user, and offer to combine them, as the guardrails skill describes." ;;
esac
exit 0
