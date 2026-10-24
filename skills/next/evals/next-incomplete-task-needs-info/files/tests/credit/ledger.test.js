import { test } from "node:test";
import assert from "node:assert/strict";
import { addEntry, entriesOf, reset } from "../../src/credit/ledger.js";

test("T-1 AC-1 a ledger entry is recorded for its customer", () => {
  reset();
  addEntry("c1", 1000);
  assert.equal(entriesOf("c1").length, 1);
});
