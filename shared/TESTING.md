# Testing

The factory builds test-first: a **red** test, then the least code that turns it **green**, one slice at a time. This file is what makes those tests worth keeping. Name tests in `CONTEXT.md` terms.

## A good test

- **Tests behaviour through the public interface**, not implementation details. The code behind it can change completely without the test changing.
- **Reads like a specification**: "user can check out with a valid cart" names a capability.
- **Has one logical assertion**, on an observable outcome.
- **Survives refactoring.** If a test breaks while behaviour stays the same, it was testing the implementation.

```typescript
// Good: observable behaviour through the interface
test("user can check out with a valid cart", async () => {
  const cart = createCart();
  cart.add(product);
  const result = await checkout(cart, paymentMethod);
  expect(result.status).toBe("confirmed");
});
```

## Naming

Every test that proves an acceptance criterion is named `<job id> AC-n <behaviour>`, for example `REF-12 AC-2 retry applies credit once`. The validator (`factory.py`) traces each criterion to its test by that name, and checks that it ran. Put the name where the test runner reports it: the test title, or a `describe` block around the tests.

Where test names must be identifiers (pytest, Go, Rust, JUnit methods, XCTest), drop the job id's punctuation and keep the criterion: `test_ref12_ac2_retry_applies_credit_once`, `TestREF12AC2RetryAppliesCreditOnce`. Case and the `_` separators don't matter. Run the tests verbosely (`pytest -v`, `go test -v`) so each name appears in the results.

## Where tests go

Tests live at **seams**, the public interfaces in `DESIGN.md`, never against internals. The plan names the seam and the test for each step, so testing effort lands on the critical paths rather than on every edge case.

## Anti-patterns

- **Implementation-coupled**: mocks internal collaborators, tests private methods, or verifies through a side channel, such as querying the database instead of reading back through the interface.

  ```typescript
  // Bad: checks storage behind the interface's back
  await createUser({ name: "Alice" });
  expect(await db.query("SELECT * FROM users WHERE name = ?", ["Alice"])).toBeDefined();

  // Good: reads back through the interface
  const user = await createUser({ name: "Alice" });
  expect((await getUser(user.id)).name).toBe("Alice");
  ```

- **Tautological**: the expected value is computed the way the code computes it, so the test can never disagree with the code. Expected values come from an independent source: a known literal, a worked example, the spec.

  ```typescript
  // Bad
  expect(calculateTotal(items)).toBe(items.reduce((s, i) => s + i.price, 0));
  // Good
  expect(calculateTotal([{ price: 10 }, { price: 5 }])).toBe(15);
  ```

- **Horizontal slicing**: writing all the tests first, then all the code. It tests imagined behaviour. Go one test, one implementation, then repeat: each test a **tracer bullet** that learns from the last.
- **Interaction counting**: asserting that a method was called, how many times, or in what order. Assert on outcomes instead.

## Mocking

Mock only at **system boundaries**:

- third-party APIs (payment, email, SMS)
- time and randomness
- sometimes the database or filesystem, though a real test database is better

Never mock your own modules or anything you control. At a boundary, make mocking easy:

- **Inject the dependency** rather than constructing it inside.
- **Prefer one function per external operation** (`getUser`, `createOrder`) over one generic `fetch(endpoint, options)`. Each mock then returns one shape, with no conditional logic in the test setup.

## Characterization tests

Before changing code with little coverage (rated `bare` in `docs/baseline.md`), pin its current behaviour with **characterization tests**: run the code, record what it actually does, and assert exactly that, odd behaviour included. Unlike every other test here, they pass from the start. Their job is to turn red if the change breaks something it wasn't meant to.

## The loop

1. **Red**: write one failing test, and see it fail for the reason the step states.
2. **Green**: write only enough code to pass it. No speculative features, and nothing for tests you haven't written yet.
3. **Whole build green**: the full suite, lint and boundary checks.
4. Then the next slice.
