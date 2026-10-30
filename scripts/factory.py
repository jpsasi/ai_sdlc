#!/usr/bin/env python3
"""Deterministic checks for the software factory, over the OpenSpec layout.

Run from the product repo root:
  factory.py validate <id> --stage spec|plan|build [--results <test-output-file>]
  factory.py approve <id> --what proposal --by "<name>"
  factory.py sync <id>
  factory.py archive <id>
  factory.py check-specs
  factory.py check-docs
  factory.py scan <id>      run the config's security scans, and save which findings the job adds

Prints OK (or what it did) and exits 0, or lists every problem and exits 1. scan exits 1 when the
job adds a finding, and 2 when a scan can't run. Its output goes to .factory/runs/, which is never
committed.
"""
import argparse
import datetime
import hashlib
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SPECS = Path("openspec/specs")
CHANGES = Path("openspec/changes")
ARCHIVE = CHANGES / "archive"
JOBS = Path(".factory/jobs")
RUNS = Path(".factory/runs")  # local scan output, kept out of git

AC = re.compile(r"\bAC-\d+\b")
STEP = re.compile(r"^- \[( |x)\] (\d+)\.(.*)$")
REQ = "### Requirement: "
TAG = re.compile(r"`((?:P|K|NFR)-\d+|[A-Za-z][A-Za-z0-9-]* AC-\d+)`")
NORMATIVE = re.compile(r"\b(SHALL|MUST)\b")
DELTA_SECTIONS = ("ADDED", "MODIFIED", "REMOVED", "RENAMED")
TEST_PATH = re.compile(r"(^|/)(tests?|spec|specs|__tests__)/|(^|/)test_[^/]*$|_test\.[a-z]+$|\.(test|spec)\.[a-z]+$")
NOT_TESTS = ("docs/", "openspec/", ".factory/")
SCANS = ("Secrets", "Dependencies", "Code scan")  # Commands table rows, by shared/SECURITY.md
ADVISORY = re.compile(r"\b(?:GHSA(?:-[23456789cfghjmpqrvwx]{4}){3}|(?:CVE|PYSEC|GO|RUSTSEC|OSV|MAL)-\d{4}-\d+)\b")


class Problem(Exception):
    pass


# ---------- reading ----------

def read(path):
    p = Path(path)
    return p.read_text(encoding="utf-8").replace("\r\n", "\n") if p.is_file() else None


def section(text, heading):
    """Lines under '## <heading>' up to the next '## ' heading."""
    out, inside = [], False
    for line in text.split("\n"):
        if line.startswith("## "):
            inside = line[3:].strip().lower().startswith(heading.lower())
            continue
        if inside:
            out.append(line)
    return out


def change_dir(job):
    active = CHANGES / job
    if active.is_dir():
        return active
    archived = sorted(ARCHIVE.glob(f"*-{job}")) + sorted(ARCHIVE.glob(f"*-{job}.*"))
    return archived[-1] if archived else active


def proposal_acs(proposal):
    return [m.group(1) for line in section(proposal, "Acceptance criteria")
            for m in [re.match(r"\s*-\s*(AC-\d+)\b", line)] if m]


def task_steps(tasks):
    """[(number, ticked, block_text)] for each step."""
    steps, current = [], None
    for line in tasks.split("\n"):
        m = STEP.match(line)
        if m:
            current = [int(m.group(2)), m.group(1) == "x", line]
            steps.append(current)
        elif current and line.startswith("## "):
            current = None
        elif current:
            current[2] += "\n" + line
    return [tuple(s) for s in steps]


def product_ids():
    text = read("docs/product.md") or ""
    return set(re.findall(r"^### (P-\d+)\b", text, re.M)) | set(re.findall(r"^(K-\d+)\b", text, re.M))


# ---------- specs and deltas ----------

def parse_requirements(text):
    """[(name, block)] for each '### Requirement:' block, up to the next one or a '## ' heading."""
    reqs, current = [], None
    for line in text.split("\n"):
        if line.startswith(REQ):
            current = [line[len(REQ):].strip(), line]
            reqs.append(current)
        elif line.startswith("## "):
            current = None
        elif current is not None:
            current[1] += "\n" + line
    return [(n, b.rstrip() + "\n") for n, b in reqs]


