"""Tests of arbiter.py: a run of the arbiter on a temporary git repository, and the workflow template.

Every test builds a git repository (git init, commits dated by GIT_COMMITTER_DATE) with minimal living docs, copies
the scripts into it (arbiter.py, the checker, the archiver, the generator) and runs arbiter.py with "--date", so that
the hours are counted without depending on the clock.
"""
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from .test_tools import (ARCHIVER, CHECKER, GENERATOR, NO_PYYAML, TEMPLATES, TempCase, block, decision_log, load,
                         pyyaml, pyyaml_reading, without_position, yaml)

ARBITER = TEMPLATES / "arbiter.py"
WORKFLOW = TEMPLATES / "living-docs-repo" / "arbiter.yml"

RUN = "2026-03-15 06:43"            # the Paris time of the run
BASE = "2026-03-01T10:00:00+0100"   # the base commit
LOG_HEADER = "# Arbiter's log\n\n"

TABLE = """# Domains
- domain: alpha
  pl: Opus-PL-Alpha
  checkpoint: Alpha/CHECKPOINT_ALPHA.md
  queue: "## The queue"
  modules: module-a
  prefixes: alpha-

- domain: beta
  pl: Opus-PL-Beta
  checkpoint: Beta/CHECKPOINT_BETA.md
  queue: "## The queue"
  modules: module-b

- domain: coordination
  pl: Opus-Coordination
  checkpoint: Method/CHECKPOINT_METHOD.md
  queue: "## The queue"
  modules: method
"""

CHECKPOINTS = {
    "alpha": "Alpha/CHECKPOINT_ALPHA.md",
    "beta": "Beta/CHECKPOINT_BETA.md",
    "coordination": "Method/CHECKPOINT_METHOD.md",
}
FREE = "Session active: none — free since 1 March"


def checkpoint(*cited: str, baton: str = FREE, padding: int = 0) -> str:
    """A checkpoint: the baton, then a "The queue" section that cites the given ids; "padding" more bytes."""
    queue = "".join(f"- `{i}` to do\n" for i in cited)
    text = f"# Checkpoint\n\n{baton}\n\n## The queue\n{queue}## History\nNothing.\n"
    return text + ("x" * padding + "\n" if padding else "")


def entries(text: str) -> list[dict]:
    """The entries of a workstreams.yaml, read the way the scripts read them."""
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "workstreams.yaml"
        path.write_bytes(text.encode("utf-8"))
        return without_position(load(CHECKER, "check_living_docs_test").read_workstreams(path))


class ArbiterCase(TempCase):
    """A git repository of compliant living docs; each test changes one piece, then runs the arbiter."""

    def setUp(self):
        super().setUp()
        self.repo = self.subfolder("repo")
        self.git("init", "-q", "-b", "main")
        for script in (ARBITER, CHECKER, ARCHIVER, GENERATOR):
            self.write(f"repo/Method/{script.name}", script.read_text(encoding="utf-8"))
        self.write("repo/Method/domains.yaml", TABLE)
        self.write("repo/Method/ARBITER_LOG.md", LOG_HEADER)
        self.write("repo/Method/METHOD.md", "# Method\n")
        self.write("repo/Folder/decision_log.md", decision_log(1, 2, 3))
        os.makedirs(self.repo / "Folder" / "Archives")
        self.write("repo/Folder/Archives/.keep", "")
        self.compliant_workstreams()
        for domain, path in CHECKPOINTS.items():
            self.write(f"repo/{path}", checkpoint(*self.cited.get(domain, ())))
        self.commit()

    cited = {"alpha": ("alpha-1",), "beta": ("beta-1",)}

    def compliant_workstreams(self):
        self.write_workstreams(block("alpha-1", title="First", status="upcoming", module="module-a"),
                               block("beta-1", title="Other", status="upcoming", module="module-b"))

    # ── the repository ──

    def git(self, *arguments, when: str | None = None):
        environment = {**os.environ, "GIT_AUTHOR_NAME": "Test", "GIT_AUTHOR_EMAIL": "test@example.org",
                       "GIT_COMMITTER_NAME": "Test", "GIT_COMMITTER_EMAIL": "test@example.org"}
        if when:
            environment.update(GIT_COMMITTER_DATE=when, GIT_AUTHOR_DATE=when)
        process = subprocess.run(["git", *arguments], cwd=self.repo, env=environment, capture_output=True,
                                 text=True, encoding="utf-8")
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
        return process.stdout

    def commit(self, message: str = "base", when: str = BASE, board: bool = True):
        """Regenerates the board (unless "board=False"), then a dated commit."""
        if board:
            output = self.run_script(GENERATOR, "Folder/workstreams.yaml", "Folder/workstreams.html", cwd=self.repo)
            self.assertEqual(output.code, 0, output.stdout + output.stderr)
        self.git("add", "-A")
        self.git("commit", "-q", "--allow-empty", "-m", message, when=when)

    def write_workstreams(self, *blocks: str, header: str = "# Workstreams — Test") -> str:
        text = yaml(*blocks, header=header)
        self.write("repo/Folder/workstreams.yaml", text)
        return text

    def read(self, path: str) -> str:
        return (self.repo / path).read_bytes().decode("utf-8")

    def workstreams(self) -> list[dict]:
        return entries(self.read("Folder/workstreams.yaml"))

    def by_id(self) -> dict:
        return {c["id"]: c for c in self.workstreams()}

    def arbiter_ids(self) -> list[str]:
        return [c["id"] for c in self.workstreams() if c["id"].startswith("arbiter-")]

    def log_lines(self) -> list[str]:
        return [line for line in self.read("Method/ARBITER_LOG.md").split("\n") if line.startswith("- ")]

    def modified(self) -> list[str]:
        return sorted(line[3:] for line in self.git("status", "--short").split("\n") if line)

    # ── the arbiter ──

    def options(self, method: bool = True, sheet: bool = False) -> list[str]:
        options = ["--workstreams", "Folder/workstreams.yaml", "--log", "Folder/decision_log.md",
                   "--archives", "Folder/Archives", "--domains", "Method/domains.yaml",
                   "--arbiter-log", "Method/ARBITER_LOG.md",
                   "--board", "Folder/workstreams.html", "--generator", "Method/make_board.py"]
        if method:
            options += ["--method", "Method/METHOD.md"]
        if sheet:
            options += ["--sheet", "Alpha/CHECKPOINT_ALPHA.md"]
        return options

    def arbitrate(self, *extra, date: str | None = RUN, options: list | None = None):
        arguments = self.options() if options is None else options
        if date:
            arguments = [*arguments, "--date", date]
        return self.run_script(self.repo / "Method" / "arbiter.py", *arguments, *extra, cwd=self.repo)

    def verifications(self):
        return ["--workstreams", "Folder/workstreams.yaml", "--log", "Folder/decision_log.md",
                "--archives", "Folder/Archives", "--domains", "Method/domains.yaml",
                "--board", "Folder/workstreams.html", "--generator", "Method/make_board.py"]

    def run_commit(self, output) -> str:
        m = re.search(r"^Commit: (.*)$", output.stdout, re.M)
        self.assertTrue(m, output.stdout)
        return m.group(1)


