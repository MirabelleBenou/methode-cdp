#!/usr/bin/env python3
"""Shared living-docs checker — read-only checks.

When several project leads write to a living-docs repository at the same time,
this script checks that the shared documents stay consistent: the decision
log, the workstreams source (workstreams.yaml), the fixed page and the data file
regenerated from it (workstreams.html and workstreams.json, next to it) and the plan's
version log.

    python3 -B check_living_docs.py --workstreams <workstreams.yaml> --log <decision_log.md> \\
        [--board <workstreams.html> --generator <make_board.py>] [--plan <plan.md>] \\
        [--archives <folder>] [--domains <file> [--root <folder>] [--checkpoint-cap <bytes>]
                                 [--workstream-cap <bytes>] [--log-cap <characters>] [--log-from <n>]]

"--board" and "--generator" go together; "--board" names the page, its data file is the one
next to it, same name in ".json"; "--plan" is optional.
"--archives" gives the folder of the workstream archives (the WORKSTREAMS_*.yaml files, same
form as workstreams.yaml, which archive_workstreams.py makes); it must exist. Without this
option, nothing changes. With it, four checks extend to the archives: 3, 4 (its rule for the
batches in flight), 7 and 11.
"--domains" gives the domain table (see check 9) and triggers that check, then
extends 11 to the table;
"--root" is the folder the paths of that table are read from (the current folder
by default); it is only used with "--domains". "--checkpoint-cap" gives the size cap of a
checkpoint, in bytes (a positive integer, 10240 by default): a checkpoint is re-read in full at
every resumption, so it must stay short (see check 10); it too is only used with "--domains".
Likewise "--workstream-cap" (bytes, 1536 by default), "--log-cap" (characters, 800 by default) and
"--log-from" (the number of the first decision log entry that is measured; without it, the log is not
measured): positive integers, only used with "--domains" (see check 12). A check whose files are
not given shows "not requested".

The twelve checks, in this order:
  1. decision numbers: the lines "| **D<n>** |" have no duplicated number and
     no gap between the smallest and the largest;
  2. reservations: a line "| **D<n>** | *reserved …" still present is a
     warning, not a gap (a reservation lives while the entry is being written);
  3. workstream ids: no duplicated "id:" in workstreams.yaml; with "--archives", also: no id
     of workstreams.yaml that appears in an archive, no id present twice in the archives, and
     the count becomes "<n> workstreams, <a> archived";
  4. batch versions: (a) no "version:" value carried by two entries of workstreams.yaml;
     (b) an entry in "status: in-flight" that carries "version:" and "deliverable:" carries a
     version strictly higher than every other "version:" of the same "deliverable:", in
     workstreams.yaml and, with "--archives", in the archives: this is the rule of the number
     of a batch (method §1 bis). A version is compared by the sequence of numbers of its
     version token: the first occurrence, bounded by a non-alphanumeric character or the edge,
     of "[vV]?<n>.<n>[.<n>…]" or of "[vV]<n>" ("v1.0065" -> (1, 65); "agent-v0.1.1" ->
     (0, 1, 1); "AC-V1.5.1" -> (1, 5, 1); "v1.10 (D205)" -> (1, 10); "v19" -> (19,)); a value
     without a token is not compared ("18a2957, no release (D188)": neither the hash nor the
     decision number is a version). One gap line per entry in flight at fault, which names
     the highest of the other versions: "<id>: <version> is not above <other version>
     (<other id>)". The count stays "<n> versions" (distinct values of workstreams.yaml);
  5. workstreams in flight: every "status: in-flight" entry carries a non-empty "pl:";
  6. board: the fixed page and its data file (the one next to "--board", same name
     in ".json") are byte-identical to the regeneration of workstreams.yaml by the
     generator, made in a temporary folder under the same page name, after
     replacing in the texts of each pair every date "dd/mm/yyyy" with the same
     token (the generator dates the data file with the day it runs). One gap per
     file that differs (first byte and line); one gap if the published data file is
     missing ("data file missing: <path>"); the count gives the bytes of the page
     and of the data;
  7. version log: the last version of the log (the last line of the plan that
     starts with "| `v…` |") has a workstreams.yaml entry in "status: accepted"
     whose id or version contains it; with "--archives", this entry is also looked for in
     the archives (an archived entry was accepted). It checks that the log and the
     workstreams agree, not the number of a fix: that is rule (b) of check 4;
  8. deliverables and resources: a deliverable ("deliverable:", the code
     repository the release comes out of) and a shared resource ("resource:", a
     machine or a piece of software two batches cannot occupy at the same time)
     each have a single batch in flight at a time, and a batch that waits
     ("waits: <id>") is suspended. Three rules: (a) for each value of
     "deliverable:" and for each value of "resource:", at most one entry in
     "status: in-flight" (the two namespaces are separate: a deliverable and a
     resource of the same name do not mix; an entry may carry both and then
     counts for each); (b) every "waits:" names the id of an entry that exists;
     (c) an entry that carries "waits:" is not in "status: in-flight". The count
     is "<n> deliverables, <r> resources, <m> in flight, <k> waiting": distinct
     values of each field, in-flight entries that carry a deliverable or a
     resource (an entry carrying both counts once), entries that carry "waits:".
     This check depends on "--workstreams" only: it always runs;
  9. checkpoints: every domain (a project lead, a scope) has a checkpoint, a free
     document one section of which carries its queue (what comes next). The check
     cross-checks that queue and the document with workstreams.yaml. It needs "--domains"; it
     reads the domain table in the same form as workstreams.yaml: an entry
     starts with "- domain:", one key per line, blank lines and "#" ignored.
     The keys: "domain" (short name), "pl" (the domain's project lead),
     "checkpoint" (path of the checkpoint, relative to "--root"), "queue" (the exact
     start of the queue section's title, a line that starts with this value; empty: no
     queue section declared, which is a gap of the domain), "modules" (the workstreams.yaml
     modules of the domain, separated by spaces, may be empty) and "prefixes" (optional: starts of the domain's ids).
     An entry of workstreams.yaml belongs to the first domain that fits, following this
     order of rules: its "pl:" equals the domain's, otherwise its id starts with one of
     the prefixes, otherwise its "module:" is one of the modules; otherwise it belongs to
     no domain. An id is cited by a checkpoint if it appears there between backticks
     (`id`). The queue section runs from its title line to the next line that starts
     with "## ", or to the end of the file. Two rules: (b) the queue cites no closed
     workstream, that is one in "status: accepted" or only archived (the archives come
     from "--archives"); (c) every entry of the domain in "status" upcoming, to-brief,
     debt or in-flight, with no "for:" key (a message, not a subject), is cited IN THE
     QUEUE SECTION of the checkpoint (the same one rule (b) reads): an entry cited only
     elsewhere in the checkpoint is a gap. An empty "queue:" makes one gap line of the
     domain ("no queue section declared"); without a queue section, rule (c) looks for the
     citation in the whole checkpoint. That gap line is placed before the (c) lines; (b)
     does not apply to it, (c) does. A faulty
     table (checkpoint not found, queue section not found, entry with no "domain" or no
     "checkpoint") is a gap, and the domain is not checked any further. The count is
     "<n> domains, <b> cited closed, <c> not cited, <v> without a queue section";
 10. checkpoint size: a checkpoint is re-read in full at every session resumption; above
     the cap, it costs at every resumption and its history must go to an archive. The
     check needs "--domains". For each domain (in the order of the table) that has a
     "domain" and a "checkpoint", it measures the size in bytes of the checkpoint file on
     disk; strictly above "--checkpoint-cap" (10240 by default), that is one gap line
     "<domain>: <path> weighs <n> bytes, cap <p>" (the path as written in the table). A
     checkpoint not found, or an entry with no "domain" or no "checkpoint", is ignored here:
     check 9 already reports it. The count is "<n> domains, <k> above <p> bytes", <n> being
     the entries that have a domain and a checkpoint;
 11. YAML format: every value of workstreams.yaml ("--workstreams"), of the archives (if
     "--archives" is given) and of the domain table (if "--domains" is given) is a safe YAML
     scalar, so that a standard YAML parser reads the same values as this script. A value
     conforms if it is empty; or bare and safe (no ":" followed by a space or the end of the
     line, no "#" preceded by a space, no tab or control character, and not starting with any
     of - ? : , [ ] { } # & * ! | > ' " % @ ` ); or between double quotes, where only \\" and
     \\\\ are escapes. The check always runs. OK: "<n> files, <m> lines read"; GAP: "<k>
     non-conforming value(s), <n> files, <m> lines read", the first five non-conforming
     values ("file:line : key <key>"), then the command that normalizes
     ("archive_workstreams.py normalize", which rewrites only those values);
 12. entry sizes: a workstream entry or a decision log entry is re-read at every resumption; above
     its cap, its detail goes to the batch folder or to a note, and the entry only keeps the summary and
     the path. The check needs "--domains". Workstream entries measured: those of workstreams.yaml (not
     of the archives) in "status" upcoming, to-brief, debt or in-flight, except those whose id starts
     with "arbiter-" (the arbiter's findings are closed by fixing their cause); an entry with "for:" is
     measured. Its size is the number of UTF-8 bytes of the file's lines from its "- id:" line to the line
     before the next one, without the empty lines or those whose first non-blank character is "#" (the
     section banners), each followed by a line break; a gap if strictly above "--workstream-cap" (1536
     by default). Decision log entries measured: the lines "| **D<n>** |" whose number is at least
     "--log-from", except the reservations; their size is the number of characters of the line, line break
     excluded; a gap above "--log-cap" (800 by default). Without "--log-from", the log is not measured.
     The domain of a workstream entry is that of check 9 (pl, then prefix, then module), otherwise
     "outside any domain"; a decision log entry has no domain. One gap line per entry, in the order of
     the files (workstreams.yaml, then the log): "<domain>: workstream <id> weighs <o> bytes, cap <p>"
     ("outside any domain: workstream …"), "decision log: D<n> counts <c> characters, cap <p>". The count
     is "<n> open workstreams, <r> decision log entries, <k> above" (<n> the entries measured, <r> those
     of the log, <k> the gap lines); without "--log-from": "<n> open workstreams, decision log not
     measured, <k> above".

Output: one line per check (OK, GAP or warning, with a count), the details of
the gaps indented below, then a last line "LIVING DOCS · …".
Exit code: 0 with no gap, 1 with at least one gap, 2 for an invalid call
(missing argument, file or folder not found, "--root", "--checkpoint-cap", "--workstream-cap",
"--log-cap" or "--log-from" without "--domains", a cap or a number that is not a positive integer).

Python 3.11 and later, standard library only. The YAML reader is deliberately poor, like
the generator's: "- id:" then "key: value" on a single line; a value between double quotes
is read without the quotes and the escapes (\\" and \\\\), a bare value is read as it is,
conforming or not.
"""
import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

