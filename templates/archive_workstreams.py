#!/usr/bin/env python3
"""Archiving of accepted workstreams, and search for a workstream, living or archived.

A "living docs" repository keeps the list of workstreams in workstreams.yaml. A finished
workstream goes to "status: accepted" and stays there: the file grows without end. This script
automatically moves the workstreams accepted for long enough into frozen archives (one per
month), and makes it possible to find an archived workstream.

    python3 -B archive_workstreams.py archive --workstreams <workstreams.yaml> --archives <folder> \\
        [--delay <days, 7 by default>] [--date YYYY-MM-DD] [--dry-run]
    python3 -B archive_workstreams.py search <pattern> --workstreams <workstreams.yaml> \\
        --archives <folder> [--everywhere]

The shape of the file: workstreams.yaml is NOT standard YAML and is read without a
library. An entry starts with "- id: <id>" in column 0; its other keys follow, one per
line, as "<two spaces><key>: <value>". The block of an entry is that line and the key
lines that follow it, up to the first line that does not have that shape. The empty lines
and the comments between blocks are never touched.

"archive" applies these rules, in order:
  1. date: an entry in "status: accepted" without "accepted-on:" gets the line
     "accepted-on: <today's date>" right after its "status:";
  2. undate: an entry that carries "accepted-on:" but is no longer accepted (a reopened
     workstream) loses that line;
  3. an unreadable date (an "accepted-on:" that is not a valid YYYY-MM-DD): the entry is neither
     archived nor modified, the script reports it and ends with code 1;
  4. move out: every accepted entry whose "accepted-on:" + delay days <= today's date
     is appended, block as is, at the end of <folder>/WORKSTREAMS_<YYYY-MM>.yaml (the month
     of today) and removed from workstreams.yaml. An entry dated in this very run does not leave;
  5. the month's archive is created with a header, or completed: things are only appended to it;
  6. in workstreams.yaml only the lines of the blocks moved out are removed, never leaving
     two empty lines in a row;
  7. lossless, checked before writing: the non-empty lines of the old file, plus the
     "accepted-on:" lines added, minus those removed, equal (as a multiset) the non-empty
     lines of the new file plus those of the blocks added to the archive;
  8. the archive is written first, then workstreams.yaml through a temporary file and
     os.replace; nothing is written if nothing changes; run again at the same date, no
     change.
"--date" replaces today's date; "--dry-run" says what would be done without writing anything.
The archive folder must exist: it is never created.

"search" looks in workstreams.yaml then in each <folder>/WORKSTREAMS_*.yaml (in name
order). A pattern equal to an id (case included) gives that single workstream; otherwise
the pattern is looked for, case-insensitively, in the id and the title (in all the values with
"--everywhere"). One line per entry: "<path>:<line> · <id> · <status> · <title>";
if there is only one, its complete block follows.

Exit code of "archive": 0 done (with or without change), 1 done with at least one
warning, 2 invalid call, file or folder not found, or check 7 failing
(nothing is written). Exit code of "search": 0 at least one found, 1 none, 2 invalid call
or file not found.

Python 3.11 and later, standard library only.
"""
import argparse
import os
import re
import shutil
import sys
import tempfile
from collections import Counter
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

RE_ENTRY = re.compile(r"^- id:(.*)$")
RE_KEY = re.compile(r"^  ([a-z][a-z0-9-]*):(.*)$")
RE_DATE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")

MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August",
          "September", "October", "November", "December"]

DEFAULT_DELAY = 7


@dataclass
class Block:
    """One entry: lines [start, end) of the file; keys: key -> (line index, value)."""
    start: int
    end: int
    id: str
    keys: dict = field(default_factory=dict)

    @property
    def line(self) -> int:
        return self.start + 1

    def value(self, key: str) -> str:
        return self.keys[key][1] if key in self.keys else ""


def read_lines(path: Path) -> tuple[list[str], bool]:
    """The lines of the file (without their ending) and: does the file end with a line ending?"""
    text = path.read_bytes().decode("utf-8")
    lines = text.split("\n")
    if lines[-1] == "":
        return lines[:-1], True
    return lines, False


def assemble(lines: list[str], final: bool) -> str:
    return "\n".join(lines) + ("\n" if final and lines else "")


def find_blocks(lines: list[str]) -> list[Block]:
    """The entries of the file, each with its keys (first occurrence of a key)."""
    blocks: list[Block] = []
    for i, line in enumerate(lines):
        m = RE_ENTRY.match(line)
        if m:
            blocks.append(Block(i, i + 1, m.group(1).strip(), {"id": (i, m.group(1).strip())}))
            continue
        m = RE_KEY.match(line)
        if m and blocks and blocks[-1].end == i:
            blocks[-1].end = i + 1
            blocks[-1].keys.setdefault(m.group(1), (i, m.group(2).strip()))
    return blocks


def read_date(value: str) -> date | None:
    if not RE_DATE.match(value):
        return None
    try:
        return date(int(value[0:4]), int(value[5:7]), int(value[8:10]))
    except ValueError:
        return None