class TestCompliant(ArbiterCase):
    def test_compliant_living_docs_return_0_and_write_only_the_log(self):
        before = {c: self.read(c) for c in ("Folder/workstreams.yaml", "Folder/workstreams.html", "Folder/workstreams.json")}
        output = self.arbitrate()
        self.assertEqual(output.code, 0, output.stdout + output.stderr)
        self.assertEqual(self.modified(), ["Method/ARBITER_LOG.md"])
        self.assertEqual({c: self.read(c) for c in before}, before, "workstreams and board are not touched")
        self.assertEqual(len(self.log_lines()), 1)
        self.assertRegex(self.log_lines()[0],
                         r"^- 2026-03-15 06:43 · 0 gaps · 0 new findings · batons fresh · "
                         r"archiving: 0 dated, 0 archived · checkpoints: up to date · footprint: \d+ KB$")
        self.assertTrue(self.read("Method/ARBITER_LOG.md").startswith(LOG_HEADER), "nothing is rewritten")
        self.assertIn("Living docs compliant on 2026-03-15", output.stdout)
        self.assertEqual(self.run_commit(output), "Arbiter 2026-03-15: living docs compliant")

    def test_the_log_line_is_appended_at_the_end_without_rewriting_the_previous_ones(self):
        self.arbitrate(date="2026-03-15 06:43")
        first = self.log_lines()[0]
        self.arbitrate(date="2026-03-16 06:43")
        lines = self.log_lines()
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0], first)
        self.assertTrue(lines[1].startswith("- 2026-03-16 06:43 · 0 gaps"))

    def test_a_log_without_a_final_newline_gets_its_line_on_a_new_line(self):
        self.write("repo/Method/ARBITER_LOG.md", "# Log\n- 2026-03-14 06:43 · 0 gaps")
        self.commit("log without a final newline")
        self.arbitrate()
        lines = self.read("Method/ARBITER_LOG.md").split("\n")
        self.assertEqual(lines[1], "- 2026-03-14 06:43 · 0 gaps")
        self.assertTrue(lines[2].startswith("- 2026-03-15 06:43"))

    def test_the_default_date_is_the_time_in_paris(self):
        output = self.arbitrate(date=None)
        self.assertEqual(output.code, 0, output.stderr)
        self.assertRegex(self.log_lines()[0], r"^- \d{4}-\d{2}-\d{2} \d{2}:\d{2} · 0 gaps")

    def test_no_bytecode_is_written_in_the_repository(self):
        self.arbitrate()
        self.assertEqual([p for p in self.repo.rglob("__pycache__")], [])


class TestNewGap(ArbiterCase):
    cited = {"alpha": ("alpha-1", "alpha-2"), "beta": ("beta-1",)}

    def compliant_workstreams(self):
        self.write_workstreams(
            block("alpha-1", title="First", status="upcoming", module="module-a"),
            block("alpha-2", title="Second", status="in-flight", module="module-a"),  # in flight without pl: check 5
            block("beta-1", title="Other", status="upcoming", module="module-b"))

    def test_a_new_gap_makes_a_workstream_of_the_right_shape_and_returns_1(self):
        before = self.read("Folder/workstreams.yaml")
        output = self.arbitrate()
        self.assertEqual(output.code, 1, output.stdout + output.stderr)
        line = next(i for i, text in enumerate(before.split("\n"), start=1) if text == "- id: alpha-2")
        expected = (
            "\n- id: arbiter-c5-alpha-2\n"
            f"  title: \"Check 5: alpha-2 (line {line}): pl missing or empty\"\n"
            "  module: module-a\n"
            "  category: doc\n"
            "  status: to-brief\n"
            "  for: Opus-PL-Alpha\n"
            "  priority: medium\n"
            "  complexity: low\n"
            "  cost: none; a correction in the living docs\n"
            "  basis: \"Reported by the arbiter on 15 March 2026 (check 5). "
            f"alpha-2 (line {line}): pl missing or empty. Fill in the pl: of the workstream in flight.\"\n"
            "  refs: Method/ARBITER.md\n")
        self.assertEqual(self.read("Folder/workstreams.yaml"), before + expected)
        self.assertEqual(self.run_commit(output), "Arbiter 2026-03-15: 1 finding(s)")
        self.assertIn("New findings (1):\n  - arbiter-c5-alpha-2 · for Opus-PL-Alpha", output.stdout)
        self.assertRegex(self.log_lines()[0], r"^- 2026-03-15 06:43 · 1 gap · 1 new finding · ")

    def test_the_board_is_regenerated_then_check_6_is_ok(self):
        self.arbitrate()
        # the page is fixed: only the data changes
        self.assertEqual(self.modified(), ["Folder/workstreams.json", "Folder/workstreams.yaml", "Method/ARBITER_LOG.md"])
        self.assertIn("arbiter-c5-alpha-2", self.read("Folder/workstreams.json"))
        check = self.run_script(self.repo / "Method" / "check_living_docs.py", *self.verifications(), cwd=self.repo)
        self.assertEqual(check.verdict(6), "OK", check.stdout)

    def test_the_same_gap_at_the_next_run_makes_no_duplicate(self):
        self.arbitrate()
        after_the_first = self.read("Folder/workstreams.yaml")
        output = self.arbitrate(date="2026-03-16 06:43")
        self.assertEqual(output.code, 0, output.stdout + output.stderr)
        self.assertEqual(self.read("Folder/workstreams.yaml"), after_the_first)
        self.assertEqual(self.arbiter_ids(), ["arbiter-c5-alpha-2"])
        self.assertIn("Reported before and still there (1):\n  - arbiter-c5-alpha-2 · for Opus-PL-Alpha", output.stdout)
        self.assertRegex(self.log_lines()[1], r"^- 2026-03-16 06:43 · 1 gap · 0 new findings · ")
        self.assertEqual(self.run_commit(output), "Arbiter 2026-03-16: 0 finding(s)")

    def test_an_accepted_workstream_still_covers_the_case(self):
        self.arbitrate()
        text = self.read("Folder/workstreams.yaml").replace(
            "  status: to-brief\n  for: Opus-PL-Alpha", "  status: accepted\n  for: Opus-PL-Alpha")
        self.write("repo/Folder/workstreams.yaml", text)
        self.commit("the PL accepts the finding")
        output = self.arbitrate(date="2026-03-16 06:43")
        self.assertEqual(output.code, 0, output.stdout)
        self.assertEqual(self.arbiter_ids(), ["arbiter-c5-alpha-2"])

    def test_an_archived_id_is_not_reused_the_date_is_added(self):
        self.arbitrate()
        entry = [b for b in self.read("Folder/workstreams.yaml").split("\n\n") if b.startswith("- id: arbiter-c5-alpha-2")][0]
        self.write("repo/Folder/workstreams.yaml", self.read("Folder/workstreams.yaml").replace("\n\n" + entry, "\n"))
        self.write("repo/Folder/Archives/WORKSTREAMS_2026-03.yaml",
                   "# Archived workstreams — March 2026\n\n" + entry.replace("to-brief", "accepted"))
        self.commit("the finding is archived, the case comes back")
        output = self.arbitrate(date="2026-03-20 06:43")
        self.assertEqual(output.code, 1, output.stdout + output.stderr)
        self.assertEqual(self.arbiter_ids(), ["arbiter-c5-alpha-2-20260320"])
        check = self.run_script(self.repo / "Method" / "check_living_docs.py", *self.verifications(), cwd=self.repo)
        self.assertEqual(check.verdict(3), "OK", check.stdout)

    @NO_PYYAML
    def test_the_workstreams_written_read_the_same_by_a_standard_yaml_parser(self):
        self.arbitrate()
        text = self.read("Folder/workstreams.yaml")
        self.assertEqual(pyyaml_reading(text), self.workstreams())