RE_NUMBER = re.compile(r"^\|\s*\*\*D(\d+)\*\*\s*\|")
RE_RESERVATION = re.compile(r"^\|\s*\*\*D(\d+)\*\*\s*\|\s*\*reserved")
RE_LOG = re.compile(r"^\|\s*`(v[^`]*)`\s*\|")
# the version token (check 4): the first occurrence, bounded by a non-alphanumeric character or the edge, of
# "[vV]?<n>.<n>[.<n>…]" or of "[vV]<n>"; "(?!\.?[^\W_])" prevents reading "1.2" in "1.2.3a"
RE_VERSION_TOKEN = re.compile(r"(?<![^\W_])(?:[vV]?[0-9]+(?:\.[0-9]+)+|[vV][0-9]+)(?!\.?[^\W_])")
RE_DATE = re.compile(rb"\d{2}/\d{2}/\d{4}")
# The strict YAML format of the values (check 11): see the docstring.
RE_QUOTED = re.compile(r'"((?:[^"\\]|\\["\\])*)"')
RE_ESCAPE = re.compile(r'\\(["\\])')
RE_COLON = re.compile(r":(?:\s|$)")
RE_COMMENT = re.compile(r"\s#")
RE_NON_PRINTABLE = re.compile(r"[\x00-\x08\x0b-\x1f\x7f-\x9f\u2028\u2029]")
FORBIDDEN_STARTS = "-?:,[]{}#&*!|>'\"%@`"