def key_of(line: str) -> str:
    m = RE_KEY.match(line)
    return m.group(1) if m else ""


@dataclass
class Plan:
    """What a run would do: lines to insert, to remove, blocks to move out, warnings."""
    insert: dict = field(default_factory=dict)     # line index -> line to insert after
    remove: set = field(default_factory=set)       # indices of "accepted-on:" lines to remove
    leaving: list = field(default_factory=list)    # blocks to move out, in file order
    warnings: list = field(default_factory=list)
    dated: int = 0
    undated: int = 0


def plan_run(lines: list[str], blocks: list[Block], today: date, delay: int) -> Plan:
    plan = Plan()
    for b in blocks:
        accepted = b.value("status") == "accepted"
        if not accepted:
            dated = [i for i in range(b.start, b.end) if key_of(lines[i]) == "accepted-on"]
            plan.remove.update(dated)
            plan.undated += bool(dated)
        elif "accepted-on" not in b.keys:
            i = b.keys["status"][0]
            ending = "\r" if lines[i].endswith("\r") else ""
            plan.insert[i] = f"  accepted-on: {today.isoformat()}{ending}"
            plan.dated += 1
        else:
            value = b.value("accepted-on")
            day = read_date(value)
            if day is None:
                plan.warnings.append(f"id {b.id}: unreadable accepted-on “{value}”")
            elif (today - day).days >= delay:
                plan.leaving.append(b)
    return plan


def trailing_empty_lines(lines: list) -> int:
    n = 0
    while n < len(lines) and lines[-1 - n] is not None and not lines[-1 - n].strip():
        n += 1
    return n


def rebuild(lines: list[str], plan: Plan) -> list[str]:
    """The lines of workstreams.yaml after the plan: dates set, blocks moved out removed."""
    left = {i for b in plan.leaving for i in range(b.start, b.end)}
    starts = {b.start for b in plan.leaving}
    output: list = []
    for i, line in enumerate(lines):
        if i in left:
            if i in starts:
                output.append(None)  # marker: a block was moved out here
            continue
        if i in plan.remove:
            continue
        output.append(line)
        if i in plan.insert:
            output.append(plan.insert[i])
    return tighten(output, trailing_empty_lines(lines), trailing_empty_lines(lines[::-1]))


def bound_of_the_run(i: int, j: int, total: int, trailing: int, leading: int) -> int:
    """How many empty lines to keep around a marker: one, except at the start and the end of the file."""
    if i == 0:
        return leading
    return 1 if j < total else trailing


def tighten(output: list, trailing: int, leading: int) -> list[str]:
    """At each marker, the run of empty lines around it is reduced to one at most."""
    result: list[str] = []
    i = 0
    while i < len(output):
        if output[i] is not None and output[i].strip():
            result.append(output[i])
            i += 1
            continue
        j = i
        while j < len(output) and (output[j] is None or not output[j].strip()):
            j += 1
        empties = [x for x in output[i:j] if x is not None]
        if any(x is None for x in output[i:j]):
            empties = empties[:bound_of_the_run(i, j, len(output), trailing, leading)]
        result.extend(empties)
        i = j
    return result


def non_empty(lines) -> Counter:
    return Counter(line for line in lines if line.strip())


def archive_header(today: date, delay: int) -> str:
    month = f"{MONTHS[today.month - 1]} {today.year}"
    return (f"# Archived workstreams — {month}\n"
            "#\n"
            "# Moved automatically out of workstreams.yaml by archive_workstreams.py: workstreams accepted for\n"
            f"# at least {delay} days (key accepted-on). Same form as workstreams.yaml (not standard YAML).\n"
            "# Things are only appended to it; frozen at the end of the month. Search: archive_workstreams.py search <word>\n"
            "\n")


def text_of_blocks(lines: list[str], blocks: list[Block]) -> str:
    return "\n".join("\n".join(lines[b.start:b.end]) + "\n" for b in blocks)


def new_archive(existing: str | None, addition: str, header: str) -> str:
    if existing is None:
        return header + addition
    if existing and not existing.endswith("\n"):
        existing += "\n"
    if existing and not existing.endswith("\n\n"):
        existing += "\n"
    return existing + addition