def parse_delta(text):
    delta = {k: [] for k in DELTA_SECTIONS}
    unknown = []
    for chunk in re.split(r"(?m)^(?=## )", text):
        head = chunk.split("\n", 1)[0]
        if not head.startswith("## "):
            continue
        m = re.match(r"## (ADDED|MODIFIED|REMOVED|RENAMED) Requirements\s*$", head)
        if not m:
            unknown.append(head)
            continue
        kind = m.group(1)
        if kind == "RENAMED":
            froms = re.findall(r"FROM:\s*`### Requirement: (.+?)`", chunk)
            tos = re.findall(r"TO:\s*`### Requirement: (.+?)`", chunk)
            delta[kind] += list(zip(froms, tos))
        else:
            delta[kind] += parse_requirements(chunk)
    return delta, unknown


def requirement_problems(where, name, block, need_trace=True):
    out = []
    first = block.split("####", 1)[0]
    if not NORMATIVE.search(first):
        out.append(f"{where}: '{name}' has no SHALL or MUST")
    if "#### Scenario:" not in block:
        out.append(f"{where}: '{name}' has no '#### Scenario:'")
    if need_trace and not TAG.search(block) and "Source:" not in block:
        out.append(f"{where}: '{name}' has no tag and no Source line")
    return out


def split_main(text):
    """(head, [(name, block)], tail) of a living spec."""
    idx = text.find(REQ)
    if idx == -1:
        return text, [], ""
    head, rest = text[:idx], text[idx:]
    m = re.search(r"(?m)^## ", rest)
    body, tail = (rest[:m.start()], rest[m.start():]) if m else (rest, "")
    return head, parse_requirements(body), tail


def apply_delta(cap, delta, job):
    """New text of openspec/specs/<cap>/spec.md with the delta applied. Raises Problem."""
    main = SPECS / cap / "spec.md"
    text = read(main)
    if text is None:
        title = cap.replace("/", " / ").replace("-", " ").title()
        text = f"# {title} Specification\n\n## Purpose\nAdded by change {job}; describe the capability here.\n\n## Requirements\n"
    head, reqs, tail = split_main(text)
    order = [n for n, _ in reqs]
    blocks = dict(reqs)
    for old, new in delta["RENAMED"]:
        if old not in blocks:
            raise Problem(f"{cap}: cannot rename missing requirement '{old}'")
        blocks[new] = blocks.pop(old).replace(f"{REQ}{old}", f"{REQ}{new}", 1)
        order[order.index(old)] = new
    for name, _ in delta["REMOVED"]:
        if name not in blocks:
            raise Problem(f"{cap}: cannot remove missing requirement '{name}'")
        del blocks[name]
        order.remove(name)
    for name, block in delta["MODIFIED"]:
        if name not in blocks:
            raise Problem(f"{cap}: cannot modify missing requirement '{name}'")
        blocks[name] = block
    for name, block in delta["ADDED"]:
        if name in blocks:
            raise Problem(f"{cap}: '{name}' already exists; use MODIFIED")
        blocks[name] = block
        order.append(name)
    new = head.rstrip() + "\n\n" + "\n".join(blocks[n] for n in order)
    if tail:
        new = new.rstrip() + "\n\n" + tail.lstrip()
    return main, new.rstrip() + "\n"


def delta_files(cdir):
    root = cdir / "specs"
    return sorted((str(p.parent.relative_to(root)), p) for p in root.rglob("spec.md")) if root.is_dir() else []


def check_deltas(job, cdir, acs, problems):
    for cap, path in delta_files(cdir):
        where = f"delta {cap}"
        delta, unknown = parse_delta(read(path))
        for head in unknown:
            problems.append(f"{where}: unknown section '{head}'")
        if not any(delta.values()):
            problems.append(f"{where}: no ADDED, MODIFIED, REMOVED or RENAMED requirements")
        for kind in ("ADDED", "MODIFIED"):
            for name, block in delta[kind]:
                problems += requirement_problems(where, name, block)
                for tag in TAG.findall(block):
                    m = re.fullmatch(r"(.+) (AC-\d+)", tag)
                    if m and m.group(1) == job and m.group(2) not in acs:
                        problems.append(f"{where}: '{name}' tags {tag}, which the proposal doesn't define")
        if cdir.parent == ARCHIVE:
            continue  # already synced into the living specs
        try:
            apply_delta(cap, delta, job)
        except Problem as e:
            problems.append(f"{where}: {e}")