NOT_REQUESTED = "—  not requested"
OPEN_STATUSES = ("upcoming", "to-brief", "debt", "in-flight")
DEFAULT_CAP = 10240  # bytes: a checkpoint is re-read in full at every resumption
DEFAULT_WORKSTREAM_CAP = 1536  # bytes: a workstream entry (check 12)
DEFAULT_LOG_CAP = 800  # characters: a decision log entry (check 12)
NO_DOMAIN = "outside any domain"
CAP_OPTIONS = (("checkpoint_cap", "checkpoint-cap"), ("workstream_cap", "workstream-cap"),
               ("log_cap", "log-cap"), ("log_from", "log-from"))


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def analyse(text: str):
    """The useful lines of the text: (number, entry start, key, raw value); without ":", key and value are None."""
    started = False
    for number, line in enumerate(text.split("\n"), start=1):
        bare = line.strip()
        if not bare or bare.startswith("#"):
            continue
        start = bare.startswith("- ")
        if start:
            started, bare = True, bare[2:]
        if ":" not in bare or not started:
            yield number, start, None, None
            continue
        key, _, raw = bare.partition(":")
        yield number, start, key.strip(), raw


def read_value(raw: str) -> str:
    """The value of a line: without the double quotes and the escapes (\\" and \\\\) if it is between quotes, otherwise as it is."""
    value = raw.strip()
    quoted = RE_QUOTED.fullmatch(value)
    return RE_ESCAPE.sub(r"\1", quoted.group(1)) if quoted else value


