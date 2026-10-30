import contextlib
import io
import os
import subprocess
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

## Security
Sensitive: no

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

    # security

    def test_proposal_needs_a_security_section(self):
        self.write(f"{C}/proposal.md", PROPOSAL.replace("## Security\nSensitive: no\n", ""))
        self.assertProblem(self.run_cli("validate", "REF-12", "--stage", "spec"), "no '## Security' section")

    def test_sensitive_proposal_names_its_areas_and_misuse_cases(self):
        self.write(f"{C}/proposal.md", PROPOSAL.replace("Sensitive: no", "Sensitive: yes"))
        result = self.run_cli("validate", "REF-12", "--stage", "spec")
        self.assertProblem(result, "names its areas")
        self.assertProblem(result, "lists its misuse cases")
        self.write(f"{C}/proposal.md", PROPOSAL.replace("Sensitive: no", "Sensitive: yes — money movement\nMisuse cases: AC-2, AC-7"))
        self.assertProblem(self.run_cli("validate", "REF-12", "--stage", "spec"), "misuse case AC-7 isn't an acceptance criterion")
        self.write(f"{C}/proposal.md", PROPOSAL.replace("Sensitive: no", "Sensitive: yes — money movement\nMisuse cases: AC-2"))
        self.assertEqual(self.run_cli("validate", "REF-12", "--stage", "spec"), (0, "OK\n"))

    def test_a_cleared_flag_names_who_and_why(self):
        self.write(f"{C}/proposal.md", PROPOSAL.replace("Sensitive: no", "Sensitive: cleared"))
        self.assertProblem(self.run_cli("validate", "REF-12", "--stage", "spec"), "names who cleared it")
        self.write(f"{C}/proposal.md", PROPOSAL.replace("Sensitive: no", "Sensitive: cleared by Priya — reads its own balance only"))
        self.assertEqual(self.run_cli("validate", "REF-12", "--stage", "spec"), (0, "OK\n"))

    # scan

    SCANS = ".factory/runs/REF-12-scans.txt"

    def git(self, *args):
        subprocess.run(["git", *args], check=True, capture_output=True)

    def commit_all(self):
        self.git("add", "-A")
        self.git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "x")

    def scan_repo(self, deps="sh deps.sh", secrets="true", code="true"):
        """A repo on main, a job branch on top; deps.sh prints the advisories in deps.txt."""
        self.git("init", "-q", "-b", "main")
        self.write(".factory/config.md", "Target branch: main\n\n## Commands\n| Command | Run |\n|---|---|\n"
                   f"| Secrets | {secrets} |\n| Dependencies | {deps} |\n| Code scan | {code} |\n")
        self.write("deps.sh", "[ -s deps.txt ] || exit 0; cat deps.txt; exit 1\n")
        self.write("deps.txt", "")
        self.commit_all()
        self.git("checkout", "-qb", "factory/REF-12")

    def test_scan_counts_only_the_advisories_the_job_adds(self):
        self.scan_repo()
        self.write("deps.txt", "lodash GHSA-35jh-r3h4-6jhm\n")
        self.git("checkout", "-q", "main"); self.commit_all(); self.git("checkout", "-q", "factory/REF-12")
        self.git("merge", "-q", "main")
        self.assertEqual(self.run_cli("scan", "REF-12")[0], 0)
        self.assertIn("Dependencies: no new findings (1 advisory ids known on main)", Path(self.SCANS).read_text())
        self.write("deps.txt", "lodash GHSA-35jh-r3h4-6jhm\nminimist CVE-2021-44906\n")
        self.commit_all()
        code, out = self.run_cli("scan", "REF-12")
        self.assertEqual(code, 1)
        self.assertIn("Dependencies: new: CVE-2021-44906 (1 advisory ids known on main)", out)

    def test_scan_passes_the_merge_base_and_flags_new_findings(self):
        self.scan_repo(secrets="test -n '<base>' && git cat-file -e <base> && exit 1")
        code, out = self.run_cli("scan", "REF-12")
        self.assertEqual(code, 1)
        self.assertIn("Secrets: new findings", out)
        self.assertIn("Code scan: clean", out)

    def test_a_repo_without_dependencies_skips_that_scan(self):
        self.scan_repo(deps="none")
        self.assertEqual(self.run_cli("scan", "REF-12"),
                         (0, "Secrets: clean\nDependencies: none, the repo has no dependencies\nCode scan: clean\n"
                             f"saved to {self.SCANS}\n"))

    def test_scan_output_is_never_committed(self):
        self.scan_repo()
        self.run_cli("scan", "REF-12")
        self.git("add", "-A")
        staged = subprocess.run(["git", "diff", "--cached", "--name-only"], capture_output=True, text=True).stdout
        self.assertNotIn(".factory/runs/", staged)

    def test_scan_fails_closed(self):
        self.scan_repo(code="no-such-scanner --error")
        code, out = self.run_cli("scan", "REF-12")
        self.assertEqual(code, 2)
        self.assertIn("Code scan: can't run", out)
        self.assertIn("no-such-scanner is missing", Path(self.SCANS).read_text())

    def test_scan_without_setup_cant_run_rather_than_finding_something(self):
        self.scan_repo()
        self.write(".factory/config.md", "Target branch: main\n")
        self.assertEqual(self.run_cli("scan", "REF-12"),
                         (2, "- no Secrets, Dependencies, Code scan command in .factory/config.md: run /factory:guardrails\n"))
        self.write(".factory/config.md", (Path(".factory/config.md").read_text() + "\n## Commands\n| Secrets | true |\n"
                                          "| Dependencies | none |\n| Code scan | true |\n").replace("Target branch: main\n", ""))
        code, out = self.run_cli("scan", "REF-12")
        self.assertEqual(code, 2)
        self.assertIn("no Target branch", out)


if __name__ == "__main__":
    unittest.main()