class TestAddressees(ArbiterCase):
    def compliant_workstreams(self):
        self.write_workstreams(
            block("alpha-1", title="First", status="upcoming", module="module-a"),
            block("beta-1", title="Other", status="upcoming", module="module-b"),
            block("beta-2", title="In flight", status="in-flight", module="module-b", pl="Opus-PL-Other"),
            block("orphan-1", title="No domain", status="in-flight", module="module-z", version="v1"),
            block("orphan-2", title="No domain either", status="upcoming", module="module-z", version="v1"))

    cited = {"alpha": ("alpha-1",), "beta": ("beta-1", "beta-2")}

    def test_a_workstream_in_flight_goes_to_the_pl_it_carries_a_module_without_pl_to_the_coordinator(self):
        output = self.arbitrate()
        self.assertEqual(output.code, 1, output.stdout + output.stderr)
        arbiter = self.by_id()
        # orphan-1: in flight without pl, and no domain; orphan-2 carries the same version
        self.assertEqual(arbiter["arbiter-c5-orphan-1"]["for"], "Opus-Coordination")
        self.assertEqual(arbiter["arbiter-c5-orphan-1"]["module"], "module-z")
        self.assertEqual(arbiter["arbiter-c4-orphan-1"]["for"], "Opus-Coordination")

    def test_the_log_the_board_and_the_plan_go_to_the_coordinator(self):
        self.write("repo/Folder/decision_log.md", decision_log(1, 3))
        self.write("repo/Folder/workstreams.html", "<html>stale</html>")
        self.commit("decision log with a hole, stale board", board=False)
        output = self.arbitrate()
        self.assertEqual(output.code, 1, output.stdout)
        arbiter = self.by_id()
        for i in ("arbiter-c1-D2", "arbiter-c6-board"):
            self.assertEqual(arbiter[i]["for"], "Opus-Coordination", i)
            self.assertEqual(arbiter[i]["module"], "method", i)
        self.assertIn("D2 missing", arbiter["arbiter-c1-D2"]["basis"])
        self.assertIn("the board page differs", arbiter["arbiter-c6-board"]["basis"])
        self.assertNotIn("arbiter-c6-board-2", arbiter)

    def test_two_batches_in_flight_on_one_resource_one_workstream_each_to_its_pl(self):
        self.write_workstreams(
            block("alpha-1", title="First", status="in-flight", module="module-a", pl="Opus-PL-Alpha", resource="machine"),
            block("beta-1", title="Other", status="in-flight", module="module-b", pl="Opus-PL-Beta", resource="machine"))
        self.commit("two batches on the machine")
        output = self.arbitrate()
        self.assertEqual(output.code, 1, output.stdout)
        arbiter = self.by_id()
        self.assertEqual(arbiter["arbiter-c8-alpha-1"]["for"], "Opus-PL-Alpha")
        self.assertEqual(arbiter["arbiter-c8-beta-1"]["for"], "Opus-PL-Beta")
        self.assertEqual(arbiter["arbiter-c8-beta-1"]["module"], "module-b")
        self.assertIn("resource machine: 2 batches in flight (alpha-1, beta-1)", arbiter["arbiter-c8-beta-1"]["basis"])

    def test_a_batch_in_flight_that_carries_a_pl_foreign_to_the_table_goes_to_that_pl(self):
        self.write_workstreams(
            block("alpha-1", title="First", status="in-flight", module="module-a", pl="Opus-PL-Other", deliverable="repo"),
            block("alpha-2", title="Second", status="in-flight", module="module-a", pl="Opus-PL-Alpha", deliverable="repo"),
            block("beta-1", title="Other", status="upcoming", module="module-b"))
        self.commit("two batches on one deliverable")
        self.assertEqual(self.arbitrate().code, 1)
        arbiter = self.by_id()
        self.assertEqual(arbiter["arbiter-c8-alpha-1"]["for"], "Opus-PL-Other")
        self.assertEqual(arbiter["arbiter-c8-alpha-2"]["for"], "Opus-PL-Alpha")

    def test_a_batch_in_flight_below_the_highest_version_of_its_deliverable_goes_to_its_pl(self):
        # check 4 (b): the key and the workstream at issue are the id at the head of the line
        self.write_workstreams(
            block("alpha-1", title="First", status="upcoming", module="module-a", deliverable="repo", version="v1.2"),
            block("alpha-2", title="Second", status="in-flight", module="module-a", pl="Opus-PL-Alpha", deliverable="repo",
                  version="v1.1"),
            block("beta-1", title="Other", status="upcoming", module="module-b"))
        self.commit("a batch in flight below the highest version")
        self.assertEqual(self.arbitrate().code, 1)
        arbiter = self.by_id()
        self.assertNotIn("arbiter-c4-alpha-1", arbiter)
        self.assertEqual(arbiter["arbiter-c4-alpha-2"]["for"], "Opus-PL-Alpha")
        self.assertEqual(arbiter["arbiter-c4-alpha-2"]["module"], "module-a")
        self.assertIn("alpha-2: v1.1 is not above v1.2 (alpha-1)", arbiter["arbiter-c4-alpha-2"]["basis"])
        self.assertIn("a batch in flight goes above the highest version of its deliverable",
                      arbiter["arbiter-c4-alpha-2"]["basis"])

    def test_both_forms_of_check_4_give_the_id_at_issue(self):
        arbiter = load(ARBITER, "arbiter_under_test")

        class Ctx:
            by_id = {"agent-server-trial": {"id": "agent-server-trial"}, "alpha-1": {"id": "alpha-1"}}

        cases = arbiter.cases_of_check(
            4, "trial-back: agent-v0.1.0 is not above agent-v0.1.1 (agent-server-trial)", Ctx)
        self.assertEqual(cases, [("trial-back", None)])
        cases = arbiter.cases_of_check(
            4, "agent-server-trial: agent-v0.1.0 is not above agent-v0.1.1 (alpha-1)", Ctx)
        self.assertEqual(cases, [("agent-server-trial", {"id": "agent-server-trial"})])
        cases = arbiter.cases_of_check(4, "version v1 carried by alpha-1 and beta-2", Ctx)
        self.assertEqual(cases, [("alpha-1", {"id": "alpha-1"})])

    def test_gap_b_of_check_4_is_read_even_if_the_version_contains_a_space(self):
        arbiter = load(ARBITER, "arbiter_under_test")

        class Ctx:
            by_id = {"co-x": {"id": "co-x"}, "co-y": {"id": "co-y"}}

        cases = arbiter.cases_of_check(4, "co-x: v1.2 (R205) is not above v1.3 (co-y)", Ctx)
        self.assertEqual(cases, [("co-x", {"id": "co-x"})])

    def test_the_coordinator_is_read_in_the_domain_table(self):
        table = TABLE.replace("Opus-Coordination", "Opus-Coordination-Other")
        self.write("repo/Method/domains.yaml", table)
        self.commit("another coordinator name")
        self.arbitrate()
        self.assertEqual(self.by_id()["arbiter-c5-orphan-1"]["for"], "Opus-Coordination-Other")

    def test_a_coordinator_entry_may_say_coordinator(self):
        table = TABLE.replace("Opus-Coordination", "Opus-Coordinator")
        self.write("repo/Method/domains.yaml", table)
        self.commit("the coordinator is called Coordinator")
        self.arbitrate()
        self.assertEqual(self.by_id()["arbiter-c5-orphan-1"]["for"], "Opus-Coordinator")

    def test_without_a_coordination_entry_the_script_exits_with_code_2_and_writes_only_the_log(self):
        table = TABLE.replace("Opus-Coordination", "Opus-Other")
        self.write("repo/Method/domains.yaml", table)
        self.commit("no coordinator any more")
        before = self.read("Folder/workstreams.yaml")
        output = self.arbitrate()
        self.assertEqual(output.code, 2)
        self.assertIn("no Coordination entry", output.stderr)
        self.assertEqual(self.read("Folder/workstreams.yaml"), before)
        self.assertEqual(self.modified(), ["Method/ARBITER_LOG.md"])
        self.assertRegex(self.log_lines()[0], r"^- 2026-03-15 06:43 · check impossible: Method/domains\.yaml$")