def read_workstreams(path: Path) -> list[dict]:
    """The same reader as the generator; each entry keeps its source line (and its file)."""
    workstreams: list[dict] = []
    for number, start, key, raw in analyse(read_text(path)):
        if start:
            workstreams.append({"_line": number, "_file": path.name})
        if key is not None:
            workstreams[-1][key] = read_value(raw)
    return workstreams


def name(c: dict) -> str:
    return c.get("id") or f"(no id, line {c['_line']})"


def ranges(numbers: list[int]) -> list[str]:
    """['D320', 'D325 to D327 (3 numbers)'] from a sorted list."""
    out, i = [], 0
    while i < len(numbers):
        j = i
        while j + 1 < len(numbers) and numbers[j + 1] == numbers[j] + 1:
            j += 1
        if i == j:
            out.append(f"D{numbers[i]}")
        else:
            out.append(f"D{numbers[i]} to D{numbers[j]} ({j - i + 1} numbers)")
        i = j + 1
    return out


# Each check returns (verdict, count, details); verdict: OK, GAP or warning.

def check_numbers(log: Path):
    lines: dict[int, list[int]] = {}
    for position, line in enumerate(read_text(log).split("\n"), start=1):
        m = RE_NUMBER.match(line)
        if m:
            lines.setdefault(int(m.group(1)), []).append(position)
    total = sum(len(v) for v in lines.values())
    if not lines:
        return "GAP", "no number found", ['no line "| **D<n>** |" in the decision log']
    details = [f"D{n} duplicated (lines {', '.join(map(str, v))})"
               for n, v in sorted(lines.items()) if len(v) > 1]
    missing = [n for n in range(min(lines), max(lines) + 1) if n not in lines]
    details += [f"{p} missing" for p in ranges(missing)]
    count = f"{total} numbers, D{min(lines)} to D{max(lines)}"
    return ("GAP" if details else "OK"), count, details


def check_reservations(log: Path):
    found = []
    for position, line in enumerate(read_text(log).split("\n"), start=1):
        m = RE_RESERVATION.match(line)
        if m:
            found.append(f"D{m.group(1)} reserved (line {position})")
    if found:
        return "warning", f"{len(found)} reservation(s) pending", found
    return "OK", "no reservation pending", []


def check_ids(workstreams: list[dict], archives: list[dict] | None = None):
    seen: dict[str, list[int]] = {}
    for c in workstreams:
        if c.get("id"):
            seen.setdefault(c["id"], []).append(c["_line"])
    details = [f"id {i} duplicated (lines {', '.join(map(str, v))})"
               for i, v in seen.items() if len(v) > 1]
    count = f"{len(workstreams)} workstreams"
    if archives is not None:
        details += archive_gaps(seen, archives)
        count += f", {len(archives)} archived"
    return ("GAP" if details else "OK"), count, details


def archive_gaps(living: dict[str, list[int]], archives: list[dict]) -> list[str]:
    """The ids of workstreams.yaml also archived, then the ids present twice in the archives."""
    archives_by_id: dict[str, list[str]] = {}
    for c in archives:
        if c.get("id"):
            archives_by_id.setdefault(c["id"], []).append(f"{c['_file']}:{c['_line']}")
    details = [f"id {i} also archived ({places[0]})"
               for i, places in archives_by_id.items() if i in living]
    details += [f"id {i} duplicated in the archives ({', '.join(places)})"
                for i, places in archives_by_id.items() if len(places) > 1]
    return details


def numbers(version: str) -> tuple[int, ...]:
    """The sequence of numbers of the version token of a value: "v1.0065" -> (1, 65); "AC-V1.5.1" -> (1, 5, 1);
    "v1.10 (D205)" -> (1, 10); empty if the value carries none ("… 18a2957, no release (D188)")."""
    m = RE_VERSION_TOKEN.search(version)
    return tuple(int(n) for n in re.findall(r"[0-9]+", m.group(0))) if m else ()


