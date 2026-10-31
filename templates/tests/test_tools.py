"""Common helpers for the tests of the living-docs scripts.

The three scripts (check_living_docs.py, archive_workstreams.py, make_board.py) are always run by
a path computed from this file, never from the current folder; every test builds its fixtures in
a temporary folder, from short, neutral texts.

Run from the repository root:
    python3 -m unittest discover -s en/templates/tests -t .
"""
import importlib.util
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TEMPLATES = Path(__file__).resolve().parent.parent
CHECKER = TEMPLATES / "check_living_docs.py"
ARCHIVER = TEMPLATES / "archive_workstreams.py"
GENERATOR = TEMPLATES / "make_board.py"

GAP = "GAP"
WARNING = "warning"
NOT_REQUESTED = "not requested"


def load(path: Path, name: str):
    """Imports a script by its path, to call its functions (it does not run: __main__ guard)."""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def block(id: str, **keys) -> str:
    """An entry: "- id: …" then one key per line; _ becomes - in the key name; None: key omitted."""
    lines = [f"- id: {id}"]
    lines += [f"  {key.replace('_', '-')}: {value}" for key, value in keys.items() if value is not None]
    return "\n".join(lines)


def yaml(*blocks: str, header: str = "# Workstreams — Test") -> str:
    """A workstreams.yaml: the header, then the blocks separated by an empty line."""
    return header + "\n\n" + "\n\n".join(blocks) + "\n"


def decision_log(*numbers: int) -> str:
    """A decision log: a title, then a line "| **D<n>** | … |" per number given (in the order given)."""
    return "# Decision log\n" + "".join(f"| **D{n}** | decision {n} |\n" for n in numbers)


def read_output(text: str):
    """The checker's output: ({rank: (verdict, count, [details])}, last line)."""
    checks, last = {}, None
    for line in text.split("\n"):
        if not line.strip():
            continue
        if line.startswith("      ") and last is not None:
            checks[last][2].append(line.strip())
            continue
        m = re.match(rf"^(\d+)\s+(.+?)\s+({GAP}|{WARNING}|OK)\s+(.*)$", line)
        if m:
            last = int(m.group(1))
            checks[last] = (m.group(3), m.group(4), [])
            continue
        m = re.match(rf"^(\d+)\s+(.+?)\s+—\s+{NOT_REQUESTED}$", line)
        if m:
            last = int(m.group(1))
            checks[last] = (NOT_REQUESTED, "", [])
            continue
        last = None
        checks.setdefault("summary", line)
    return checks


class Output:
    """The result of a command-line call."""

    def __init__(self, process: subprocess.CompletedProcess):
        self.code = process.returncode
        self.stdout = process.stdout
        self.stderr = process.stderr
        self.checks = read_output(self.stdout)

    def verdict(self, rank: int) -> str:
        return self.checks[rank][0]

    def count(self, rank: int) -> str:
        return self.checks[rank][1]

    def details(self, rank: int) -> list:
        return self.checks[rank][2]

    @property
    def summary(self) -> str:
        return self.checks.get("summary", "")


class TempCase(unittest.TestCase):
    """A temporary folder per test, file writing and the call of the scripts."""

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="living-docs-test-")
        self.addCleanup(temporary.cleanup)
        self.folder = Path(temporary.name)

    # Failure messages stay short when the container is a whole page.
    def assertIn(self, member, container, msg=None):
        if isinstance(container, str) and len(container) > 2000:
            if member not in container:
                self.fail(msg or f"not in the text ({len(container)} characters): {member!r}")
        else:
            super().assertIn(member, container, msg)

    def assertNotIn(self, member, container, msg=None):
        if isinstance(container, str) and len(container) > 2000:
            if member in container:
                self.fail(msg or f"found in the text ({len(container)} characters): {member!r}")
        else:
            super().assertNotIn(member, container, msg)

    def write(self, name: str, text, binary: bool = False) -> Path:
        path = self.folder / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if binary:
            path.write_bytes(text)
        else:
            path.write_bytes(text.encode("utf-8"))
        return path

    def subfolder(self, name: str) -> Path:
        path = self.folder / name
        path.mkdir(parents=True, exist_ok=True)
        return path

    def run_script(self, script: Path, *arguments, cwd=None) -> Output:
        """Runs the script with the same Python; the current folder is the temporary folder by default."""
        environment = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1"}
        process = subprocess.run(
            [sys.executable, "-B", str(script), *map(str, arguments)],
            capture_output=True, text=True, encoding="utf-8",
            cwd=str(cwd or self.folder), env=environment)
        return Output(process)