# ---------- validate ----------

def tracked_test_files():
    try:
        out = subprocess.run(["git", "ls-files"], capture_output=True, text=True, check=True).stdout.split("\n")
    except (OSError, subprocess.CalledProcessError):
        out = [str(p) for p in Path(".").rglob("*") if p.is_file()]
    return [f for f in out if f and TEST_PATH.search(f) and not f.startswith(NOT_TESTS)]


def approval_hash(cdir):
    parts = [read(cdir / "proposal.md") or ""] + [read(p) for _, p in delta_files(cdir)]
    normal = "\n".join(line.rstrip() for part in parts for line in part.strip().split("\n"))
    return hashlib.sha256(normal.encode("utf-8")).hexdigest()[:16]


def approvals(job_text):
    """{what: hash} from the job record's Approvals section; the latest entry wins."""
    found = {}
    for line in section(job_text, "Approvals"):
        m = re.match(r"\s*-\s*(\w+)\s+([0-9a-f]{16})\s+by\s+", line)
        if m:
            found[m.group(1)] = m.group(2)
    return found


def check_proposal(job, cdir, problems):
    proposal = read(cdir / "proposal.md")
    if proposal is None:
        problems.append(f"{cdir}/proposal.md is missing")
        return None
    acs = proposal_acs(proposal)
    if not acs:
        problems.append("proposal has no acceptance criteria (lines '- AC-n ...')")
    dupes = sorted({a for a in acs if acs.count(a) > 1})
    if dupes:
        problems.append(f"duplicate acceptance criteria: {', '.join(dupes)}")
    planned = set(AC.findall("\n".join(section(proposal, "Test plan"))))
    for ac in acs:
        if ac not in planned:
            problems.append(f"{ac} has no entry in the proposal's Test plan")
    m = re.search(r"Delivers:\s*([A-Z]-\d+|none)", proposal)
    if not m:
        problems.append("proposal header has no 'Delivers: P-n | K-n | none'")
    elif m.group(1) != "none" and m.group(1) not in product_ids():
        problems.append(f"proposal delivers {m.group(1)}, which docs/product.md doesn't define")
    check_security(proposal, acs, problems)
    check_deltas(job, cdir, acs, problems)
    return acs


def check_security(proposal, acs, problems):
    """The Security section, by SECURITY.md: no; yes, with its areas and misuse cases; or cleared by the developer, with a reason."""
    text = "\n".join(section(proposal, "Security"))
    m = re.search(r"^Sensitive:\s*(no|yes|cleared)\b(.*)$", text, re.M)
    if not m:
        problems.append("proposal has no '## Security' section with 'Sensitive: no | yes — <areas> | cleared by <name> — <reason>'")
        return
    value, rest = m.groups()
    if value == "yes":
        if not re.match(r"\s*[—-]+\s*\S", rest):
            problems.append("a sensitive proposal names its areas: 'Sensitive: yes — <areas>'")
        cases = re.search(r"^Misuse cases:(.*)$", text, re.M)
        named = AC.findall(cases.group(1)) if cases else []
        if not named:
            problems.append("a sensitive proposal lists its misuse cases: 'Misuse cases: AC-n, ...'")
        for ac in named:
            if ac not in acs:
                problems.append(f"misuse case {ac} isn't an acceptance criterion")
    elif value == "cleared" and not re.match(r"\s*by\s+\S.*?\s[—-]+\s*\S", rest):
        problems.append("a cleared flag names who cleared it, and why: "
                        "'Sensitive: cleared by <name> — <reason>'")


def check_approval(job, cdir, problems):
    record = read(JOBS / f"{job}.md")
    if record is None:
        problems.append(f"{JOBS}/{job}.md is missing")
        return
    recorded = approvals(record).get("proposal")
    if recorded is None:
        problems.append("no recorded proposal approval")
    elif recorded != approval_hash(cdir):
        problems.append("the proposal or its deltas changed after approval: approve again")