def check_versions(workstreams: list[dict], archives: list[dict] | None = None):
    carried: dict[str, list[str]] = {}
    for c in workstreams:
        if c.get("version"):
            carried.setdefault(c["version"], []).append(name(c))
    details = [f"version {v} carried by {' and '.join(ids)}"
               for v, ids in carried.items() if len(ids) > 1]
    # (b) an entry in flight carries a version higher than every other one of the same deliverable
    everything = workstreams + (archives or [])
    for c in workstreams:
        if (c.get("status") != "in-flight" or not c.get("version") or not c.get("deliverable")
                or not numbers(c["version"])):
            continue
        others = [a for a in everything if a is not c and a.get("deliverable") == c["deliverable"]
                  and a.get("version") and numbers(a["version"])]
        if not others:
            continue
        highest = max(others, key=lambda a: numbers(a["version"]))
        if numbers(highest["version"]) >= numbers(c["version"]):
            details.append(f"{name(c)}: {c['version']} is not above {highest['version']} ({name(highest)})")
    return ("GAP" if details else "OK"), f"{len(carried)} versions", details


def check_in_flight(workstreams: list[dict]):
    in_flight = [c for c in workstreams if c.get("status") == "in-flight"]
    details = [f"{name(c)} (line {c['_line']}): pl missing or empty"
               for c in in_flight if not c.get("pl")]
    return ("GAP" if details else "OK"), f"{len(in_flight)} in flight", details


def text_gap(wanted: bytes, got: bytes):
    """None if the two texts are equal; otherwise (byte of the first difference, line)."""
    if wanted == got:
        return None
    offset = next((i for i, (a, b) in enumerate(zip(wanted, got)) if a != b), min(len(wanted), len(got)))
    return offset, wanted.count(b"\n", 0, offset) + 1


def check_board(workstreams: list[dict], workstreams_yaml: Path, board: Path, generator: Path):
    """The page and its data file (next to it, same name in .json) against their regeneration."""
    count = f"{len(workstreams)} workstreams"
    data = board.with_suffix(".json")
    with tempfile.TemporaryDirectory(prefix="living-docs-") as folder:
        # same name as the published page: the page carries the name of its data file
        output = Path(folder) / board.name
        data_output = output.with_suffix(".json")
        run = subprocess.run([sys.executable, "-B", str(generator.resolve()), str(workstreams_yaml.resolve()), str(output)],
                             capture_output=True, text=True, cwd=folder)
        if run.returncode != 0 or not output.is_file():
            message = (run.stderr.strip() or run.stdout.strip() or "no message").splitlines()[-1]
            return "GAP", count, [f"the generator failed (code {run.returncode}): {message}"]
        if not data_output.is_file():
            return "GAP", count, [f"the generator did not write the data file {data_output.name}"]
        published_page, regenerated_page = board.read_bytes(), output.read_bytes()
        regenerated_data = data_output.read_bytes()
        published_data = data.read_bytes() if data.is_file() else None
    details = []
    comparisons = [("the board page", published_page, regenerated_page)]
    if published_data is None:
        details.append(f"data file missing: {data}")
    else:
        comparisons.append(("the data file", published_data, regenerated_data))
    for file_name, raw, regenerated in comparisons:
        wanted, got = RE_DATE.sub(b"<date>", raw), RE_DATE.sub(b"<date>", regenerated)
        gap = text_gap(wanted, got)
        if gap:
            offset, line = gap
            details.append(f"{file_name} differs from its regeneration (dates masked): first difference at byte "
                           f"{offset} (line {line}); {len(wanted)} bytes against {len(got)} regenerated")
    if details:
        return "GAP", count, details
    return "OK", (f"{count}, page {len(published_page)} bytes and data {len(published_data)} bytes "
                  f"identical except the date"), []


def check_log(workstreams: list[dict], plan: Path):
    last = None
    for line in read_text(plan).split("\n"):
        m = RE_LOG.match(line)
        if m:
            last = m.group(1)
    if last is None:
        return "GAP", "no version", ['no line "| `v…` |" in the version log']
    carrying = [c for c in workstreams if last in c.get("id", "") or last in c.get("version", "")]
    accepted = [c for c in carrying if c.get("status") == "accepted"]
    if accepted:
        return "OK", f"last version {last}", []
    details = [f"{last}: no entry in status accepted carries this version"]
    details += [f"{name(c)} carries it but is in status {c.get('status') or 'empty'}" for c in carrying]
    return "GAP", f"last version {last}", details


