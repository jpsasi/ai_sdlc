# Prototypes

A prototype is **throwaway code that answers one question**, fast. Use one when a decision depends on something that is easier to feel than to argue about. The question decides its shape.

## Pick the shape

| Question | Shape |
|---|---|
| "Does this logic, state model or data shape hold up?" | **Logic prototype**: one self-contained HTML file that drives the model by clicking |
| "What should this look like?" | **UI prototype**: several radically different variants on one route, switchable in the browser |
| "Can this library, API or integration do what we need?" | **Spike**: the smallest script that exercises the risky call, against a sandbox |

When the question is ambiguous and the user is away, pick the shape that matches the surrounding code, and state your assumption at the top of the prototype.

## Rules for every prototype

1. **Mark it throwaway.** Name it so a reader can see at a glance that it's a prototype, placed next to what it's for.
2. **Trivial to run**: one command, or a file you double-click.
3. **No persistence**, unless persistence is the question. Then use a scratch store clearly named for deletion.
4. **No polish**: no tests, no abstractions, and only the error handling that keeps it running.
5. **Show the state.** After every action or variant switch, render the full relevant state.
6. **Capture the result.** Record the question and the verdict where the decision lives: the ADR, the proposal, or the design. Keep the prototype on a throwaway branch named `prototype/<topic>`, never on the default branch, and link it from the decision. Only the validated decision moves into real code, rewritten properly.

## Logic prototype

- **State the question** in a visible intro at the top of the page.
- **Isolate the logic** in one small, pure module inside the page: a reducer, a state machine, or pure functions over plain data, whichever fits the question. It never touches the DOM, so it can later be lifted into real code.
- **One file**: plain HTML, CSS and JS, with no framework, bundler or server, so anyone can open it, including non-developers.
- **Write in domain language** from `CONTEXT.md`, not code names.
- **Layout**, top to bottom:
  1. the question
  2. a readable state panel that highlights what just changed
  3. one free-play button per action
  4. guided scenarios, one per tab, each resetting to a known state, covering the happy path, a tricky edge case, and something that should be impossible
- The interesting moments are "wait, that shouldn't be possible". Those are bugs in the idea, which is what the prototype is for.

## UI prototype

- **Prefer an existing page.** Render the variants inside the real page, behind a `?variant=` URL parameter, with its real data and layout around them. Use a new throwaway route only when no host page exists, and follow the project's routing conventions.
- **Three variants by default, five at most.** They must be **structurally** different (layout, information hierarchy, primary action), not just different colours or copy.
- **A floating switcher bar** at the bottom: previous and next arrows plus the variant name. It updates the URL so a variant can be shared, responds to arrow keys except while typing, and is hidden in production builds.
- **Read-only.** Point any mutation at a stub.
- **When one wins**, rewrite it properly into the real page, and move the variants and switcher to the prototype branch.