class TestCheck9Grouped(ArbiterCase):
    cited = {"alpha": (), "beta": ("beta-1",)}

    def compliant_workstreams(self):
        self.write_workstreams(
            block("alpha-1", title="First", status="upcoming", module="module-a"),
            block("alpha-2", title="Second", status="debt", module="module-a"),
            block("alpha-3", title="Third", status="to-brief", module="module-a"),
            block("beta-1", title="Other", status="upcoming", module="module-b"),
            block("beta-2", title="Other again", status="upcoming", module="module-b"))

    def test_check_9_makes_one_workstream_per_domain_not_one_per_line(self):
        output = self.arbitrate()
        self.assertEqual(output.code, 1, output.stdout + output.stderr)
        self.assertEqual(self.arbiter_ids(), ["arbiter-c9-checkpoint-alpha-20260315", "arbiter-c9-checkpoint-beta-20260315"])
        alpha = self.by_id()["arbiter-c9-checkpoint-alpha-20260315"]
        self.assertEqual((alpha["for"], alpha["module"]), ("Opus-PL-Alpha", "method"))
        self.assertEqual(alpha["title"], "The alpha checkpoint lags behind its workstreams")
        self.assertEqual(alpha["basis"], (
            "Reported by the arbiter on 15 March 2026 (check 9). "
            "alpha: alpha-1 (upcoming) is not cited in the checkpoint; alpha: alpha-2 (debt) is not cited in the "
            "checkpoint; alpha: alpha-3 (to-brief) is not cited in the checkpoint. "
            "Cite every open workstream of your domain by its id in your checkpoint, remove the closed "
            "workstreams from your queue (method §6)."))
        beta = self.by_id()["arbiter-c9-checkpoint-beta-20260315"]
        self.assertEqual(beta["for"], "Opus-PL-Beta")
        self.assertIn("beta: beta-2 (upcoming) is not cited in the checkpoint", beta["basis"])
        self.assertRegex(self.log_lines()[0], r"· 1 gap · 2 new findings · batons fresh · .*"
                                              r"· checkpoints: alpha, beta · footprint")

    def test_an_open_workstream_of_the_domain_prevents_a_new_filing_even_another_day(self):
        self.arbitrate()
        after = self.read("Folder/workstreams.yaml")
        output = self.arbitrate(date="2026-03-17 06:43")
        self.assertEqual(output.code, 0, output.stdout)
        self.assertEqual(self.read("Folder/workstreams.yaml"), after)
        self.assertEqual(self.arbiter_ids(), ["arbiter-c9-checkpoint-alpha-20260315", "arbiter-c9-checkpoint-beta-20260315"])

    def test_an_accepted_workstream_no_longer_covers_the_domain(self):
        self.arbitrate()
        text = self.read("Folder/workstreams.yaml").replace(
            "  status: to-brief\n  for: Opus-PL-Alpha", "  status: accepted\n  for: Opus-PL-Alpha")
        self.write("repo/Folder/workstreams.yaml", text)
        self.commit("alpha's PL accepts its finding")
        output = self.arbitrate(date="2026-03-17 06:43")
        self.assertEqual(output.code, 1, output.stdout)
        self.assertIn("arbiter-c9-checkpoint-alpha-20260317", self.arbiter_ids())

    def test_a_domain_name_that_prefixes_another_is_not_confused_with_it(self):
        table = TABLE + ("\n- domain: beta-bis\n  pl: Opus-PL-Bis\n  checkpoint: Beta/CHECKPOINT_BIS.md\n"
                         "  queue: \"## The queue\"\n  modules: module-c\n")
        self.write("repo/Method/domains.yaml", table)
        self.write("repo/Beta/CHECKPOINT_BIS.md", checkpoint("bis-1"))
        self.write_workstreams(block("alpha-1", status="upcoming", module="module-a"),
                               block("beta-1", status="upcoming", module="module-b"),
                               block("bis-1", status="upcoming", module="module-c"),
                               block("arbiter-c9-checkpoint-beta-bis-20260301", title="Old", status="to-brief",
                                     module="method", **{"for": "Opus-PL-Bis"}))
        self.write("repo/Alpha/CHECKPOINT_ALPHA.md", checkpoint("alpha-1"))
        self.write("repo/Beta/CHECKPOINT_BETA.md", checkpoint())
        self.commit("a beta-bis domain is open")
        output = self.arbitrate()
        self.assertEqual(output.code, 1, output.stdout + output.stderr)
        self.assertIn("arbiter-c9-checkpoint-beta-20260315", self.arbiter_ids())


class TestCheck9Table(ArbiterCase):
    def test_a_fault_of_the_table_goes_to_the_coordinator_as_a_single_workstream(self):
        os.remove(self.repo / "Beta" / "CHECKPOINT_BETA.md")
        os.remove(self.repo / "Alpha" / "CHECKPOINT_ALPHA.md")
        self.commit("two checkpoints lost")
        output = self.arbitrate()
        self.assertEqual(output.code, 1, output.stdout + output.stderr)
        self.assertEqual(self.arbiter_ids(), ["arbiter-c9-table-20260315"])
        table = self.by_id()["arbiter-c9-table-20260315"]
        self.assertEqual((table["for"], table["module"]), ("Opus-Coordination", "method"))
        self.assertIn("alpha: checkpoint not found Alpha/CHECKPOINT_ALPHA.md; "
                      "beta: checkpoint not found Beta/CHECKPOINT_BETA.md", table["basis"])

    def test_never_filed_again_while_a_table_workstream_is_open(self):
        os.remove(self.repo / "Beta" / "CHECKPOINT_BETA.md")
        self.commit("a checkpoint lost")
        self.arbitrate()
        after = self.read("Folder/workstreams.yaml")
        output = self.arbitrate(date="2026-03-18 06:43")
        self.assertEqual(output.code, 0, output.stdout)
        self.assertEqual(self.read("Folder/workstreams.yaml"), after)

    def test_an_empty_queue_section_in_the_table_is_a_gap_of_the_domain_not_of_the_table(self):
        self.write("repo/Method/domains.yaml", TABLE.replace('  queue: "## The queue"\n  modules: module-a',
                                                             '  queue:\n  modules: module-a'))
        self.commit("queue not declared")
        output = self.arbitrate()
        self.assertEqual(output.code, 1, output.stdout + output.stderr)
        self.assertEqual(self.arbiter_ids(), ["arbiter-c9-checkpoint-alpha-20260315"])
        self.assertIn("alpha: no queue section declared", self.by_id()["arbiter-c9-checkpoint-alpha-20260315"]["basis"])


class TestCheck10(ArbiterCase):
    def set_a_heavy_checkpoint(self):
        self.write("repo/Alpha/CHECKPOINT_ALPHA.md", checkpoint("alpha-1", padding=11000))
        self.commit("a heavy checkpoint")

    def test_a_checkpoint_over_10_kb_makes_one_workstream_per_domain(self):
        self.set_a_heavy_checkpoint()
        output = self.arbitrate()
        self.assertEqual(output.code, 1, output.stdout + output.stderr)
        self.assertEqual(self.arbiter_ids(), ["arbiter-c10-short-checkpoint-alpha-20260315"])
        c = self.by_id()["arbiter-c10-short-checkpoint-alpha-20260315"]
        self.assertEqual((c["for"], c["module"]), ("Opus-PL-Alpha", "method"))
        self.assertEqual(c["title"], "The alpha checkpoint exceeds 10 KB")
        self.assertRegex(c["basis"], r"^Reported by the arbiter on 15 March 2026 \(check 10\)\. alpha: "
                                     r"Alpha/CHECKPOINT_ALPHA\.md weighs \d+ bytes, cap 10240\. "
                                     r"Move the history out to `Alpha/Archives/`, cited in one line; "
                                     r"the checkpoint fits in 10 KB \(method §6\)\.$")
        self.assertRegex(self.log_lines()[0], r"· checkpoints: alpha · footprint")

    def test_no_duplicate_at_the_next_run(self):
        self.set_a_heavy_checkpoint()
        self.arbitrate()
        after = self.read("Folder/workstreams.yaml")
        output = self.arbitrate(date="2026-03-16 06:43")
        self.assertEqual(output.code, 0, output.stdout)
        self.assertEqual(self.read("Folder/workstreams.yaml"), after)

    def test_an_open_workstream_for_that_pl_that_carries_short_checkpoint_is_enough(self):
        self.set_a_heavy_checkpoint()
        self.write_workstreams(block("alpha-1", status="upcoming", module="module-a"),
                               block("beta-1", status="upcoming", module="module-b"),
                               block("alpha-short-checkpoint", title="Done by hand", status="to-brief",
                                     module="module-a", **{"for": "Opus-PL-Alpha"}))
        self.write("repo/Alpha/CHECKPOINT_ALPHA.md", checkpoint("alpha-1", "alpha-short-checkpoint", padding=11000))
        self.commit("a finding set by hand")
        output = self.arbitrate()
        self.assertEqual(output.code, 0, output.stdout + output.stderr)
        self.assertEqual(self.arbiter_ids(), [])


def long(id: str, size: int = 1700, **keys) -> str:
    """A workstream entry of "size" bytes (its lines, each followed by a line break), above the cap."""
    base = block(id, **keys, basis="")
    empty = sum(len(line.encode("utf-8")) + 1 for line in base.split("\n"))
    return block(id, **keys, basis="x" * (size - empty))


def decision(number: int, characters: int) -> str:
    """A line "| **D<n>** | … |" of "characters" characters."""
    start, end = f"| **D{number}** | ", " |"
    return start + "x" * (characters - len(start) - len(end)) + end