def check_deliverables(workstreams: list[dict]):
    # field -> value -> ids of the entries in flight; one namespace per field
    spaces: dict[str, dict[str, list[str]]] = {"deliverable": {}, "resource": {}}
    for c in workstreams:
        for field, values in spaces.items():
            if c.get(field):
                values.setdefault(c[field], [])
                if c.get("status") == "in-flight":
                    values[c[field]].append(name(c))
    ids = {c["id"] for c in workstreams if c.get("id")}
    details = [f"{field} {value}: {len(in_flight)} batches in flight ({', '.join(in_flight)})"
               for field, values in spaces.items()
               for value, in_flight in values.items() if len(in_flight) > 1]
    waiting = [c for c in workstreams if c.get("waits")]
    details += [f"{name(c)} waits for {c['waits']}, which does not exist"
                for c in waiting if c["waits"] not in ids]
    details += [f"{name(c)} is in flight but waits for {c['waits']}"
                for c in waiting if c.get("status") == "in-flight"]
    in_flight = sum(1 for c in workstreams
                    if c.get("status") == "in-flight" and (c.get("deliverable") or c.get("resource")))
    count = (f"{len(spaces['deliverable'])} deliverables, {len(spaces['resource'])} resources, "
             f"{in_flight} in flight, {len(waiting)} waiting")
    return ("GAP" if details else "OK"), count, details


def values(entry: dict, key: str) -> list[str]:
    return entry.get(key, "").split()


def domain_of(c: dict, domains: list[dict]) -> str | None:
    """The first domain that fits, rule after rule: pl, then prefix, then module."""
    rules = (
        lambda d: bool(c.get("pl")) and c["pl"] == d.get("pl"),
        lambda d: any(c["id"].startswith(p) for p in values(d, "prefixes")),
        lambda d: bool(c.get("module")) and c["module"] in values(d, "modules"),
    )
    for rule in rules:
        for d in domains:
            if rule(d):
                return d["domain"]
    return None


def queue_section(text: str, title: str) -> str | None:
    """From the line that starts with the title to the next "##" line (excluded); None without a title."""
    lines = text.split("\n")
    start = next((i for i, line in enumerate(lines) if line.startswith(title)), None)
    if start is None:
        return None
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    return "\n".join(lines[start:end])


def closed_ids(workstreams: list[dict], archives: list[dict] | None) -> dict[str, str]:
    """The closed ids: accepted in workstreams.yaml, or only archived."""
    living = {c["id"] for c in workstreams if c.get("id")}
    closed = {c["id"]: "accepted" for c in workstreams if c.get("id") and c.get("status") == "accepted"}
    for c in archives or []:
        if c.get("id") and c["id"] not in living:
            closed.setdefault(c["id"], "archived")
    return closed


def citation(i: str) -> str:
    return f"`{i}`"


def check_domain(d: dict, workstreams: list[dict], closed: dict[str, str],
                 domains: list[dict], root: Path):
    """The table's faults, or: undeclared queue, queue that cites closed ones (9b), open ones not cited in the queue (9c)."""
    domain_name, path = d["domain"], root / d["checkpoint"]
    if not path.is_file():
        return [f"{domain_name}: checkpoint not found {d['checkpoint']}"], [], [], []
    try:
        text = read_text(path)
    except (OSError, UnicodeDecodeError):
        return [f"{domain_name}: checkpoint unreadable {d['checkpoint']}"], [], [], []
    title = d.get("queue", "")
    section = queue_section(text, title) if title else None
    if title and section is None:
        return [f"{domain_name}: queue section not found “{title}”"], [], [], []
    no_queue = [] if title else [f"{domain_name}: no queue section declared (queue: empty)"]
    zone = section if section is not None else text  # the citation is looked for in the queue; without one, in the whole checkpoint
    positions = sorted((section.find(citation(i)), i) for i in closed if citation(i) in section) if section else []
    cited = [f"{domain_name}: the queue cites {i}, closed ({closed[i]})" for _, i in positions]
    not_cited = [f"{domain_name}: {c['id']} ({c['status']}) is not cited in the checkpoint"
                 for c in workstreams
                 if c.get("id") and c.get("status") in OPEN_STATUSES and "for" not in c
                 and domain_of(c, domains) == domain_name and citation(c["id"]) not in zone]
    return [], no_queue, cited, not_cited


def check_checkpoints(workstreams: list[dict], archives: list[dict] | None, table: list[dict], root: Path):
    closed = closed_ids(workstreams, archives)
    valid = [d for d in table if d.get("domain") and d.get("checkpoint")]
    details, total_cited, total_not_cited, total_no_queue = [], 0, 0, 0
    for d in table:
        if d not in valid:
            details.append(f"entry on line {d['_line']}: domain or checkpoint missing")
            continue
        faults, no_queue, cited, not_cited = check_domain(d, workstreams, closed, valid, root)
        details += faults + no_queue + cited + not_cited
        total_cited += len(cited)
        total_not_cited += len(not_cited)
        total_no_queue += len(no_queue)
    count = (f"{len(table)} domains, {total_cited} cited closed, {total_not_cited} not cited, "
             f"{total_no_queue} without a queue section")
    return ("GAP" if details else "OK"), count, details


