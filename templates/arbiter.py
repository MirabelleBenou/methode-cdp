#!/usr/bin/env python3
"""The living-docs arbiter, as a scheduled run — one script, no session and no model token.

Every morning, a scheduled action runs this script on the living-docs repository: it checks, files one workstream
per new gap, archives, writes a log line and returns a code. Everything in it is deterministic; judging the documents
(contradiction, duplicate, useless history) is left to another session, the controller.
The behavior is that of the arbiter's procedure (ARBITER.md, §1 to §3).

    python3 -B arbiter.py --workstreams <workstreams.yaml> --log <decision_log.md> --archives <folder> \\
        --domains <domains.yaml> --arbiter-log <log.md> \\
        [--board <page> --generator <script>] [--plan <plan.md>] [--root <folder>] \\
        [--method <file>] [--sheet <file>] [--date "YYYY-MM-DD HH:MM"]

The first five options are those of the checker (check_living_docs.py); "--board" and "--generator" go together;
"--root" is the folder the domain table's checkpoints are read from (the current folder by default; it is also git's
folder). "--method" (the project's method) and "--sheet" (the common product sheet) only serve to measure the
footprint of the log. "--date" (Paris time) is for the tests; without it, it is the time in Paris (zoneinfo,
Europe/Paris). The checker, the archiver and the script itself are in the same folder; the generator is the one of
"--generator". Standard library only, Python 3.11 at least.

A run does, in order:
  1. normalize (archive_workstreams.py normalize);
  2. check (check_living_docs.py) and pick up the gap lines;
  3. file ONE workstream per new gap, at the end of workstreams.yaml, in strict YAML format: the id
     "arbiter-c<n>-<key>" (<n> the number of the check); check 9 as one workstream per domain
     ("arbiter-c9-checkpoint-<domain>-<YYYYMMDD>"), check 10 likewise
     ("arbiter-c10-short-checkpoint-<domain>-<YYYYMMDD>"), a fault of the domain table as a single workstream for the
     coordinator ("arbiter-c9-table-<YYYYMMDD>"); never twice: a (living) workstream with the same id has
     been reported, an archived id is not reused ("-<YYYYMMDD>" is added), a domain workstream
     "arbiter-c9-checkpoint-<domain>-*" or "arbiter-c9-table-*" still open (not accepted) is enough, and for check 10,
     an open workstream "for:" that PL whose id carries "short-checkpoint" too;
  4. the batons: the "Session active" line of each domain checkpoint and the last commit that carries its
     identifier — information (the log and the output), never a workstream; the coordination (the domain whose "pl"
     contains "Coordination" or "Coordinator") is excluded;
  5. the late checkpoint: a workstream of the domain, accepted and without "for:", whose "accepted-on:" is later
     than the date of the checkpoint's last commit, is a line of that domain's check-9 workstream;
  6. archive (archive_workstreams.py archive);
  7. if workstreams.yaml changed: regenerate the board (with "--board"), then check again;
  8. append a line at the end of "--arbiter-log";
  9. print the summary.

The addressee "for:" is read from the data: the domain's "pl" (the "--domains" table) for a domain workstream, the
"pl:" of a workstream in flight, otherwise the one the workstream carries, otherwise the coordinator (the table entry
whose "pl" contains "Coordination" or "Coordinator": without it, code 2).

The script does not commit and does not push: the workflow does. The last line of the output, "Commit: <message>", is
the commit message. It only writes to: the end of workstreams.yaml, the regenerated board, the end of the arbiter's
log, and what the archiver and the normalizer do.

Exit code: 0 with no new workstream, 1 with at least one new workstream, 2 if a file is missing or a script fails (the
log then says "check impossible: <file>").
"""
import argparse
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path

sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
TIME_ZONE = "Europe/Paris"
SILENCE = timedelta(hours=24)
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August",
          "September", "October", "November", "December"]
GAP = "GAP"
FILE_OPTIONS = ("workstreams", "log", "domains", "arbiter_log", "board", "generator", "plan", "method", "sheet")
RE_HEADER = re.compile(r"^(\d+)\s+(.+?)\s+(GAP|warning|OK)\s+(.*)$")
RE_NOT_REQUESTED = re.compile(r"^(\d+)\s+(.+?)\s+—\s+not requested$")
RE_TABLE_FAULT = re.compile(r"checkpoint not found|checkpoint unreadable|queue section not found"
                            r"|domain or checkpoint missing")