class TestCheck12(ArbiterCase):
    """Entries that are too long: one workstream per domain; "outside any domain" and "decision log" go to the coordinator."""
    cited = {"alpha": ("alpha-1",), "beta": ("beta-1",)}

    def set(self, *blocks: str, decisions: tuple = ()):
        self.write_workstreams(*blocks)
        self.write("repo/Folder/decision_log.md", decision_log(1, 2, 3) + "".join(f"{d}\n" for d in decisions))
        self.commit("long entries")

    def long_workstreams(self):
        return (long("alpha-1", 1700, status="upcoming", module="module-a"),
                long("beta-1", 1600, status="upcoming", module="module-b"))

    def with_log(self, since: str = "4"):
        return self.arbitrate("--log-from", since)

    def test_a_workstream_that_is_too_long_makes_one_workstream_per_domain(self):
        self.set(*self.long_workstreams())
        output = self.arbitrate()
        self.assertEqual(output.code, 1, output.stdout + output.stderr)
        self.assertEqual(self.arbiter_ids(), ["arbiter-c12-short-entries-alpha-20260315",
                                              "arbiter-c12-short-entries-beta-20260315"])
        alpha = self.by_id()["arbiter-c12-short-entries-alpha-20260315"]
        self.assertEqual((alpha["for"], alpha["module"], alpha["status"]), ("Opus-PL-Alpha", "method", "to-brief"))
        self.assertEqual(alpha["title"], "Entries of alpha exceed their cap")
        self.assertEqual(alpha["basis"], (
            "Reported by the arbiter on 15 March 2026 (check 12). "
            "alpha: workstream alpha-1 weighs 1700 bytes, cap 1536. "
            "Bring every entry under its cap (method §6): the state, the decision, the next move; "
            "the detail goes to the batch folder or to a note of the domain, the entry only keeps the summary and the path."))
        beta = self.by_id()["arbiter-c12-short-entries-beta-20260315"]
        self.assertEqual((beta["for"], beta["title"]), ("Opus-PL-Beta", "Entries of beta exceed their cap"))
        self.assertIn("beta: workstream beta-1 weighs 1600 bytes, cap 1536", beta["basis"])
        self.assertEqual(self.run_commit(output), "Arbiter 2026-03-15: 2 finding(s)")
        self.assertRegex(self.log_lines()[0], r"^- 2026-03-15 06:43 · 1 gap · 2 new findings · ")

    def test_several_lines_of_a_domain_make_a_single_workstream_joined_by_a_semicolon(self):
        self.set(long("alpha-1", 1700, status="upcoming", module="module-a"),
                 long("alpha-2", 1800, status="to-brief", module="module-a"),
                 block("beta-1", status="upcoming", module="module-b"))
        self.write("repo/Alpha/CHECKPOINT_ALPHA.md", checkpoint("alpha-1", "alpha-2"))
        self.commit("alpha-2 cited")
        self.arbitrate()
        self.assertEqual(self.arbiter_ids(), ["arbiter-c12-short-entries-alpha-20260315"])
        self.assertIn("(check 12). alpha: workstream alpha-1 weighs 1700 bytes, cap 1536; "
                      "alpha: workstream alpha-2 weighs 1800 bytes, cap 1536. Bring",
                      self.by_id()["arbiter-c12-short-entries-alpha-20260315"]["basis"])

    def test_outside_any_domain_and_log_go_to_the_coordinators_domain_in_the_order_of_the_table(self):
        self.set(long("orphan-1", 1900, status="debt", module="unknown"), *self.long_workstreams(),
                 decisions=(decision(4, 900), decision(5, 100), decision(6, 801)))
        output = self.with_log()
        self.assertEqual(output.code, 1, output.stdout + output.stderr)
        self.assertEqual(self.arbiter_ids(), ["arbiter-c12-short-entries-alpha-20260315",
                                              "arbiter-c12-short-entries-beta-20260315",
                                              "arbiter-c12-short-entries-coordination-20260315"])
        c = self.by_id()["arbiter-c12-short-entries-coordination-20260315"]
        self.assertEqual((c["for"], c["module"], c["title"]),
                         ("Opus-Coordination", "method", "Entries of coordination exceed their cap"))
        self.assertIn("(check 12). outside any domain: workstream orphan-1 weighs 1900 bytes, cap 1536; "
                      "decision log: D4 counts 900 characters, cap 800; "
                      "decision log: D6 counts 801 characters, cap 800. Bring", c["basis"])
        self.assertIn("New findings (3):", output.stdout)

    def test_the_coordinators_domain_also_groups_its_own_lines(self):
        self.set(long("method-1", 1700, status="upcoming", module="method"),
                 block("alpha-1", status="upcoming", module="module-a"), block("beta-1", status="upcoming", module="module-b"),
                 decisions=(decision(4, 900),))
        self.write("repo/Method/CHECKPOINT_METHOD.md", checkpoint("method-1"))
        self.commit("method-1 cited")
        self.with_log()
        self.assertEqual(self.arbiter_ids(), ["arbiter-c12-short-entries-coordination-20260315"])
        self.assertIn("(check 12). coordination: workstream method-1 weighs 1700 bytes, cap 1536; "
                      "decision log: D4 counts 900 characters, cap 800. Bring",
                      self.by_id()["arbiter-c12-short-entries-coordination-20260315"]["basis"])

    def test_the_findings_of_check_12_come_after_those_of_checks_9_and_10(self):
        self.write("repo/Alpha/CHECKPOINT_ALPHA.md", checkpoint("alpha-1", padding=11000))
        self.set(*self.long_workstreams(), block("beta-2", status="upcoming", module="module-b"))
        self.arbitrate()
        self.assertEqual(self.arbiter_ids(), [
            "arbiter-c9-checkpoint-beta-20260315", "arbiter-c10-short-checkpoint-alpha-20260315",
            "arbiter-c12-short-entries-alpha-20260315", "arbiter-c12-short-entries-beta-20260315"])

    def test_without_log_from_the_log_is_not_measured(self):
        self.set(block("alpha-1", status="upcoming", module="module-a"), block("beta-1", status="upcoming", module="module-b"),
                 decisions=(decision(4, 5000),))
        output = self.arbitrate()
        self.assertEqual(output.code, 0, output.stdout + output.stderr)
        self.assertEqual(self.arbiter_ids(), [])

    def test_log_from_is_passed_as_it_is(self):
        self.set(block("alpha-1", status="upcoming", module="module-a"), block("beta-1", status="upcoming", module="module-b"),
                 decisions=(decision(4, 900), decision(5, 900)))
        self.with_log("5")
        self.assertEqual(self.arbiter_ids(), ["arbiter-c12-short-entries-coordination-20260315"])
        basis = self.by_id()["arbiter-c12-short-entries-coordination-20260315"]["basis"]
        self.assertIn("decision log: D5 counts 900 characters", basis)
        self.assertNotIn("D4 counts", basis)

    def test_an_invalid_log_from_is_an_impossible_check(self):
        self.set(*self.long_workstreams())
        output = self.with_log("abc")
        self.assertEqual(output.code, 2, output.stdout + output.stderr)
        self.assertIn("check_living_docs.py failed (code 2)", output.stderr)
        self.assertEqual(self.arbiter_ids(), [])
        self.assertRegex(self.log_lines()[0], r"check impossible: check_living_docs\.py$")

    def test_no_duplicate_at_the_next_run_even_on_another_day(self):
        self.set(*self.long_workstreams(), decisions=(decision(4, 900),))
        self.with_log()
        after = self.read("Folder/workstreams.yaml")
        output = self.arbitrate("--log-from", "4", date="2026-03-16 06:43")
        self.assertEqual(output.code, 0, output.stdout + output.stderr)
        self.assertEqual(self.read("Folder/workstreams.yaml"), after)
        self.assertEqual(len(self.arbiter_ids()), 3)
        self.assertIn("Reported before and still there (3):", output.stdout)

    def test_the_filed_workstreams_are_not_measured_themselves(self):
        self.set(*self.long_workstreams(), decisions=(decision(4, 900),))
        self.with_log()
        checker = self.repo / "Method" / "check_living_docs.py"
        check = self.run_script(checker, *self.verifications(), "--domains", "Method/domains.yaml", cwd=self.repo)
        self.assertEqual(check.count(12), "2 open workstreams, decision log not measured, 2 above", check.stdout)
        self.assertEqual(check.details(12), ["alpha: workstream alpha-1 weighs 1700 bytes, cap 1536",
                                             "beta: workstream beta-1 weighs 1600 bytes, cap 1536"])

    def test_an_open_workstream_for_that_pl_whose_id_carries_short_entries_is_enough(self):
        self.set(*self.long_workstreams(),
                 block("alpha-short-entries", title="Done by hand", status="to-brief", module="module-a",
                       **{"for": "Opus-PL-Alpha"}))
        self.write("repo/Alpha/CHECKPOINT_ALPHA.md", checkpoint("alpha-1"))
        self.commit("a finding set by hand")
        output = self.arbitrate()
        self.assertEqual(self.arbiter_ids(), ["arbiter-c12-short-entries-beta-20260315"])
        self.assertIn("Reported before and still there (1):\n  - alpha-short-entries · for Opus-PL-Alpha", output.stdout)

    def test_an_accepted_workstream_or_one_for_another_pl_does_not_cover(self):
        self.set(*self.long_workstreams(),
                 block("alpha-short-entries", status="accepted", module="module-a", **{"for": "Opus-PL-Alpha"}),
                 block("gamma-short-entries", status="to-brief", module="module-b", **{"for": "Opus-PL-Gamma"}))
        self.arbitrate()
        self.assertEqual(self.arbiter_ids(), ["arbiter-c12-short-entries-alpha-20260315",
                                              "arbiter-c12-short-entries-beta-20260315"])

    def test_an_archived_id_is_not_reused_the_date_is_added(self):
        self.set(*self.long_workstreams())
        self.write("repo/Folder/Archives/WORKSTREAMS_2026-03.yaml", "# Archived workstreams — March 2026\n\n" + block(
            "arbiter-c12-short-entries-alpha-20260315", status="accepted", module="method", **{"for": "Opus-PL-Alpha"}))
        self.commit("a finding of the day already archived")
        self.arbitrate()
        self.assertEqual(self.arbiter_ids(), ["arbiter-c12-short-entries-alpha-20260315-20260315",
                                              "arbiter-c12-short-entries-beta-20260315"])

    def test_the_other_findings_are_those_of_before(self):
        self.set(block("alpha-1", status="in-flight", module="module-a"),  # in flight without pl: check 5
                 long("beta-1", 1600, status="upcoming", module="module-b"))
        self.arbitrate()
        self.assertEqual(self.arbiter_ids(), ["arbiter-c5-alpha-1", "arbiter-c12-short-entries-beta-20260315"])
        self.assertEqual(self.by_id()["arbiter-c5-alpha-1"]["title"],
                         "Check 5: alpha-1 (line 3): pl missing or empty")

    def test_the_docstring_describes_check_12_and_the_option(self):
        doc = load(ARBITER, "arbiter_doc").__doc__
        for expected in ("--log-from", "arbiter-c12-short-entries-<domain>-<YYYYMMDD>", "short-entries"):
            self.assertIn(expected, doc)