def check_tasks(cdir, acs, problems):
    design = read(cdir / "design.md")
    if design is None or not "".join(section(design, "Approach")).strip():
        problems.append("design.md is missing, or has no Approach")
    tasks = read(cdir / "tasks.md")
    if tasks is None:
        problems.append(f"{cdir}/tasks.md is missing")
        return None
    steps = task_steps(tasks)
    if not steps:
        problems.append("tasks.md has no steps (lines '- [ ] n. ...')")
    covered = set()
    for number, _, block in steps:
        covered |= set(AC.findall(block))
        if "Test first:" not in block:
            problems.append(f"task {number} has no 'Test first:'")
        if "Verify:" not in block:
            problems.append(f"task {number} has no 'Verify:'")
    for ac in acs:
        if ac not in covered:
            problems.append(f"{ac} is not covered by any task")
    original = [s for s in steps if "(R-" not in s[2].split("\n")[0]]
    if len(original) > 8:
        problems.append(f"tasks.md has {len(original)} tasks; the limit is 8")
    return steps


def check_build(job, acs, steps, results, problems):
    for number, ticked, _ in steps:
        if not ticked:
            problems.append(f"task {number} is not ticked")
    corpus = "\n".join(read(f) or "" for f in tracked_test_files())
    output = read(results) if results else None
    if results and output is None:
        problems.append(f"results file {results} not found")
    for ac in acs:
        tag = f"{job} {ac}"
        if tag not in corpus:
            problems.append(f"no test named '{tag} ...' in the test files")
        elif output is not None and tag not in output:
            problems.append(f"test '{tag}' does not appear in the test results: did it run?")


def validate(args):
    problems = []
    cdir = change_dir(args.job)
    acs = check_proposal(args.job, cdir, problems)
    if acs is not None and args.stage in ("plan", "build"):
        check_approval(args.job, cdir, problems)
        steps = check_tasks(cdir, acs, problems)
        if steps is not None and args.stage == "build":
            check_build(args.job, acs, steps, args.results, problems)
    return report(problems)


# ---------- security scans ----------

def config_commands(text):
    """{row name: command} from the Commands table of .factory/config.md."""
    out = {}
    for line in section(text, "Commands"):
        cells = [c.strip().strip("`") for c in re.split(r"(?<!\\)\|", line.strip().strip("|"))]
        if line.startswith("|") and len(cells) > 1 and not re.match(r"^[\s:-]*$", cells[0]):
            out[cells[0]] = cells[1].replace("\\|", "|")
    return out