def checkpoint_size(path: Path) -> int | None:
    """The size in bytes of the file on disk; None if it is not found."""
    try:
        return path.stat().st_size if path.is_file() else None
    except OSError:
        return None


def check_size(table: list[dict], root: Path, cap: int):
    """A checkpoint strictly heavier than the cap is a gap; those not found are ignored."""
    valid = [d for d in table if d.get("domain") and d.get("checkpoint")]
    details = []
    for d in valid:
        size = checkpoint_size(root / d["checkpoint"])
        if size is not None and size > cap:
            details.append(f"{d['domain']}: {d['checkpoint']} weighs {size} bytes, cap {cap}")
    count = f"{len(valid)} domains, {len(details)} above {cap} bytes"
    return ("GAP" if details else "OK"), count, details


def entry_size(lines: list[str]) -> int:
    """The UTF-8 bytes of the lines of an entry, each followed by a line break, without the empty lines or the "#" ones."""
    return sum(len(line.encode("utf-8")) + 1 for line in lines if line.strip() and not line.strip().startswith("#"))


def check_entries(workstreams: list[dict], workstreams_text: str, log_text: str, table: list[dict],
                  workstream_cap: int, log_cap: int, log_from: int | None):
    """An open workstream entry (except "arbiter-") or a decision log entry above its cap is a gap."""
    valid = [d for d in table if d.get("domain") and d.get("checkpoint")]
    lines = workstreams_text.split("\n")
    details, measured = [], 0
    for rank, c in enumerate(workstreams):
        if c.get("status") not in OPEN_STATUSES or c.get("id", "").startswith("arbiter-"):
            continue
        measured += 1
        end = workstreams[rank + 1]["_line"] - 1 if rank + 1 < len(workstreams) else len(lines)
        size = entry_size(lines[c["_line"] - 1:end])
        if size > workstream_cap:
            domain = domain_of(c, valid) if c.get("id") else None
            details.append(f"{domain or NO_DOMAIN}: workstream {name(c)} weighs {size} bytes, cap {workstream_cap}")
    measured_log = 0
    if log_from is not None:
        for line in log_text.split("\n"):
            m = RE_NUMBER.match(line)
            if not m or int(m.group(1)) < log_from or RE_RESERVATION.match(line):
                continue
            measured_log += 1
            if len(line) > log_cap:
                details.append(f"decision log: D{m.group(1)} counts {len(line)} characters, cap {log_cap}")
    rest = f"{measured_log} decision log entries" if log_from is not None else "decision log not measured"
    count = f"{measured} open workstreams, {rest}, {len(details)} above"
    return ("GAP" if details else "OK"), count, details


def value_conforms(raw: str) -> bool:
    """A safe YAML scalar: empty, between double quotes, or bare and with nothing YAML would read otherwise."""
    value = raw.strip()
    if RE_NON_PRINTABLE.search(value):
        return False
    if not value or RE_QUOTED.fullmatch(value):
        return True
    return not (value[0] in FORBIDDEN_STARTS or "\t" in value
                or RE_COLON.search(value) or RE_COMMENT.search(value))


def line_count(text: str) -> int:
    return text.count("\n") + (0 if not text or text.endswith("\n") else 1)


def normalize_command(files: dict) -> str:
    """The command that normalizes the checked files, with the paths as given."""
    options = [f"--workstreams {files['workstreams']}"]
    options += [f"--{option} {files[option]}" for option in ("archives", "domains") if option in files]
    return "python3 -B archive_workstreams.py normalize " + " ".join(options)


def check_format(files: list[Path], command: str):
    """Every value of every file is a safe YAML scalar (see the docstring); the number of files and lines read."""
    lines, non_conforming = 0, []
    for path in files:
        text = read_text(path)
        lines += line_count(text)
        non_conforming += [f"{path}:{number} : key {key}" for number, _, key, raw in analyse(text)
                           if key is not None and not value_conforms(raw)]
    count = f"{len(files)} files, {lines} lines read"
    if not non_conforming:
        return "OK", count, []
    count = f"{len(non_conforming)} non-conforming value(s), {count}"
    return "GAP", count, non_conforming[:5] + [f"to normalize: {command}"]


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError(message.replace("expected one argument", "missing value"))