RE_BATON = re.compile(r"^\**\s*Session active\s*:")
RE_IDENTIFIER = re.compile(r"^\**\s*Session active\s*:\s*\**\s*([A-Za-z0-9]{8})(?=\s*,|\s+since\b)")
ACTIONS = {
    1: "Fix the decision log: a number is unique and has no gap.",
    3: "Make the id unique, living workstreams and archives included (an archived id is not reused).",
    4: ("A version is carried by one batch only; a batch in flight goes above the highest version of its "
        "deliverable."),
    5: "Fill in the pl: of the workstream in flight.",
    6: "Regenerate the board page and its data file from workstreams.yaml, after the last pull.",
    7: "Accept the entry of the plan log's last version, or bring the log in line with workstreams.yaml.",
    8: "One batch in flight per deliverable or resource, and a waits: that names an existing id and never a batch "
       "in flight.",
    11: "Fix the value by hand: it carries a control character, which normalizing cannot write.",
}


class Impossible(Exception):
    """The check is impossible: "file" says what is missing or fails, "detail" the message (code 2)."""

    def __init__(self, file: str, detail: str = ""):
        super().__init__(detail or file)
        self.file, self.detail = file, detail


# ───────────────────────────── the neighboring scripts ─────────────────────────────

def load(name: str):
    """Imports a neighboring script by its path (its reading functions; it does not run: __main__ guard)."""
    import importlib.util
    path = HERE / name
    if not path.is_file():
        raise Impossible(str(path), f"script not found: {path}")
    spec = importlib.util.spec_from_file_location("_arbiter_" + path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(script: Path, *arguments) -> subprocess.CompletedProcess:
    if not Path(script).is_file():
        raise Impossible(str(script), f"script not found: {script}")
    return subprocess.run([sys.executable, "-B", str(script), *map(str, arguments)],
                          capture_output=True, text=True, encoding="utf-8")


def last_line(process: subprocess.CompletedProcess) -> str:
    text = (process.stderr.strip() or process.stdout.strip() or "no message")
    return text.splitlines()[-1]


def git(root: Path, *arguments) -> tuple[int, str]:
    process = subprocess.run(["git", "-C", str(root), *arguments], capture_output=True, text=True,
                             encoding="utf-8", env={**os.environ, "LC_ALL": "C", "GIT_TERMINAL_PROMPT": "0"})
    return process.returncode, process.stdout.strip()


# ───────────────────────────── the arguments ─────────────────────────────

class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError(message.replace("expected one argument", "missing value"))


def read_arguments(argv: list[str]):
    p = Parser(prog="arbiter.py", allow_abbrev=False, add_help=False)
    for option in ("workstreams", "log", "archives", "domains", "arbiter-log", "board", "generator",
                   "plan", "root", "method", "sheet", "date"):
        p.add_argument(f"--{option}")
    a, unknown = p.parse_known_args(argv)
    if unknown:
        raise ValueError(f"unknown argument: {unknown[0]}")
    for option in ("workstreams", "log", "archives", "domains", "arbiter_log"):
        if not getattr(a, option):
            raise ValueError(f"missing argument: --{option.replace('_', '-')}")
    if bool(a.board) != bool(a.generator):
        raise ValueError("--board and --generator go together")
    return a


def read_date(text: str | None) -> datetime:
    """The instant of the run, in Paris time (that of "--date" if it is given)."""
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
    try:
        zone = ZoneInfo(TIME_ZONE)
    except ZoneInfoNotFoundError:
        raise ValueError(f"time zone {TIME_ZONE} not found (the tzdata package is missing)")
    if text is None:
        return datetime.now(zone)
    try:
        return datetime.strptime(text, "%Y-%m-%d %H:%M").replace(tzinfo=zone)
    except ValueError:
        raise ValueError(f"--date: YYYY-MM-DD HH:MM expected, got “{text}”")


# ───────────────────────────── the check ─────────────────────────────

@dataclass
class Check:
    """The checker's output: {rank: (verdict, count, [details])} and the last line."""
    ranks: dict = field(default_factory=dict)
    summary: str = ""
    code: int = 0

    def gaps(self) -> int:
        return sum(1 for verdict, _, _ in self.ranks.values() if verdict == GAP)

    def lines(self, rank: int) -> list[str]:
        verdict, _, details = self.ranks.get(rank, ("", "", []))
        return details if verdict == GAP else []


def read_output(text: str, code: int) -> Check:
    check, last = Check(code=code), None
    for line in text.split("\n"):
        if not line.strip():
            continue
        if line.startswith("      ") and last is not None:
            check.ranks[last][2].append(line.strip())
            continue
        m = RE_HEADER.match(line)
        if m:
            last = int(m.group(1))
            check.ranks[last] = (m.group(3), m.group(4), [])
            continue
        m = RE_NOT_REQUESTED.match(line)
        if m:
            last = None
            check.ranks[int(m.group(1))] = ("not requested", "", [])
            continue
        last = None
        check.summary = line
    return check


def run_check(a) -> Check:
    options = ["--workstreams", a.workstreams, "--log", a.log, "--archives", a.archives,
               "--domains", a.domains]
    if a.board:
        options += ["--board", a.board, "--generator", a.generator]
    if a.plan:
        options += ["--plan", a.plan]
    if a.root:
        options += ["--root", a.root]
    process = run(HERE / "check_living_docs.py", *options)
    if process.returncode not in (0, 1):
        raise Impossible("check_living_docs.py", f"check_living_docs.py failed (code {process.returncode}): "
                                                 f"{last_line(process)}")
    return read_output(process.stdout, process.returncode)


# ───────────────────────────── the findings ─────────────────────────────

@dataclass
class Finding:
    """A workstream to file: id, title, module, addressee, basis."""
    id: str
    title: str
    module: str
    for_: str
    basis: str


def long_date(day: date) -> str:
    return f"{day.day} {MONTHS[day.month - 1]} {day.year}"


def safe_key(text: str) -> str:
    """An id key: letters, digits, dot, hyphen and underscore."""
    return re.sub(r"[^A-Za-z0-9._-]+", "-", text).strip("-") or "case"


class Context:
    """What the addressee rules read: workstreams, archives, valid domains, coordinator."""

    def __init__(self, checker, workstreams: list[dict], archives: list[dict], table: list[dict], file: str):
        self.checker = checker
        self.workstreams, self.archives, self.table = workstreams, archives, table
        self.valid = [d for d in table if d.get("domain") and d.get("checkpoint")]
        self.by_id = {c["id"]: c for c in workstreams if c.get("id")}
        coordination = next((d for d in table if "Coordination" in d.get("pl", "") or "Coordinator" in d.get("pl", "")),
                            None)
        if coordination is None:
            raise Impossible(file, f"no Coordination entry in the domain table ({file}): "
                                   "the coordinator's name is read there")
        self.coordinator = coordination["pl"]
        self.pl_of = {d["domain"]: d.get("pl") or self.coordinator for d in self.valid}

    def domain_of(self, c: dict) -> str | None:
        return self.checker.domain_of(c, self.valid) if c.get("id") else None

    def addressee(self, c: dict | None) -> str:
        """§2: a workstream in flight goes to the pl it carries; a domain workstream to the domain's pl; otherwise to
        the pl it carries; otherwise to the coordinator."""
        if c is None:
            return self.coordinator
        if c.get("status") == "in-flight" and c.get("pl"):
            return c["pl"]
        domain = self.domain_of(c)
        if domain:
            return self.pl_of[domain]
        return c.get("pl") or self.coordinator

    def module_of(self, c: dict | None) -> str:
        return (c or {}).get("module") or "method"


def cases_of_check(rank: int, line: str, ctx: Context):
    """The cases (key, workstream at issue) of a gap line of the checks other than 9 and 10; [] if it is not a case."""
    def workstream(i):
        return ctx.by_id.get(i)

    if rank == 1:
        m = re.match(r"D(\d+)", line)
        return [(f"D{m.group(1)}" if m else "log", None)]
    if rank == 3:
        m = re.match(r"id (\S+) ", line)
        return [(safe_key(m.group(1)), workstream(m.group(1)))] if m else [(safe_key(line[:40]), None)]
    if rank == 4:
        # two forms: "version <v> carried by <id> and <id>" (a); "<id>: <v> is not above …" (b)
        m = re.match(r"version (\S+) carried by (.+)$", line)
        if m:
            first = m.group(2).split(" and ")[0]
            return [(safe_key(first), workstream(first))]
        m = re.match(r"(\S+): \S+ is not above ", line)
        if m:
            return [(safe_key(m.group(1)), workstream(m.group(1)))]
        return [(safe_key(line[:40]), None)]
    if rank == 5:
        m = re.match(r"(.+?) \(line (\d+)\): ", line)
        if m and m.group(1).startswith("(no id"):
            return [(f"line-{m.group(2)}", None)]
        return [(safe_key(m.group(1)), workstream(m.group(1)))] if m else [(safe_key(line[:40]), None)]
    if rank == 6:
        return [("board", None)]
    if rank == 7:
        return [("plan", None)]
    if rank == 8:
        m = re.match(r"(?:deliverable|resource) .+: \d+ batches in flight \((.+)\)$", line)
        if m:  # the PLs of the batches at issue, one workstream each
            return [(safe_key(i), workstream(i)) for i in m.group(1).split(", ")]
        m = re.match(r"(\S+) (?:waits for|is in flight but waits for) ", line)
        return [(safe_key(m.group(1)), workstream(m.group(1)))] if m else [(safe_key(line[:40]), None)]
    if rank == 11:
        if line.startswith("to normalize"):
            return []
        m = re.match(r"(.*):\d+ : key ", line)
        return [(f"format-{safe_key(Path(m.group(1)).stem)}", None)] if m else [(safe_key(line[:40]), None)]
    return [(safe_key(line[:40]), None)]


def ordinary_findings(check: Check, ctx: Context, day: date) -> list[Finding]:
    """One finding per case of the checks other than 9 and 10; the lines of one key are grouped."""
    findings = []
    for rank in sorted(check.ranks):
        if rank in (9, 10):
            continue
        groups: dict[str, tuple] = {}
        for line in check.lines(rank):
            for key, at_issue in cases_of_check(rank, line, ctx):
                lines = groups.setdefault(key, (at_issue, []))[1]
                if line not in lines:
                    lines.append(line)
        action = ACTIONS.get(rank, "Fix the case reported.")
        for key, (at_issue, lines) in groups.items():
            title = f"Check {rank}: {lines[0]}" + (f" (and {len(lines) - 1} more)" if len(lines) > 1 else "")
            findings.append(Finding(
                id=f"arbiter-c{rank}-{key}", title=title, module=ctx.module_of(at_issue),
                for_=ctx.addressee(at_issue),
                basis=f"Reported by the arbiter on {long_date(day)} (check {rank}). {'; '.join(lines)}. {action}"))
    return findings


def domain_name(line: str) -> str:
    return line.split(": ", 1)[0]


def checkpoint_findings(check: Check, lates: dict, ctx: Context, day: date) -> tuple[list[Finding], list[str]]:
    """The findings of checks 9 and 10 and of the lateness: one per domain (the table's fault, a single one for the
    coordinator). Also returns the domains reported, in the table's order."""
    stamp, long_day = day.strftime("%Y%m%d"), long_date(day)
    table_lines, by_domain, too_heavy = [], {}, {}
    for line in check.lines(9):
        if RE_TABLE_FAULT.search(line):
            table_lines.append(line)
        else:
            by_domain.setdefault(domain_name(line), []).append(line)
    for line in check.lines(10):
        too_heavy.setdefault(domain_name(line), []).append(line)
    late_ones = {d: list(lines) for d, lines in lates.items() if lines}
    findings = []
    if table_lines:
        findings.append(Finding(
            id=f"arbiter-c9-table-{stamp}", title="The domain table is faulty", module="method",
            for_=ctx.coordinator,
            basis=(f"Reported by the arbiter on {long_day} (check 9). {'; '.join(table_lines)}. "
                   "Align the domain table and the checkpoint: the PL may have renamed their checkpoint or section, "
                   "go back to the agreed title or fix the table.")))
    order = [d["domain"] for d in ctx.valid]
    unknown = [d for d in list(by_domain) + list(too_heavy) + list(late_ones) if d not in order]
    everyone = order + sorted(set(unknown))
    for domain in everyone:
        lines9, late = by_domain.get(domain, []), late_ones.get(domain, [])
        if lines9 or late:
            actions = []
            if lines9:
                actions.append("Cite every open workstream of your domain by its id in your checkpoint, remove the "
                               "closed workstreams from your queue (method §6).")
            if late:
                actions.append("Take your checkpoint up again: a workstream of your domain has been accepted on a date "
                               "later than its last commit (method §6).")
            findings.append(Finding(
                id=f"arbiter-c9-checkpoint-{domain}-{stamp}",
                title=f"The {domain} checkpoint lags behind its workstreams",
                module="method", for_=ctx.pl_of.get(domain, ctx.coordinator),
                basis=(f"Reported by the arbiter on {long_day} (check 9). {'; '.join(lines9 + late)}. "
                       f"{' '.join(actions)}")))
    for domain in everyone:
        lines10 = too_heavy.get(domain, [])
        if lines10:
            path = next((d["checkpoint"] for d in ctx.valid if d["domain"] == domain), "")
            folder = path.rsplit("/", 1)[0] + "/" if "/" in path else ""
            findings.append(Finding(
                id=f"arbiter-c10-short-checkpoint-{domain}-{stamp}",
                title=f"The {domain} checkpoint exceeds 10 KB",
                module="method", for_=ctx.pl_of.get(domain, ctx.coordinator),
                basis=(f"Reported by the arbiter on {long_day} (check 10). {'; '.join(lines10)}. "
                       f"Move the history out to `{folder}Archives/`, cited in one line; the checkpoint fits in 10 KB "
                       "(method §6).")))
    reported = [d for d in everyone if by_domain.get(d) or too_heavy.get(d) or late_ones.get(d)]
    return findings, reported


def is_open(c: dict) -> bool:
    return c.get("status") != "accepted"


def reported_before(finding: Finding, living: list[dict], archived_ids: set[str], ctx: Context):
    """(id to write, None) if the finding is to be filed, otherwise (None, the workstream that covers it)."""
    ids = {c["id"] for c in living if c.get("id")}
    i = finding.id
    covering = None
    m = re.match(r"arbiter-c9-checkpoint-(.+)-\d{8}$", i)
    if m:
        covering = next((c for c in living if c.get("id") and is_open(c)
                         and re.fullmatch(rf"arbiter-c9-checkpoint-{re.escape(m.group(1))}-\d{{8}}", c["id"])), None)
    elif i.startswith("arbiter-c9-table-"):
        covering = next((c for c in living if c.get("id", "").startswith("arbiter-c9-table-") and is_open(c)), None)
    elif i.startswith("arbiter-c10-short-checkpoint-"):
        covering = next((c for c in living if c.get("id") and is_open(c) and c.get("for") == finding.for_
                         and "short-checkpoint" in c["id"]), None)
    if covering is not None:
        return None, covering
    if i in ids:
        return None, next(c for c in living if c.get("id") == i)
    if i in archived_ids:  # an archived id is not reused
        i = f"{i}-{ctx.stamp}"
        if i in ids or i in archived_ids:
            return None, next((c for c in living if c.get("id") == i), {"id": i, "for": finding.for_})
    return i, None


# ───────────────────────────── writing workstreams.yaml ─────────────────────────────

def yaml_value(archiver, checker, value: str) -> str:
    value = " ".join(value.split())
    return value if checker.value_conforms(value) else archiver.quoted(value)


def yaml_entry(finding: Finding, written_id: str, archiver, checker) -> str:
    def v(text):
        return yaml_value(archiver, checker, text)
    lines = [f"- id: {v(written_id)}",
             f"  title: {v(finding.title)}",
             f"  module: {v(finding.module)}",
             "  category: doc",
             "  status: to-brief",
             f"  for: {v(finding.for_)}",
             "  priority: medium",
             "  complexity: low",
             f"  cost: {v('none; a correction in the living docs')}",
             f"  basis: {v(finding.basis)}",
             "  refs: Method/ARBITER.md"]
    return "\n".join(lines) + "\n"


def append_at_end(path: Path, entries: list[str]) -> None:
    """The entries at the end of the file, separated by an empty line; no existing line is touched."""
    text = path.read_bytes().decode("utf-8")
    if text and not text.endswith("\n"):
        text += "\n"
    if text and not text.endswith("\n\n"):
        text += "\n"
    path.write_bytes((text + "\n".join(entries)).encode("utf-8"))


def file_findings(findings: list[Finding], a, ctx: Context, archiver, checker, new: list, existing: list) -> None:
    """Files the findings that were not reported before; new and existing: lists of (id, for)."""
    path = Path(a.workstreams)
    living = checker.read_workstreams(path)
    archived_ids = {c["id"] for c in checker.read_archives(Path(a.archives)) if c.get("id")}
    entries = []
    for finding in findings:
        written_id, covering = reported_before(finding, living, archived_ids, ctx)
        if written_id is None:
            existing.append((covering.get("id", finding.id), covering.get("for") or finding.for_))
            continue
        entries.append(yaml_entry(finding, written_id, archiver, checker))
        living.append({"id": written_id, "status": "to-brief", "for": finding.for_})
        new.append((written_id, finding.for_))
    if entries:
        append_at_end(path, entries)


# ───────────────────────────── the batons and the lateness ─────────────────────────────

def baton_identifier(text: str) -> str | None:
    """The identifier of the "Session active" line; None if the line says "none", "not applicable" or does not exist."""
    for line in text.split("\n"):
        if RE_BATON.match(line):
            m = RE_IDENTIFIER.match(line)
            return m.group(1) if m else None
    return None


def git_instant(root: Path, *arguments) -> datetime | None:
    code, output = git(root, "log", "-1", "--format=%cI", *arguments)
    if code != 0 or not output:
        return None
    try:
        return datetime.fromisoformat(output)
    except ValueError:
        return None


@dataclass
class Baton:
    domain: str
    identifier: str
    when: datetime
    with_commit: bool


def read_batons(ctx: Context, root: Path, now: datetime) -> list[Baton]:
    """The batons silent for more than 24 hours; the coordination is excluded.

    The last commit that carries the identifier ("git log --grep"); with none, the last commit that touches the
    checkpoint stands for the baton being set."""
    silent = []
    for d in ctx.valid:
        if "Coordination" in d.get("pl", "") or "Coordinator" in d.get("pl", ""):
            continue
        try:
            text = (root / d["checkpoint"]).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        identifier = baton_identifier(text)
        if not identifier:
            continue
        when = git_instant(root, "--fixed-strings", f"--grep={identifier}", "HEAD")
        with_commit = when is not None
        if when is None:
            when = git_instant(root, "HEAD", "--", d["checkpoint"])
        if when is not None and now - when > SILENCE:
            silent.append(Baton(d["domain"], identifier, when, with_commit))
    return silent


def baton_text(now: datetime, silent: list[Baton]) -> str:
    if not silent:
        return "batons fresh"
    b = min(silent, key=lambda s: s.when)
    when = b.when.astimezone(now.tzinfo).strftime("%Y-%m-%d %H:%M")
    detail = f"last commit on {when}" if b.with_commit else f"no commit, checkpoint touched on {when}"
    return f"{b.domain} ({b.identifier}, {detail})"


def read_lates(ctx: Context, root: Path) -> dict[str, list[str]]:
    """Per domain, the accepted workstreams whose accepted-on: date follows the checkpoint's last commit."""
    lates: dict[str, list[str]] = {}
    for d in ctx.valid:
        code, output = git(root, "log", "-1", "--format=%cs", "--", d["checkpoint"])
        if code != 0 or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", output):
            continue
        for c in ctx.workstreams:
            accepted = c.get("accepted-on", "")
            if (c.get("status") != "accepted" or "for" in c or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", accepted)
                    or ctx.domain_of(c) != d["domain"]):
                continue
            try:
                later = date.fromisoformat(accepted) > date.fromisoformat(output)
            except ValueError:
                continue
            if later:
                lates.setdefault(d["domain"], []).append(
                    f"{d['domain']}: {c['id']} has been accepted since {accepted}, "
                    f"the checkpoint has not been touched since {output}")
    return lates


# ───────────────────────────── the scripts called ─────────────────────────────

def normalize(a) -> int:
    process = run(HERE / "archive_workstreams.py", "normalize", "--workstreams", a.workstreams,
                  "--archives", a.archives, "--domains", a.domains)
    if process.returncode not in (0, 1):
        raise Impossible("archive_workstreams.py", f"archive_workstreams.py normalize failed (code "
                                                   f"{process.returncode}): {last_line(process)}")
    m = re.search(r"normalize · (\d+) value", process.stdout)
    return int(m.group(1)) if m else 0


@dataclass
class Archiving:
    dated: int = 0
    archived: int = 0
    warnings: list = field(default_factory=list)
    error: str = ""


def archive(a, day: date) -> Archiving:
    process = run(HERE / "archive_workstreams.py", "archive", "--workstreams", a.workstreams,
                  "--archives", a.archives, "--date", day.isoformat())
    result = Archiving()
    if process.returncode not in (0, 1):
        result.error = f"{last_line(process)}"
        return result
    m = re.search(r"archive · (\d+) dated, (\d+) date\(s\) removed, (\d+) archived", process.stdout)
    if m:
        result.dated, result.archived = int(m.group(1)), int(m.group(3))
    result.warnings = [line for line in process.stdout.split("\n") if line.startswith("id ")]
    return result


def regenerate_board(a) -> None:
    process = run(Path(a.generator), Path(a.workstreams).resolve(), Path(a.board).resolve())
    if process.returncode != 0:
        raise Impossible(a.generator, f"the generator failed (code {process.returncode}): {last_line(process)}")


def archiving_findings(archiving: Archiving, ctx: Context, day: date) -> list[Finding]:
    findings = []
    for line in archiving.warnings:
        m = re.match(r"id (\S+): ", line)
        i = m.group(1) if m else safe_key(line[:40])
        findings.append(Finding(
            id=f"arbiter-ca-archiving-{safe_key(i)}", title=f"Archiving: {line}",
            module=ctx.module_of(ctx.by_id.get(i)), for_=ctx.coordinator,
            basis=(f"Reported by the arbiter on {long_date(day)} (archiving). {line}. "
                   "Have the owner fix the accepted-on: date (YYYY-MM-DD): the arbiter does not correct it.")))
    return findings


# ───────────────────────────── the log and the output ─────────────────────────────

def count(n: int, singular: str, plural: str) -> str:
    return f"{n} {singular if n == 1 else plural}"


def footprint_kb(a, ctx: Context, root: Path) -> int:
    """The sum of the sizes of the method, the sheet and all the table's checkpoints, in KB (1 KB = 1024 bytes)."""
    files = {}
    for option in (a.method, a.sheet):
        if option:
            files[Path(option).resolve()] = Path(option)
    for d in ctx.table:
        if d.get("checkpoint"):
            files[(root / d["checkpoint"]).resolve()] = root / d["checkpoint"]
    total = sum(path.stat().st_size for path in files.values() if path.is_file())
    return int(total / 1024 + 0.5)


def append_to_log(path: Path, line: str) -> None:
    text = path.read_bytes().decode("utf-8")
    if text and not text.endswith("\n"):
        text += "\n"
    path.write_bytes((text + line + "\n").encode("utf-8"))


def commit_message(day: date, findings: int, gaps: int, archiving: Archiving, normalized: int) -> str:
    base = f"{findings} finding(s)" if findings or gaps else "living docs compliant"
    rest = []
    if base == "living docs compliant" and archiving.dated:
        rest.append(f"{archiving.dated} dated")
    if archiving.archived:
        rest.append(f"{archiving.archived} archived")
    if normalized:
        rest.append(f"{normalized} value(s) normalized")
    return f"Arbiter {day.isoformat()}: " + ", ".join([base] + rest)


def check_prerequisites(a, root: Path) -> None:
    """A file that is missing is a code 2, before any writing."""
    for option in FILE_OPTIONS:
        path = getattr(a, option)
        if path and not Path(path).is_file():
            raise Impossible(path, f"file not found: {path}")
    for option in ("archives", "root"):
        path = getattr(a, option)
        if path and not Path(path).is_dir():
            raise Impossible(path, f"folder not found: {path}")
    for script in ("check_living_docs.py", "archive_workstreams.py"):
        if not (HERE / script).is_file():
            raise Impossible(script, f"script not found: {HERE / script}")
    code, _ = git(root, "rev-parse", "--git-dir")
    if code != 0:
        raise Impossible("git repository", f"{root} is not a git repository")


def make_run(a, now: datetime) -> int:
    root = Path(a.root) if a.root else Path(".")
    day = now.date()
    check_prerequisites(a, root)
    checker, archiver = load("check_living_docs.py"), load("archive_workstreams.py")
    table = checker.read_workstreams(Path(a.domains))
    ctx = Context(checker, [], [], table, a.domains)  # the coordinator first: without one, nothing is written
    ctx.stamp = day.strftime("%Y%m%d")
    workstreams_before = Path(a.workstreams).read_bytes()

    normalized = normalize(a)                                    # 1
    check = run_check(a)                                         # 2
    ctx.workstreams = checker.read_workstreams(Path(a.workstreams))
    ctx.archives = checker.read_archives(Path(a.archives))
    ctx.by_id = {c["id"]: c for c in ctx.workstreams if c.get("id")}
    silent = read_batons(ctx, root, now)                         # 4
    lates = read_lates(ctx, root)                                # 5
    new, existing = [], []
    findings_9, reported = checkpoint_findings(check, lates, ctx, day)
    findings = ordinary_findings(check, ctx, day) + findings_9
    file_findings(findings, a, ctx, archiver, checker, new, existing)  # 3
    archiving = archive(a, day)                                  # 6
    if archiving.warnings:
        ctx.workstreams = checker.read_workstreams(Path(a.workstreams))
        ctx.by_id = {c["id"]: c for c in ctx.workstreams if c.get("id")}
        file_findings(archiving_findings(archiving, ctx, day), a, ctx, archiver, checker, new, existing)
    final = check
    if Path(a.workstreams).read_bytes() != workstreams_before:   # 7
        if a.board:
            regenerate_board(a)
        final = run_check(a)
    gaps = final.gaps() + (1 if lates else 0)

    baton = baton_text(now, silent)
    checkpoints = ", ".join(reported) if reported else "up to date"
    if archiving.error:
        archiving_text = f"archiving: impossible, {archiving.error}"
    else:
        archiving_text = f"archiving: {archiving.dated} dated, {archiving.archived} archived"
    kb = footprint_kb(a, ctx, root)
    line = " · ".join([now.strftime("%Y-%m-%d %H:%M"), count(gaps, "gap", "gaps"),
                       count(len(new), "new finding", "new findings"),
                       baton, archiving_text, f"checkpoints: {checkpoints}", f"footprint: {kb} KB"])
    append_to_log(Path(a.arbiter_log), "- " + line)              # 8

    commit = commit_message(day, len(new), gaps, archiving, normalized)
    summary(day, final, gaps, new, existing, baton, archiving_text, checkpoints, kb, commit, archiving.error,
            list(lates))  # 9
    if archiving.error:
        print(f"archiving impossible: {archiving.error}", file=sys.stderr)
        return 2
    return 1 if new else 0


def summary(day: date, final: Check, gaps: int, new: list, existing: list, baton: str, archiving_text: str,
            checkpoints: str, kb: int, commit: str, error: str, lates: list) -> None:
    if not gaps and not new and not error:
        print(f"Living docs compliant on {day.isoformat()}")
    else:
        print(f"Arbiter run on {day.isoformat()} · {count(gaps, 'gap', 'gaps')}")
        if final.summary:
            print(f"Check · {final.summary}")
        if lates:
            print(f"Late checkpoint · {', '.join(lates)}")
        print(f"New findings ({len(new)}):")
        for i, for_ in new:
            print(f"  - {i} · for {for_}")
        print(f"Reported before and still there ({len(existing)}):")
        for i, for_ in existing:
            print(f"  - {i} · for {for_}")
    print(f"Batons · {baton}")
    print(f"Archiving · {archiving_text.removeprefix('archiving: ')}")
    print(f"Checkpoints · {checkpoints}")
    print(f"Footprint · {kb} KB")
    print(f"Commit: {commit}")


def fail(a, now: datetime, error: Impossible) -> int:
    """A code 2: the log says "check impossible", nothing else is written."""
    print(f"arbiter: {error.detail}", file=sys.stderr)
    log = Path(a.arbiter_log)
    if log.is_file():
        append_to_log(log, f"- {now.strftime('%Y-%m-%d %H:%M')} · check impossible: {error.file}")
        print(f"Check impossible: {error.file}")
        print(f"Commit: Arbiter {now.date().isoformat()}: check impossible")
    return 2


def main(argv: list[str]) -> int:
    try:
        a = read_arguments(argv)
        now = read_date(a.date)
    except ValueError as error:
        print(f"arbiter: {' '.join(str(error).split())}", file=sys.stderr)
        return 2
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        return make_run(a, now)
    except Impossible as error:
        return fail(a, now, error)
    except (OSError, UnicodeDecodeError) as error:
        return fail(a, now, Impossible(getattr(error, "filename", None) or "arbiter.py", str(error)))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