def git_out(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout


def run_scan(command, cwd=None):
    """(outcome, output): outcome is clean, found or error. A scan exits 0 clean, 1 on a finding."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=cwd)
    except OSError as e:
        return "error", str(e)
    output = (result.stdout + result.stderr).strip()
    if result.returncode == 127:
        return "error", f"{command.split()[0]} is missing: install it (see shared/SECURITY.md)\n{output}"
    return {0: "clean", 1: "found"}.get(result.returncode, "error"), output


def merge_base(config):
    m = re.search(r"^Target branch: *(\S+)", config, re.M)
    if not m:
        raise Problem("no Target branch in .factory/config.md: run Setup in shared/CONFIG.md")
    target = m.group(1)
    for ref in (f"origin/{target}", target):
        try:
            return target, git_out("merge-base", ref, "HEAD").strip()
        except (OSError, subprocess.CalledProcessError):
            continue
    raise Problem(f"can't find the merge base with {target}: run git fetch origin {target}")


def scan_on(base, command):
    """Runs a scan over the code at base, in a throwaway worktree."""
    with tempfile.TemporaryDirectory() as tmp:
        tree = Path(tmp) / "base"
        git_out("worktree", "add", "--detach", "--quiet", str(tree), base)
        try:
            return run_scan(command, cwd=tree)
        finally:
            git_out("worktree", "remove", "--force", str(tree))


def scan(args):
    """Runs the Secrets, Dependencies and Code scan commands. The secrets and code scans see only the
    job's commits (<base>); the dependency scan sees the whole tree, so it runs on the merge base too,
    and only advisories missing there count as the job's. Exits 2 when the scans can't run at all."""
    config = read(".factory/config.md") or ""
    commands = config_commands(config)
    missing = [name for name in SCANS if not commands.get(name)]
    try:
        if missing:
            raise Problem(f"no {', '.join(missing)} command in .factory/config.md: run /factory:guardrails")
        target, base = merge_base(config)
    except Problem as e:
        print(f"- {e}")
        return 2
    RUNS.mkdir(parents=True, exist_ok=True)
    if not (RUNS / ".gitignore").exists():
        (RUNS / ".gitignore").write_text("*\n", encoding="utf-8")
    path = RUNS / f"{args.job}-scans.txt"
    summary, details, worst = [], [], 0
    for name in SCANS:
        command = commands[name].replace("<base>", base)
        if name == "Dependencies" and command.lower() == "none":
            summary.append(f"{name}: none, the repo has no dependencies")
            continue
        outcome, output = run_scan(command)
        line = {"clean": "clean", "found": "new findings", "error": "can't run"}[outcome]
        if outcome == "found" and name == "Dependencies":
            known_outcome, known_output = scan_on(base, command)
            if known_outcome == "error":
                outcome, line = "error", f"can't run on {target}"
                output += f"\n\n-- on {target} --\n{known_output}"
            else:
                now, before = set(ADVISORY.findall(output)), set(ADVISORY.findall(known_output))
                new = sorted(now - before) if now else ["(advisory ids not recognised: all count as new)"]
                if not new:
                    outcome = "known"
                    line = f"no new findings ({len(before & now)} advisory ids known on {target})"
                else:
                    known = len(now & before)
                    line = f"new: {', '.join(new)}" + (f" ({known} advisory ids known on {target})" if known else "")
        worst = max(worst, {"clean": 0, "known": 0, "found": 1, "error": 2}[outcome])
        summary.append(f"{name}: {line}")
        details.append(f"== {name}: {command} ==\n{output}")
    path.write_text("\n".join(summary) + "\n\n" + "\n\n".join(details) + "\n", encoding="utf-8")
    print("\n".join(summary))
    print(f"saved to {path}")
    return worst


# ---------- approve, sync, archive ----------

def approve(args):
    if args.what != "proposal":
        print("only 'proposal' approvals are recorded", file=sys.stderr)
        return 2
    cdir = change_dir(args.job)
    record_path = JOBS / f"{args.job}.md"
    if read(cdir / "proposal.md") is None or not record_path.is_file():
        print(f"need {cdir}/proposal.md and {record_path}", file=sys.stderr)
        return 2
    record = read(record_path)
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = f"- proposal {approval_hash(cdir)} by {args.by} at {stamp}"
    if "\n## Approvals" not in "\n" + record:
        record = record.rstrip("\n") + "\n\n## Approvals\n"
    lines = record.rstrip("\n").split("\n")
    start = next(i for i, l in enumerate(lines) if l.startswith("## Approvals"))
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    lines.insert(end, entry)
    record_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"recorded: {entry[2:]}")
    return 0


def sync(args):
    """Merge every delta of the change into openspec/specs. Writes nothing unless every delta applies."""
    cdir = CHANGES / args.job
    if not cdir.is_dir():
        return report([f"{cdir} not found (is it archived already?)"])
    pending, problems = [], []
    for cap, path in delta_files(cdir):
        delta, unknown = parse_delta(read(path))
        problems += [f"delta {cap}: unknown section '{h}'" for h in unknown]
        try:
            pending.append((cap, delta, *apply_delta(cap, delta, args.job)))
        except Problem as e:
            problems.append(f"delta {cap}: {e} (nothing written)")
    if problems:
        return report(problems)
    for cap, delta, main, text in pending:
        main.parent.mkdir(parents=True, exist_ok=True)
        main.write_text(text, encoding="utf-8")
        print(f"{main}: +{len(delta['ADDED'])} ~{len(delta['MODIFIED'])} -{len(delta['REMOVED'])} >{len(delta['RENAMED'])}")
    if not pending:
        print("no deltas to sync")
    return 0


def archive(args):
    cdir = CHANGES / args.job
    if not cdir.is_dir():
        return report([f"{cdir} not found (is it archived already?)"])
    date = datetime.date.today().isoformat()
    target, n = ARCHIVE / f"{date}-{args.job}", 2
    while target.exists():
        target, n = ARCHIVE / f"{date}-{args.job}.{n}", n + 1
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    shutil.move(str(cdir), str(target))
    print(f"archived to {target}")
    return 0


# ---------- checks ----------

def check_specs(_args):
    problems = []
    for path in sorted(SPECS.rglob("spec.md")) if SPECS.is_dir() else []:
        where = str(path)
        text = read(path)
        if not text.startswith("# "):
            problems.append(f"{where}: no '# <title>' first line")
        for heading in ("## Purpose", "## Requirements"):
            if f"\n{heading}" not in "\n" + text:
                problems.append(f"{where}: no '{heading}' section")
        _, reqs, _ = split_main(text)
        names = [n for n, _ in reqs]
        for name in sorted({n for n in names if names.count(n) > 1}):
            problems.append(f"{where}: duplicate requirement '{name}'")
        for name, block in reqs:
            problems += requirement_problems(where, name, block)
            for line in block.split("\n"):
                if line.startswith("Source:"):
                    for kind, ref in re.findall(r"\b(test|code|imported)\s+`([^`]+)`", line):
                        file = ref.split(":")[0]
                        if kind != "imported" and not Path(file).exists():
                            problems.append(f"{where}: '{name}' cites {kind} `{ref}`, which doesn't exist")
    return report(problems)


def check_docs(_args):
    problems = []
    product = read("docs/product.md")
    if product is None:
        return report(["docs/product.md is missing"])
    for prefix in ("P", "NFR", "C", "K"):
        ids = re.findall(rf"^(?:### )?({prefix}-\d+)\b", product, re.M)
        dupes = sorted({i for i in ids if ids.count(i) > 1})
        if dupes:
            problems.append(f"duplicate ids in docs/product.md: {', '.join(dupes)}")
    backlog = read("docs/backlog.md")
    if backlog:
        known = product_ids()
        tasks, deps = [], {}
        for line in backlog.split("\n"):
            h = re.match(r"^## ((?:P|K)-\d+)\b", line)
            if h and h.group(1) not in known:
                problems.append(f"backlog section {h.group(1)} has no match in docs/product.md")
            row = re.match(r"^\|\s*(T-\d+)\s*\|(.*)$", line)
            if row:
                tasks.append(row.group(1))
                cells = [c.strip() for c in row.group(2).split("|")]
                deps[row.group(1)] = re.findall(r"T-\d+", cells[2] if len(cells) > 2 else "")
        dupes = sorted({t for t in tasks if tasks.count(t) > 1})
        if dupes:
            problems.append(f"duplicate task ids in docs/backlog.md: {', '.join(dupes)}")
        for task, needs in deps.items():
            for d in needs:
                if d not in deps:
                    problems.append(f"{task} depends on {d}, which is not in the backlog")
        problems += cycles(deps)
    return report(problems)


def cycles(deps):
    state, found = {}, []

    def visit(node, path):
        state[node] = "open"
        for nxt in deps.get(node, []):
            if state.get(nxt) == "open":
                found.append("dependency cycle: " + " -> ".join(path + [nxt]))
            elif nxt in deps and nxt not in state:
                visit(nxt, path + [nxt])
        state[node] = "done"

    for node in deps:
        if node not in state:
            visit(node, [node])
    return found


def report(problems):
    if problems:
        for p in problems:
            print(f"- {p}")
        return 1
    print("OK")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="Deterministic checks for the software factory")
    sub = parser.add_subparsers(dest="command", required=True)
    v = sub.add_parser("validate", help="check a change's proposal, deltas, tasks and test traceability")
    v.add_argument("job")
    v.add_argument("--stage", choices=["spec", "plan", "build"], required=True)
    v.add_argument("--results", help="file holding the full test run's output")
    a = sub.add_parser("approve", help="record a person's approval of the proposal and its deltas")
    a.add_argument("job")
    a.add_argument("--what", required=True)
    a.add_argument("--by", required=True)
    for name, text in (("sync", "merge the change's deltas into openspec/specs"),
                       ("archive", "move the change to openspec/changes/archive")):
        sub.add_parser(name, help=text).add_argument("job")
    sub.add_parser("check-specs", help="check every living spec is well formed and traceable")
    sub.add_parser("check-docs", help="check ids and dependencies in docs/product.md and docs/backlog.md")
    sub.add_parser("scan", help="run the security scans, and save which findings the job adds").add_argument("job")
    args = parser.parse_args(argv)
    commands = {"validate": validate, "approve": approve, "sync": sync, "archive": archive,
                "check-specs": check_specs, "check-docs": check_docs, "scan": scan}
    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