def archive_files(folder: Path) -> list[Path]:
    """The archives of the folder, in file-name order."""
    return sorted(p for p in folder.glob("WORKSTREAMS_*.yaml") if p.is_file())


def read_archives(folder: Path) -> list[dict]:
    """The entries of every archive in the folder, in file-name order."""
    archives: list[dict] = []
    for file in archive_files(folder):
        archives += read_workstreams(file)
    return archives


def read_arguments(argv: list[str]):
    p = Parser(prog="check_living_docs.py", allow_abbrev=False, add_help=False)
    for option in ("workstreams", "log", "board", "generator", "plan", "archives", "domains", "root"):
        p.add_argument(f"--{option}")
    for _, option in CAP_OPTIONS:
        p.add_argument(f"--{option}")
    a, unknown = p.parse_known_args(argv)
    if unknown:
        raise ValueError(f"unknown argument: {unknown[0]}")
    for option in ("workstreams", "log"):
        if not getattr(a, option):
            raise ValueError(f"missing argument: --{option}")
    if bool(a.board) != bool(a.generator):
        raise ValueError("--board and --generator go together")
    if a.root and not a.domains:
        raise ValueError("--root only goes with --domains")
    caps = {"checkpoint_cap": DEFAULT_CAP, "workstream_cap": DEFAULT_WORKSTREAM_CAP,
            "log_cap": DEFAULT_LOG_CAP, "log_from": None}
    for attribute, option in CAP_OPTIONS:
        value = getattr(a, attribute)
        if value is None:
            continue
        if not a.domains:
            raise ValueError(f"--{option} only goes with --domains")
        if not re.fullmatch(r"[0-9]+", value) or int(value) < 1:
            raise ValueError(f"--{option}: a positive integer is expected ({value})")
        caps[attribute] = int(value)
    paths = {option: Path(getattr(a, option)) for option in
             ("workstreams", "log", "board", "generator", "plan", "archives", "domains", "root") if getattr(a, option)}
    for option, path in paths.items():
        if not (path.is_dir() if option in ("archives", "root") else path.is_file()):
            raise ValueError(f"file not found: --{option} {path}")
    return paths, caps


def main(argv: list[str]) -> int:
    try:
        f, caps = read_arguments(argv)
        workstreams = read_workstreams(f["workstreams"])
        archives = read_archives(f["archives"]) if "archives" in f else None
        table = read_workstreams(f["domains"]) if "domains" in f else None
        for option in ("log", "plan"):  # trial read: an unreadable file is an invalid call
            if option in f:
                read_text(f[option])
    except (ValueError, OSError, UnicodeDecodeError) as error:
        print(f"check_living_docs: {' '.join(str(error).split())}", file=sys.stderr)
        return 2

    checks = [
        ("decision numbers", lambda: check_numbers(f["log"])),
        ("reservations", lambda: check_reservations(f["log"])),
        ("workstream ids", lambda: check_ids(workstreams, archives)),
        ("batch versions", lambda: check_versions(workstreams, archives)),
        ("workstreams in flight", lambda: check_in_flight(workstreams)),
        ("board", (lambda: check_board(workstreams, f["workstreams"], f["board"], f["generator"]))
         if "board" in f else None),
        ("version log", (lambda: check_log(workstreams + (archives or []), f["plan"])) if "plan" in f else None),
        ("deliverables and resources", lambda: check_deliverables(workstreams)),
        ("checkpoints", (lambda: check_checkpoints(workstreams, archives, table, f.get("root", Path("."))))
         if table is not None else None),
        ("checkpoint size", (lambda: check_size(table, f.get("root", Path(".")), caps["checkpoint_cap"]))
         if table is not None else None),
        ("YAML format", lambda: check_format(
            [f["workstreams"]] + (archive_files(f["archives"]) if "archives" in f else [])
            + ([f["domains"]] if "domains" in f else []), normalize_command(f))),
        ("entry sizes", (lambda: check_entries(
            workstreams, read_text(f["workstreams"]), read_text(f["log"]), table, caps["workstream_cap"],
            caps["log_cap"], caps["log_from"])) if table is not None else None),
    ]
    gaps = 0
    for rank, (label, check) in enumerate(checks, start=1):
        if check is None:
            print(f"{rank:<2} {label:<26} {NOT_REQUESTED}")
            continue
        verdict, count, details = check()
        gaps += verdict == "GAP"
        print(f"{rank:<2} {label:<26} {verdict:<13}  {count}")
        for detail in details:
            print(f"      {detail}")
    print("LIVING DOCS · no gap" if not gaps else f"LIVING DOCS · {gaps} gap(s)")
    return 1 if gaps else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
