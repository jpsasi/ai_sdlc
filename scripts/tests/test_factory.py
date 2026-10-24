import contextlib
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import factory  # noqa: E402

PRODUCT = """# Product: Demo

## Capabilities
### P-1 Referral credit · S-1
Acceptance hints:
- credit is applied once
"""

PROPOSAL = """# Proposal REF-12: Credit applied twice

Ticket: REF-12 · Kind: bug · Delivers: P-1 · Priority: high

## Acceptance criteria
- AC-1 Given a cart with credit, when checkout submits, then credit applies once
- AC-2 Given a retried order, when it submits again, then credit is not applied again

## Test plan
- AC-1 → tests/credit.test.ts — "REF-12 AC-1 applies once"
- AC-2 → tests/credit.test.ts — "REF-12 AC-2 retry is idempotent"
"""

DESIGN = """# Design REF-12

## Approach
Apply credit only at submit, keyed on order id.
"""

TASKS = """# Tasks REF-12

- [{t}] 1. Credit applies once (AC-1)
        Test first: tests/credit.test.ts — "REF-12 AC-1 applies once"
        Verify: npm test
- [{t}] 2. Retry is idempotent (AC-2)
        Test first: tests/credit.test.ts — "REF-12 AC-2 retry is idempotent"
        Verify: npm test
"""

LIVING = """# Referral Credit Specification

## Purpose
How referral credit works.

## Requirements

### Requirement: Credit applies at checkout
The checkout SHALL apply referral credit to the order. `P-1`

#### Scenario: Checkout with credit
- **WHEN** a cart holding credit is submitted
- **THEN** the credit is deducted
"""

DELTA = """## MODIFIED Requirements

### Requirement: Credit applies at checkout
The checkout SHALL apply referral credit to an order at most once. `P-1` `REF-12 AC-1`

#### Scenario: Updated then submitted
- **WHEN** a cart holding credit is updated, then submitted
- **THEN** the credit is deducted once

## ADDED Requirements

### Requirement: Retried orders keep their credit
A retried order MUST NOT receive credit a second time. `REF-12 AC-2`

#### Scenario: Retry
- **WHEN** the same order is submitted twice
- **THEN** credit is applied once
"""

JOB = """# Job REF-12

Status: building

## History
- queued
"""

TESTS = """test("REF-12 AC-1 applies once", () => {});
test("REF-12 AC-2 retry is idempotent", () => {});
"""

C = "openspec/changes/REF-12"


class FactoryTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cwd = os.getcwd()
        os.chdir(self.tmp.name)
        self.write("docs/product.md", PRODUCT)
        self.write(f"{C}/proposal.md", PROPOSAL)
        self.write(f"{C}/design.md", DESIGN)
        self.write(f"{C}/tasks.md", TASKS.format(t="x"))
        self.write(f"{C}/specs/referral-credit/spec.md", DELTA)
        self.write("openspec/specs/referral-credit/spec.md", LIVING)
        self.write(".factory/jobs/REF-12.md", JOB)
        self.write("tests/credit.test.ts", TESTS)

    def tearDown(self):
        os.chdir(self.cwd)
        self.tmp.cleanup()

    def write(self, path, text):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(text, encoding="utf-8")

    def run_cli(self, *argv):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            code = factory.main(list(argv))
        return code, out.getvalue()

    def approve(self):
        return self.run_cli("approve", "REF-12", "--what", "proposal", "--by", "Sasi")

    def assertProblem(self, result, text):
        code, out = result
        self.assertEqual(code, 1, out)
        self.assertIn(text, out)

    # spec stage

    def test_spec_stage_ok(self):
        self.assertEqual(self.run_cli("validate", "REF-12", "--stage", "spec"), (0, "OK\n"))

    def test_ac_missing_from_test_plan(self):
        self.write(f"{C}/proposal.md", PROPOSAL.replace('- AC-2 → tests/credit.test.ts — "REF-12 AC-2 retry is idempotent"\n', ""))
        self.assertProblem(self.run_cli("validate", "REF-12", "--stage", "spec"), "AC-2 has no entry in the proposal's Test plan")

    def test_delivers_unknown_capability(self):
        self.write(f"{C}/proposal.md", PROPOSAL.replace("Delivers: P-1", "Delivers: P-9"))
        self.assertProblem(self.run_cli("validate", "REF-12", "--stage", "spec"), "P-9")

    def test_delta_modifies_missing_requirement(self):
        self.write(f"{C}/specs/referral-credit/spec.md", DELTA.replace("### Requirement: Credit applies at checkout", "### Requirement: Nope", 1))
        self.assertProblem(self.run_cli("validate", "REF-12", "--stage", "spec"), "cannot modify missing requirement 'Nope'")

    def test_delta_requirement_without_scenario_or_shall(self):
        self.write(f"{C}/specs/referral-credit/spec.md", "## ADDED Requirements\n\n### Requirement: Vague\nCredit is nice. `REF-12 AC-1`\n")
        code, out = self.run_cli("validate", "REF-12", "--stage", "spec")
        self.assertEqual(code, 1)
        self.assertIn("'Vague' has no SHALL or MUST", out)
        self.assertIn("'Vague' has no '#### Scenario:'", out)

    def test_delta_tags_undefined_criterion(self):
        self.write(f"{C}/specs/referral-credit/spec.md", DELTA.replace("`REF-12 AC-2`", "`REF-12 AC-7`"))
        self.assertProblem(self.run_cli("validate", "REF-12", "--stage", "spec"), "tags REF-12 AC-7, which the proposal doesn't define")

    def test_delta_unknown_section(self):
        self.write(f"{C}/specs/referral-credit/spec.md", DELTA + "\n## Notes\nhello\n")
        self.assertProblem(self.run_cli("validate", "REF-12", "--stage", "spec"), "unknown section '## Notes'")

    # approval and plan stage

    def test_plan_stage_needs_approval(self):
        self.assertProblem(self.run_cli("validate", "REF-12", "--stage", "plan"), "no recorded proposal approval")

    def test_approval_then_plan_ok(self):
        self.assertEqual(self.approve()[0], 0)
        self.assertEqual(self.run_cli("validate", "REF-12", "--stage", "plan"), (0, "OK\n"))

    def test_delta_edit_invalidates_approval(self):
        self.approve()
        self.write(f"{C}/specs/referral-credit/spec.md", DELTA.replace("at most once", "exactly once"))
        self.assertProblem(self.run_cli("validate", "REF-12", "--stage", "plan"), "changed after approval")

    def test_task_missing_ac_coverage(self):
        self.approve()
        self.write(f"{C}/tasks.md", TASKS.format(t="x").replace("(AC-2)", "").replace("REF-12 AC-2", "REF-12"))
        self.assertProblem(self.run_cli("validate", "REF-12", "--stage", "plan"), "AC-2 is not covered by any task")

    # build stage

    def test_build_ok_with_results(self):
        self.approve()
        self.write("out.txt", "PASS REF-12 AC-1 applies once\nPASS REF-12 AC-2 retry is idempotent\n")
        self.assertEqual(self.run_cli("validate", "REF-12", "--stage", "build", "--results", "out.txt"), (0, "OK\n"))

    def test_build_unticked_and_untested(self):
        self.approve()
        self.write(f"{C}/tasks.md", TASKS.format(t=" "))
        self.write("tests/credit.test.ts", 'test("REF-12 AC-1 applies once", () => {});\n')
        code, out = self.run_cli("validate", "REF-12", "--stage", "build")
        self.assertEqual(code, 1)
        self.assertIn("task 1 is not ticked", out)
        self.assertIn("no test named 'REF-12 AC-2 ...'", out)

    def test_build_test_did_not_run(self):
        self.approve()
        self.write("out.txt", "PASS REF-12 AC-1 applies once\n")
        self.assertProblem(self.run_cli("validate", "REF-12", "--stage", "build", "--results", "out.txt"),
                           "'REF-12 AC-2' does not appear in the test results")

    def test_build_ignores_binary_test_fixtures(self):
        self.approve()
        Path("tests/fixtures").mkdir(parents=True)
        Path("tests/fixtures/data.csv.zip").write_bytes(b"PK\x03\x04\xff\xfe\x80 binary")
        self.write("out.txt", "PASS REF-12 AC-1 applies once\nPASS REF-12 AC-2 retry is idempotent\n")
        self.assertEqual(self.run_cli("validate", "REF-12", "--stage", "build", "--results", "out.txt"), (0, "OK\n"))

    def test_build_accepts_identifier_style_names(self):
        # pytest, Go, Rust and JUnit names can't hold spaces or dashes
        self.approve()
        self.write("tests/test_credit.py", "def test_ref12_ac1_applies_once(): ...\ndef test_REF12_AC2_retry(): ...\n")
        self.write("tests/credit.test.ts", "")
        self.write("out.txt", "tests/test_credit.py::test_ref12_ac1_applies_once PASSED\n"
                              "tests/test_credit.py::test_REF12_AC2_retry PASSED\n")
        self.assertEqual(self.run_cli("validate", "REF-12", "--stage", "build", "--results", "out.txt"), (0, "OK\n"))

    def test_identifier_style_names_need_the_exact_criterion(self):
        self.approve()
        self.write("tests/test_credit.py", "def test_ref12_ac1_applies_once(): ...\nfunc TestREF12AC21Other() {}\n")
        self.write("tests/credit.test.ts", "")
        self.assertProblem(self.run_cli("validate", "REF-12", "--stage", "build"), "no test named 'REF-12 AC-2 ...'")

    # sync, archive, check-specs

    def test_sync_applies_delta_then_archive(self):
        self.assertEqual(self.run_cli("sync", "REF-12")[0], 0)
        living = Path("openspec/specs/referral-credit/spec.md").read_text()
        self.assertIn("at most once", living)
        self.assertIn("### Requirement: Retried orders keep their credit", living)
        self.assertEqual(living.count("### Requirement: Credit applies at checkout"), 1)
        self.assertEqual(self.run_cli("check-specs"), (0, "OK\n"))
        code, out = self.run_cli("archive", "REF-12")
        self.assertEqual(code, 0)
        self.assertFalse(Path(C).exists())
        self.assertEqual(len(list(Path("openspec/changes/archive").glob("*-REF-12"))), 1)

    def test_sync_writes_nothing_when_a_delta_fails(self):
        self.write(f"{C}/specs/other/spec.md", "## REMOVED Requirements\n\n### Requirement: Ghost\n**Reason**: x\n")
        self.assertProblem(self.run_cli("sync", "REF-12"), "cannot remove missing requirement 'Ghost'")
        self.assertEqual(Path("openspec/specs/referral-credit/spec.md").read_text(), LIVING)

    def test_sync_creates_new_capability(self):
        self.write(f"{C}/specs/referral-credit/spec.md", DELTA.split("## ADDED Requirements")[0])
        self.write(f"{C}/specs/payouts/spec.md", "## ADDED Requirements\n\n" + DELTA.split("## ADDED Requirements\n\n")[1])
        self.assertEqual(self.run_cli("sync", "REF-12")[0], 0)
        self.assertTrue(Path("openspec/specs/payouts/spec.md").read_text().startswith("# Payouts Specification"))
        self.assertEqual(self.run_cli("check-specs"), (0, "OK\n"))

    def test_check_specs_untraced_and_missing_source(self):
        self.write("openspec/specs/rates/spec.md", """# Rates Specification

## Purpose
Rates.

## Requirements

### Requirement: Symbol rate wins
The engine SHALL use the symbol rate first.
Source: test `tests/rates.test.ts:88`

#### Scenario: Own rate
- **WHEN** EURUSD has its own rate
- **THEN** it is used

### Requirement: Untraced
The engine SHALL do something.

#### Scenario: It does
- **WHEN** x
- **THEN** y
""")
        code, out = self.run_cli("check-specs")
        self.assertEqual(code, 1)
        self.assertIn("cites test `tests/rates.test.ts:88`, which doesn't exist", out)
        self.assertIn("'Untraced' has no tag and no Source line", out)

    def test_approve_and_validate_after_archive(self):
        self.approve()
        self.run_cli("sync", "REF-12")
        self.run_cli("archive", "REF-12")
        self.write("out.txt", "PASS REF-12 AC-1\nPASS REF-12 AC-2\n")
        self.assertEqual(self.run_cli("validate", "REF-12", "--stage", "build", "--results", "out.txt"), (0, "OK\n"))
        self.assertEqual(self.approve()[0], 0)

    # check-docs

    def test_check_docs_backlog_cycle_and_unknown(self):
        self.write("docs/backlog.md", """# Backlog

## P-1 Referral credit
| Task | Title | Priority | Depends on | Modules | Status | Ticket |
|------|-------|----------|------------|---------|--------|--------|
| T-1 | One | high | T-2 | credit | ready | |
| T-2 | Two | high | T-1 | credit | ready | |
| T-3 | Three | low | T-9 | credit | ready | |

## P-7 Unknown
""")
        code, out = self.run_cli("check-docs")
        self.assertEqual(code, 1)
        self.assertIn("dependency cycle", out)
        self.assertIn("T-3 depends on T-9", out)
        self.assertIn("backlog section P-7", out)

    def test_check_docs_ok(self):
        self.assertEqual(self.run_cli("check-docs"), (0, "OK\n"))


if __name__ == "__main__":
    unittest.main()
