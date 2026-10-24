# Shared by the factory's git hooks: prints the protected branch patterns, one per line.
# The default branch is always protected; add others with
#   git config --add factory.protected '<branch or pattern>'
default=$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null | sed 's|^origin/||')
[ -n "$default" ] || default=$(git config --get init.defaultBranch 2>/dev/null)
[ -n "$default" ] || default=main
echo "$default"
git config --get-all factory.protected 2>/dev/null