class TestBatons(ArbiterCase):
    def set_a_baton(self, domain: str, identifier: str, since: str = "1 March"):
        self.write(f"repo/{CHECKPOINTS[domain]}", checkpoint(*self.cited.get(domain, ()),
                   baton=f"**Session active: {identifier}, since {since}**"))

    def test_a_baton_silent_for_more_than_24_h_goes_to_the_log_and_the_output_without_a_workstream(self):
        self.set_a_baton("alpha", "AbCd1234")
        self.commit("Alpha: resumption\n\nClaude-Session: https://claude.ai/code/session_01XYZAbCd1234",
                    when="2026-03-14T04:00:00+0100")
        before = self.read("Folder/workstreams.yaml")
        output = self.arbitrate()
        self.assertEqual(output.code, 0, output.stdout + output.stderr)
        self.assertEqual(self.read("Folder/workstreams.yaml"), before)
        self.assertEqual(self.arbiter_ids(), [])
        self.assertIn("alpha (AbCd1234, last commit on 2026-03-14 04:00)", self.log_lines()[0])
        self.assertIn("Batons · alpha (AbCd1234, last commit on 2026-03-14 04:00)", output.stdout)

    def test_a_baton_that_committed_less_than_24_h_ago_is_fresh(self):
        self.set_a_baton("alpha", "AbCd1234")
        self.commit("Alpha: resumption AbCd1234", when="2026-03-14T08:00:00+0100")
        output = self.arbitrate()
        self.assertEqual(output.code, 0, output.stdout)
        self.assertIn("· batons fresh ·", self.log_lines()[0])

    def test_the_oldest_baton_is_given(self):
        self.set_a_baton("alpha", "AbCd1234")
        self.set_a_baton("beta", "ZyXw9876")
        self.commit("Alpha AbCd1234", when="2026-03-13T10:00:00+0100")
        self.commit("Beta ZyXw9876", when="2026-03-11T10:00:00+0100")
        self.arbitrate()
        self.assertIn("· beta (ZyXw9876, last commit on 2026-03-11 10:00) ·", self.log_lines()[0])

    def test_the_coordination_is_excluded_from_the_batons(self):
        self.set_a_baton("coordination", "CoOr5678", since="1 March")
        self.commit("Coordination CoOr5678", when="2026-03-05T10:00:00+0100")
        output = self.arbitrate()
        self.assertEqual(output.code, 0, output.stdout)
        self.assertIn("· batons fresh ·", self.log_lines()[0])

    def test_without_any_commit_of_the_baton_the_last_commit_of_the_checkpoint_stands_for_the_setting(self):
        self.set_a_baton("alpha", "AbCd1234")
        self.commit("Alpha: a baton with no trace of a session", when="2026-03-10T10:00:00+0100")
        self.arbitrate()
        self.assertIn("alpha (AbCd1234, no commit, checkpoint touched on 2026-03-10 10:00)",
                      self.log_lines()[0])

    def test_a_free_or_not_applicable_baton_is_not_checked(self):
        self.write(f"repo/{CHECKPOINTS['alpha']}", checkpoint("alpha-1", baton="**Session active: not applicable — sheet.**"))
        self.commit("sheet", when="2026-03-02T10:00:00+0100")
        self.arbitrate()
        self.assertIn("· batons fresh ·", self.log_lines()[0])

    def test_a_baton_whose_message_carries_the_identifier_in_the_session_line_counts(self):
        self.set_a_baton("alpha", "AbCd1234")
        self.commit("Resumption\n\nClaude-Session: https://claude.ai/code/session_01XYZAbCd1234", when="2026-03-15T01:00:00+0100")
        self.arbitrate()
        self.assertIn("· batons fresh ·", self.log_lines()[0])


