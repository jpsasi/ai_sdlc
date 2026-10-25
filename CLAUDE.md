# Factory plugin

## Version bump

Every change to what the plugin ships bumps `version` in `.claude-plugin/plugin.json`, in the same PR. Installs are keyed by version, so without a bump, product repos keep serving the old files after `/plugin marketplace update`.

- **Ships:** `skills/`, `agents/`, `scripts/`, `shared/`, `.claude-plugin/`.
- **Doesn't ship:** `README.md`, `CLAUDE.md`, `skills/*/evals/`, `scripts/tests/`. A PR touching only these keeps its version.
- **Which part:** minor (`0.7.0` → `0.8.0`) for a new command, hook or stage behaviour; patch (`0.7.0` → `0.7.1`) for a fix or rewording that keeps behaviour.
- **Check before opening a PR:** when `git diff main --stat` lists a shipped path but not `.claude-plugin/plugin.json`, bump. One bump per PR, however many commits it has.
