# Module design

Design **deep modules**: a lot of behaviour behind a small interface, at a clean seam, tested through that interface. Use these terms exactly, in `docs/architecture.md`, plans and reviews.

## Vocabulary

- **Module**: anything with an interface and an implementation, at any scale: a function, a class, a package, a slice across layers.
- **Interface**: everything a caller must know to use the module correctly. That means not only the type signatures, but also invariants, ordering rules, error modes, required configuration and performance characteristics.
- **Implementation**: the code inside the module.
- **Depth**: how much behaviour a caller or a test gets per unit of interface they must learn. A module is **deep** when a small interface hides a lot of behaviour, and **shallow** when the interface is nearly as complex as what it hides.
- **Seam**: a place where behaviour can be changed without editing at that place. It is where an interface lives. Where to put a seam is a design decision in its own right.
- **Adapter**: a concrete thing that fills an interface at a seam, such as a Postgres repository or an in-memory fake.
- **Leverage**: what callers gain from depth. **Locality**: what maintainers gain, because change, bugs and knowledge stay in one place.

## Principles

- **Shrink the interface.** Fewer entry points, simpler parameters, and more complexity hidden inside.
- **The deletion test.** Imagine deleting the module. If its complexity vanishes, it was a pass-through. If the complexity reappears across its callers, it was earning its keep.
- **The interface is the test surface.** Callers and tests cross the same seam. Needing to test past the interface means the module is the wrong shape.
- **One adapter is a hypothetical seam; two adapters make it real.** Add a seam (a port) only when something actually varies across it, typically production plus test.
- **Internal seams stay internal.** A module may have private seams for its own tests. Don't expose them through its interface.

## Designing for testability

- **Accept dependencies; don't create them.** Pass the payment gateway in, rather than constructing it inside.
- **Return results rather than producing side effects** where possible: compute the discount, rather than mutating the cart.
- **Keep the surface small.** Fewer methods mean fewer tests and simpler setup.

## Dependencies decide the seam

| Dependency | Example | How to test across the seam |
|---|---|---|
| In-process | Pure logic, in-memory state | Directly through the interface; no adapter |
| Local stand-in exists | Postgres via a test database, in-memory filesystem | Run the stand-in in the test suite; the seam stays internal |
| Remote, owned by you | Your own internal service | A port at the seam: an HTTP adapter in production, an in-memory adapter in tests |
| Remote, third party | Stripe, email, SMS | A port at the seam with a mock adapter in tests |

## Comparing designs

When an interface's shape is genuinely in doubt, design it at least twice. Draft two or three radically different interfaces, for example one minimising entry points, one optimising for the most common caller, and one built around ports and adapters. Compare them on depth, locality and seam placement, then recommend one, or a hybrid.