class TestLateCheckpoint(ArbiterCase):
    cited = {"alpha": ("alpha-1",), "beta": ("beta-1",)}

    def compliant_workstreams(self):
        self.write_workstreams(
            block("alpha-1", title="First", status="upcoming", module="module-a"),
            block("alpha-2", title="Delivered", status="accepted", module="module-a", accepted_on="2026-03-12"),
            block("beta-1", title="Other", status="upcoming", module="module-b"))

    def test_a_workstream_accepted_after_the_last_commit_of_the_checkpoint_is_detected(self):
        output = self.arbitrate()  # alpha's checkpoint dates from 1 March, the acceptance from the 12th
        self.assertEqual(output.code, 1, output.stdout + output.stderr)
        self.assertEqual(self.arbiter_ids(), ["arbiter-c9-checkpoint-alpha-20260315"])
        c = self.by_id()["arbiter-c9-checkpoint-alpha-20260315"]
        self.assertEqual(c["for"], "Opus-PL-Alpha")
        self.assertIn("alpha: alpha-2 has been accepted since 2026-03-12, "
                      "the checkpoint has not been touched since 2026-03-01", c["basis"])
        self.assertIn("Take your checkpoint up again", c["basis"])
        self.assertNotIn("Cite every open workstream", c["basis"], "no check-9 line: no citation instruction")
        self.assertRegex(self.log_lines()[0], r"· 1 gap · 1 new finding · .*· checkpoints: alpha · footprint")

    def test_no_gap_if_the_checkpoint_was_touched_after_the_acceptance(self):
        self.write(f"repo/{CHECKPOINTS['alpha']}", checkpoint("alpha-1") + "\nUpdated.\n")
        self.commit("Alpha: checkpoint up to date", when="2026-03-13T10:00:00+0100")
        output = self.arbitrate()
        self.assertEqual(output.code, 0, output.stdout + output.stderr)
        self.assertEqual(self.arbiter_ids(), [])
        self.assertIn("· 0 gaps ·", self.log_lines()[0])

    def test_the_same_day_is_not_a_lateness(self):
        self.write(f"repo/{CHECKPOINTS['alpha']}", checkpoint("alpha-1") + "\nUpdated.\n")
        self.commit("Alpha: checkpoint of the acceptance day", when="2026-03-12T23:00:00+0100")
        self.assertEqual(self.arbitrate().code, 0)

    def test_the_lateness_is_grouped_with_the_check_9_lines_of_the_same_domain(self):
        self.write_workstreams(
            block("alpha-1", status="upcoming", module="module-a"),
            block("alpha-2", status="accepted", module="module-a", accepted_on="2026-03-12"),
            block("alpha-3", status="upcoming", module="module-a"),
            block("beta-1", status="upcoming", module="module-b"))
        self.commit("alpha-3 is not cited")
        output = self.arbitrate()
        self.assertEqual(output.code, 1, output.stdout + output.stderr)
        self.assertEqual(self.arbiter_ids(), ["arbiter-c9-checkpoint-alpha-20260315"])
        basis = self.by_id()["arbiter-c9-checkpoint-alpha-20260315"]["basis"]
        self.assertIn("alpha: alpha-3 (upcoming) is not cited in the checkpoint; alpha: alpha-2 has been accepted", basis)

    def test_a_message_for_a_pl_is_not_a_subject_of_the_domain(self):
        self.write_workstreams(
            block("alpha-1", status="upcoming", module="module-a"),
            block("alpha-msg", status="accepted", module="module-a", accepted_on="2026-03-12", **{"for": "Opus-PL-Alpha"}),
            block("beta-1", status="upcoming", module="module-b"))
        self.commit("a message accepted")
        self.assertEqual(self.arbitrate().code, 0)

    def test_no_duplicate_at_the_next_run(self):
        self.arbitrate()
        after = self.read("Folder/workstreams.yaml")
        output = self.arbitrate(date="2026-03-16 06:43")
        self.assertEqual(output.code, 0, output.stdout)
        self.assertEqual(self.read("Folder/workstreams.yaml"), after)


class TestNormalization(ArbiterCase):
    def test_normalization_is_done_before_the_check(self):
        text = self.read("Folder/workstreams.yaml").replace(
            "title: First", "title: First: a title with a colon")
        self.write("repo/Folder/workstreams.yaml", text)
        self.commit("a non-conforming value")
        output = self.arbitrate()
        self.assertEqual(output.code, 0, output.stdout + output.stderr)
        self.assertEqual(self.arbiter_ids(), [], "check 11 sees nothing any more: the value is normalized first")
        self.assertIn('  title: "First: a title with a colon"', self.read("Folder/workstreams.yaml"))
        self.assertEqual(self.run_commit(output), "Arbiter 2026-03-15: living docs compliant, 1 value(s) normalized")
        check = self.run_script(self.repo / "Method" / "check_living_docs.py", "--workstreams", "Folder/workstreams.yaml",
                                "--log", "Folder/decision_log.md", cwd=self.repo)
        self.assertEqual(check.verdict(11), "OK")

    def test_a_value_that_cannot_be_normalized_stays_a_check_11_gap_for_the_coordinator(self):
        text = self.read("Folder/workstreams.yaml").replace("title: First", "title: Fi\x01rst")
        self.write("repo/Folder/workstreams.yaml", text)
        self.commit("a control character")
        output = self.arbitrate()
        self.assertEqual(output.code, 1, output.stdout + output.stderr)
        self.assertEqual(self.arbiter_ids(), ["arbiter-c11-format-workstreams"])
        c = self.by_id()["arbiter-c11-format-workstreams"]
        self.assertEqual((c["for"], c["module"]), ("Opus-Coordination", "method"))


class TestArchiving(ArbiterCase):
    def compliant_workstreams(self):
        self.write_workstreams(
            block("alpha-1", title="First", status="upcoming", module="module-a"),
            block("beta-1", title="Other", status="upcoming", module="module-b"),
            block("alpha-old", title="Delivered eight days ago", status="accepted", module="module-a",
                  accepted_on="2026-03-07"),
            block("beta-new", title="Delivered yesterday", status="accepted", module="module-b"))

    cited = {"alpha": ("alpha-1",), "beta": ("beta-1",)}

    def test_archiving_dates_and_moves_out_and_the_log_and_the_commit_say_so(self):
        self.write("repo/Alpha/CHECKPOINT_ALPHA.md", checkpoint("alpha-1") + "\nUpdated.\n")
        self.commit("Alpha up to date", when="2026-03-14T10:00:00+0100")
        output = self.arbitrate()
        self.assertEqual(output.code, 0, output.stdout + output.stderr)
        archive = self.read("Folder/Archives/WORKSTREAMS_2026-03.yaml")
        self.assertIn("- id: alpha-old", archive)
        workstreams = self.read("Folder/workstreams.yaml")
        self.assertNotIn("alpha-old", workstreams)
        self.assertIn("  status: accepted\n  accepted-on: 2026-03-15\n", workstreams)
        self.assertIn("· archiving: 1 dated, 1 archived ·", self.log_lines()[0])
        self.assertEqual(self.run_commit(output), "Arbiter 2026-03-15: living docs compliant, 1 dated, 1 archived")
        self.assertIn("Folder/Archives/", " ".join(self.modified()))
        self.assertIn("Archiving · 1 dated, 1 archived", output.stdout)

    def test_the_board_is_regenerated_when_archiving_changes_workstreams_yaml(self):
        self.write("repo/Alpha/CHECKPOINT_ALPHA.md", checkpoint("alpha-1") + "\nUpdated.\n")
        self.commit("Alpha up to date", when="2026-03-14T10:00:00+0100")
        before = self.read("Folder/workstreams.json")
        self.arbitrate()
        self.assertNotEqual(self.read("Folder/workstreams.json"), before)
        self.assertNotIn("alpha-old", self.read("Folder/workstreams.json"))
        check = self.run_script(self.repo / "Method" / "check_living_docs.py", "--workstreams", "Folder/workstreams.yaml",
                                "--log", "Folder/decision_log.md", "--archives", "Folder/Archives",
                                "--board", "Folder/workstreams.html", "--generator", "Method/make_board.py",
                                cwd=self.repo)
        self.assertEqual(check.verdict(6), "OK", check.stdout)

    def test_an_unreadable_date_is_a_finding_for_the_coordinator(self):
        self.write_workstreams(block("alpha-1", status="upcoming", module="module-a"),
                               block("beta-1", status="upcoming", module="module-b"),
                               block("alpha-bad", status="accepted", module="module-a", accepted_on="yesterday"))
        self.commit("an unreadable date")
        output = self.arbitrate()
        self.assertEqual(output.code, 1, output.stdout + output.stderr)
        self.assertEqual(self.arbiter_ids(), ["arbiter-ca-archiving-alpha-bad"])
        c = self.by_id()["arbiter-ca-archiving-alpha-bad"]
        self.assertEqual((c["for"], c["module"]), ("Opus-Coordination", "module-a"))
        self.assertIn("alpha-bad: unreadable accepted-on", c["basis"])


class TestBoardOnlyIfChanged(ArbiterCase):
    def test_a_run_that_does_not_change_workstreams_yaml_does_not_touch_the_board(self):
        before = (self.read("Folder/workstreams.html"), self.read("Folder/workstreams.json"))
        self.arbitrate(date="2026-03-15 06:43")
        self.arbitrate(date="2026-03-16 06:43")
        self.assertEqual((self.read("Folder/workstreams.html"), self.read("Folder/workstreams.json")), before)
        self.assertEqual(self.modified(), ["Method/ARBITER_LOG.md"])

    def test_a_stale_board_is_reported_then_regenerated_because_workstreams_yaml_changed(self):
        self.write("repo/Folder/workstreams.json", "{}")
        self.commit("stale data", board=False)
        output = self.arbitrate()
        self.assertEqual(output.code, 1, output.stdout)
        self.assertEqual(self.arbiter_ids(), ["arbiter-c6-board"])
        self.assertNotEqual(self.read("Folder/workstreams.json"), "{}")
        self.assertIn("arbiter-c6-board", self.read("Folder/workstreams.json"))

    def test_without_a_board_the_script_does_not_write_one(self):
        self.write_workstreams(block("alpha-1", status="in-flight", module="module-a"),
                               block("beta-1", status="upcoming", module="module-b"))
        self.commit("alpha-1 in flight without pl")
        before = self.read("Folder/workstreams.json")
        options = [o for o in self.options() if o not in ("--board", "Folder/workstreams.html", "--generator",
                                                          "Method/make_board.py")]
        output = self.arbitrate(options=options)
        self.assertEqual(output.code, 1, output.stdout + output.stderr)
        self.assertEqual(self.read("Folder/workstreams.json"), before)