def write(path: Path, content: str) -> None:
    """Writing through a temporary file in the same folder, then os.replace."""
    descriptor, temporary = tempfile.mkstemp(prefix=".archive-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as output:
            output.write(content.encode("utf-8"))
        if path.exists():
            shutil.copymode(path, temporary)
        else:
            os.chmod(temporary, 0o644)
        os.replace(temporary, path)
    except BaseException:
        if os.path.exists(temporary):
            os.unlink(temporary)
        raise


def command_archive(a) -> int:
    workstreams, folder = Path(a.workstreams), Path(a.archives)
    if not workstreams.is_file():
        raise ValueError(f"file not found: --workstreams {workstreams}")
    if not folder.is_dir():
        raise ValueError(f"folder not found: --archives {folder}")
    today = a.today
    lines, final = read_lines(workstreams)
    plan = plan_run(lines, find_blocks(lines), today, a.delay)
    archive = folder / f"WORKSTREAMS_{today.year:04d}-{today.month:02d}.yaml"
    new_lines = rebuild(lines, plan)
    addition = text_of_blocks(lines, plan.leaving)
    added = list(plan.insert.values())
    removed = [lines[i] for i in plan.remove]
    expected = non_empty(lines) + non_empty(added) - non_empty(removed)
    received = non_empty(new_lines) + non_empty(addition.split("\n"))
    if expected != received:
        raise FailedCheck("loss check failing: nothing is written")
    change = bool(plan.insert or plan.remove or plan.leaving)
    if change and not a.dry_run:
        if plan.leaving:
            existing = archive.read_bytes().decode("utf-8") if archive.is_file() else None
            write(archive, new_archive(existing, addition, archive_header(today, a.delay)))
        write(workstreams, assemble(new_lines, final))
    print_summary(plan, archive)
    return 1 if plan.warnings else 0


def print_summary(plan: Plan, archive: Path) -> None:
    to = f" to {archive}" if plan.leaving else ""
    print(f"archive · {plan.dated} dated, {plan.undated} date(s) removed, {len(plan.leaving)} archived{to}")
    for b in plan.leaving:
        print(f"  {b.id}")
    for warning in plan.warnings:
        print(warning)


def files_to_search(workstreams: Path, folder: Path) -> list[Path]:
    return [workstreams] + sorted(p for p in folder.glob("WORKSTREAMS_*.yaml") if p.is_file())


def entries_found(files: list[Path], pattern: str, everywhere: bool) -> list[tuple[Path, list[str], Block]]:
    """The entries that answer the pattern: an equal id first, otherwise a case-insensitive substring."""
    every = []
    for file in files:
        lines, _ = read_lines(file)
        every += [(file, lines, b) for b in find_blocks(lines)]
    exact = [t for t in every if t[2].id == pattern]
    if exact:
        return exact
    small = pattern.casefold()
    return [t for t in every if any(small in v.casefold() for v in values_searched(t[2], everywhere))]


def values_searched(block: Block, everywhere: bool) -> list[str]:
    keys = block.keys if everywhere else ("id", "title")
    return [block.value(key) for key in keys]


def command_search(a) -> int:
    workstreams, folder = Path(a.workstreams), Path(a.archives)
    if not workstreams.is_file():
        raise ValueError(f"file not found: --workstreams {workstreams}")
    if not folder.is_dir():
        raise ValueError(f"folder not found: --archives {folder}")
    found = entries_found(files_to_search(workstreams, folder), a.pattern, a.everywhere)
    for file, _, b in found:
        print(f"{file}:{b.line} · {b.id} · {b.value('status')} · {b.value('title')}")
    if len(found) == 1:
        _, lines, b = found[0]
        print("\n".join(lines[b.start:b.end]))
    print(f"search · {len(found)} found")
    return 0 if found else 1


class FailedCheck(Exception):
    """The "lossless" check (rule 7) failed."""


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError(reworded(message))


def reworded(message: str) -> str:
    """The messages of the argument parser, reworded."""
    rewordings = [
        (r"the following arguments are required: (.*)", r"missing argument: \1"),
        (r"unrecognized arguments: (\S*).*", r"unknown argument: \1"),
        (r"argument (\S+): expected one argument", r"\1: missing value"),
        (r"argument (\S+): invalid int value: (.*)", r"\1: an integer is expected, got \2"),
        (r"argument command: invalid choice: (\S+).*", r"unknown command: \1 (archive or search)"),
    ]
    for pattern, replacement in rewordings:
        if re.fullmatch(pattern, message):
            return re.sub(pattern, replacement, message)
    return message


def build_parser() -> argparse.ArgumentParser:
    p = Parser(prog="archive_workstreams.py", allow_abbrev=False, add_help=False)
    sub = p.add_subparsers(dest="command", required=True)
    arch = sub.add_parser("archive", allow_abbrev=False, add_help=False)
    find = sub.add_parser("search", allow_abbrev=False, add_help=False)
    for s in (arch, find):
        s.add_argument("--workstreams", required=True)
        s.add_argument("--archives", required=True)
    arch.add_argument("--delay", type=int, default=DEFAULT_DELAY)
    arch.add_argument("--date")
    arch.add_argument("--dry-run", dest="dry_run", action="store_true")
    find.add_argument("pattern")
    find.add_argument("--everywhere", action="store_true")
    return p


def read_arguments(argv: list[str]):
    a = build_parser().parse_args(argv)
    if a.command == "archive":
        if a.delay < 0:
            raise ValueError("--delay: a positive number of days or zero is expected")
        a.today = date.today()
        if a.date is not None:
            a.today = read_date(a.date)
            if a.today is None:
                raise ValueError(f"--date: YYYY-MM-DD expected, got “{a.date}”")
    return a


def main(argv: list[str]) -> int:
    try:
        a = read_arguments(argv)
        return command_archive(a) if a.command == "archive" else command_search(a)
    except (ValueError, FailedCheck, OSError, UnicodeDecodeError) as error:
        print(f"archive_workstreams: {' '.join(str(error).split())}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