class TestMissingFile(ArbiterCase):
    def test_a_missing_file_returns_2_and_writes_the_log_alone(self):
        os.remove(self.repo / "Folder" / "decision_log.md")
        before = self.read("Folder/workstreams.yaml")
        output = self.arbitrate()
        self.assertEqual(output.code, 2, output.stdout + output.stderr)
        self.assertIn("file not found: Folder/decision_log.md", output.stderr)
        self.assertEqual(self.read("Folder/workstreams.yaml"), before)
        self.assertEqual(self.modified(), ["Folder/decision_log.md", "Method/ARBITER_LOG.md"])
        self.assertEqual(self.log_lines(), ["- 2026-03-15 06:43 · check impossible: Folder/decision_log.md"])
        self.assertEqual(self.run_commit(output), "Arbiter 2026-03-15: check impossible")

    def test_a_missing_archives_folder_returns_2(self):
        shutil.rmtree(self.repo / "Folder" / "Archives")
        output = self.arbitrate()
        self.assertEqual(output.code, 2)
        self.assertIn("check impossible: Folder/Archives", self.log_lines()[0])

    def test_a_missing_neighboring_script_returns_2(self):
        os.remove(self.repo / "Method" / "check_living_docs.py")
        output = self.arbitrate()
        self.assertEqual(output.code, 2)
        self.assertIn("check impossible: check_living_docs.py", self.log_lines()[0])

    def test_outside_a_git_repository_returns_2(self):
        shutil.rmtree(self.repo / ".git")
        output = self.arbitrate()
        self.assertEqual(output.code, 2)
        self.assertIn("check impossible: git repository", self.log_lines()[0])

    def test_a_script_that_fails_returns_2(self):
        self.write("repo/Method/make_board.py", "import sys\nsys.exit(3)\n")
        self.write_workstreams(block("alpha-1", status="in-flight", module="module-a"),
                               block("beta-1", status="upcoming", module="module-b"))
        self.commit("a broken generator", board=False)
        output = self.arbitrate()
        self.assertEqual(output.code, 2, output.stdout + output.stderr)
        self.assertRegex(self.log_lines()[-1], r"check impossible: ")


class TestFootprint(ArbiterCase):
    def test_the_footprint_of_the_log_sums_the_method_the_sheet_and_the_checkpoints(self):
        self.write("repo/Method/METHOD.md", "x" * 3000)
        for path in CHECKPOINTS.values():
            self.write(f"repo/{path}", "x" * 1000)
        self.write("repo/Folder/SHEET.md", "x" * 2000)
        self.commit("known sizes")
        self.arbitrate(options=self.options(method=True) + ["--sheet", "Folder/SHEET.md"])
        # 3000 + 2000 + 3 × 1000 = 8000 bytes = 7.8 KB, rounded to 8
        self.assertTrue(self.log_lines()[0].endswith(" · footprint: 8 KB"), self.log_lines()[0])

    def test_without_method_or_sheet_the_footprint_only_counts_the_checkpoints(self):
        for path in CHECKPOINTS.values():
            self.write(f"repo/{path}", "x" * 1024)
        self.commit("three checkpoints of 1 KB")
        self.arbitrate(options=self.options(method=False))
        self.assertTrue(self.log_lines()[0].endswith(" · footprint: 3 KB"), self.log_lines()[0])

    def test_a_file_given_twice_counts_once(self):
        for path in CHECKPOINTS.values():
            self.write(f"repo/{path}", "x" * 1024)
        self.commit("three checkpoints of 1 KB")
        self.arbitrate(options=self.options(method=False, sheet=True))  # the sheet is alpha's checkpoint
        self.assertTrue(self.log_lines()[0].endswith(" · footprint: 3 KB"), self.log_lines()[0])


class TestInvalidCalls(ArbiterCase):
    def test_a_required_option_is_missing(self):
        options = self.options()
        i = options.index("--log")
        output = self.arbitrate(options=options[:i] + options[i + 2:])
        self.assertEqual(output.code, 2)
        self.assertIn("missing argument: --log", output.stderr)
        self.assertEqual(self.log_lines(), [])

    def test_board_and_generator_go_together(self):
        options = [o for o in self.options() if o not in ("--generator", "Method/make_board.py")]
        output = self.arbitrate(options=options)
        self.assertEqual(output.code, 2)
        self.assertIn("--board and --generator go together", output.stderr)

    def test_an_unknown_option(self):
        output = self.arbitrate("--gizmo", "1")
        self.assertEqual(output.code, 2)
        self.assertIn("unknown argument: --gizmo", output.stderr)

    def test_a_malformed_date(self):
        output = self.arbitrate(date="15/03/2026")
        self.assertEqual(output.code, 2)
        self.assertIn("--date: YYYY-MM-DD HH:MM expected", output.stderr)


class TestWorkflow(unittest.TestCase):
    def text(self) -> str:
        return WORKFLOW.read_text(encoding="utf-8")

    def test_the_template_carries_the_trigger_the_rights_and_the_script(self):
        text = self.text()
        for expected in ("schedule:", 'cron: "42 5 * * *"', "workflow_dispatch:", "contents: write", "concurrency:",
                         "fetch-depth: 300", "actions/checkout@v4", "actions/setup-python@v5", 'python-version: "3.12"',
                         "github-actions[bot]", "git pull --rebase", "GITHUB_STEP_SUMMARY", "sed -n 's/^Commit: //p'"):
            self.assertIn(expected, text)

    def test_it_does_not_live_in_the_package_s_github_folder(self):
        self.assertFalse((TEMPLATES.parent.parent / ".github" / "workflows" / "arbiter.yml").exists())

    @unittest.skipIf(pyyaml is None, "PyYAML absent")
    def test_the_template_is_valid_yaml_and_its_structure_is_the_expected_one(self):
        document = pyyaml.safe_load(self.text())
        triggers = document.get("on", document.get(True))  # YAML 1.1 reads "on" as a boolean
        self.assertIn("schedule", triggers)
        self.assertIn("workflow_dispatch", triggers)
        self.assertEqual(document["permissions"], {"contents": "write"})
        self.assertEqual(document["concurrency"]["cancel-in-progress"], False)
        steps = document["jobs"]["arbiter"]["steps"]
        self.assertEqual(steps[0]["with"]["fetch-depth"], 300)
        self.assertEqual(steps[1]["with"]["python-version"], "3.12")
        for variable in ("SCRIPT", "WORKSTREAMS", "LOG", "ARCHIVES", "DOMAINS", "ARBITER_LOG"):
            self.assertIn(variable, document["env"])

    def test_the_variable_log_from_is_optional_and_empty_by_default(self):
        text = self.text()
        self.assertRegex(text, r'(?m)^  LOG_FROM: ""$')
        self.assertIn('if [ -n "$LOG_FROM" ]; then args+=(--log-from "$LOG_FROM"); fi', text)
        self.assertLess(text.index("  SHEET:"), text.index("  LOG_FROM:"))
        self.assertLess(text.index("  LOG_FROM:"), text.index("jobs:"))

    def test_every_path_has_its_variable_at_the_top_of_the_file(self):
        text = self.text()
        for variable in ("WORKSTREAMS", "LOG", "ARCHIVES", "DOMAINS", "ARBITER_LOG", "BOARD", "GENERATOR",
                         "PLAN_LOG", "METHOD", "SHEET", "SCRIPT"):
            self.assertRegex(text, rf"(?m)^  {variable}: ")


if __name__ == "__main__":
    unittest.main()
