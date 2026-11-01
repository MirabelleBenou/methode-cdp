"""Tests of check_living_docs.py: each of the twelve checks, once OK and once in gap; the invalid calls.

Every test builds its fixtures in a temporary folder (see test_tools.py) and calls the script on the
command line; a few tests call its functions when that is clearer.
"""
import re
import unittest

from .test_tools import (CHECKER, GAP, GENERATOR, NOT_REQUESTED, NO_PYYAML, WARNING, TempCase,
                         block, decision_log, load, pyyaml_reading, without_position, yaml)

TWO_DOMAINS_TABLE = """# Domains
- domain: alpha
  pl: Opus-PL-Alpha
  checkpoint: CHECKPOINT_ALPHA.md
  queue: "## The queue"
  modules: module-a
  prefixes: alpha-

- domain: beta
  pl: Opus-PL-Beta
  checkpoint: CHECKPOINT_BETA.md
  queue: "## The queue"
  modules: module-b
"""


def checkpoint(*cited: str, history: tuple = ()) -> str:
    """A checkpoint: a queue section that cites the given ids, then a history section."""
    queue = "".join(f"- `{i}` to do\n" for i in cited)
    rest = "".join(f"- `{i}` done\n" for i in history)
    return f"# Checkpoint\n## State\nNothing to report.\n## The queue\n{queue}## History\n{rest}"


class CheckerCase(TempCase):
    """A base that passes the first five checks; each test changes one piece."""

    def setUp(self):
        super().setUp()
        self.log = self.write("decision_log.md", decision_log(1, 2, 3))
        self.workstreams = self.write("workstreams.yaml", yaml(
            block("alpha-1", title="First", status="upcoming", module="module-a"),
            block("alpha-2", title="Second", status="accepted", module="module-a", version="v1.0.0")))

    def check(self, *options, cwd=None):
        return self.run_script(CHECKER, "--workstreams", self.workstreams, "--log", self.log, *options, cwd=cwd)

    def with_workstreams(self, *blocks: str):
        """Replaces workstreams.yaml with the given blocks."""
        self.workstreams = self.write("workstreams.yaml", yaml(*blocks))

    def archives(self, **files) -> str:
        """An archives folder; files: name (without extension) -> blocks; returns the folder's path."""
        folder = self.subfolder("archives")
        for name, blocks in files.items():
            self.write(f"archives/{name}.yaml", yaml(*blocks, header="# Archived workstreams — Test"))
        return str(folder)


class TestBasicCall(CheckerCase):
    def test_base_without_option_no_gap(self):
        output = self.check()
        self.assertEqual(output.code, 0, output.stdout + output.stderr)
        self.assertEqual(output.summary, "LIVING DOCS · no gap")
        for rank in (1, 2, 3, 4, 5, 8):
            self.assertEqual(output.verdict(rank), "OK", f"check {rank}")
        self.assertEqual(output.count(1), "3 numbers, D1 to D3")
        self.assertEqual(output.count(2), "no reservation pending")
        self.assertEqual(output.count(3), "2 workstreams")
        self.assertEqual(output.count(4), "1 versions")
        self.assertEqual(output.count(5), "0 in flight")
        self.assertEqual(output.count(8), "0 deliverables, 0 resources, 0 in flight, 0 waiting")
        self.assertEqual(output.verdict(11), "OK", "check 11 always runs")
        self.assertEqual(output.count(11), "1 files, 12 lines read")

    def test_not_requested_when_an_option_is_missing(self):
        output = self.check()
        for rank in (6, 7, 9, 10, 12):
            self.assertEqual(output.verdict(rank), NOT_REQUESTED, f"check {rank}")
        self.assertEqual(len(output.checks) - 1, 12, "twelve check lines, plus the summary")

    def test_twelve_checks_in_order(self):
        labels = re.findall(r"^\d+\s+(\S.*?)\s+(?:OK|GAP|warning|—)(?:\s|$)", self.check().stdout, flags=re.M)
        self.assertEqual(labels, [
            "decision numbers", "reservations", "workstream ids", "batch versions",
            "workstreams in flight", "board", "version log", "deliverables and resources", "checkpoints",
            "checkpoint size", "YAML format", "entry sizes"])

    def test_a_gap_gives_code_1(self):
        self.log = self.write("decision_log.md", decision_log(1, 3))
        output = self.check()
        self.assertEqual(output.code, 1)
        self.assertEqual(output.summary, "LIVING DOCS · 1 gap(s)")

    def test_a_warning_does_not_change_the_code(self):
        self.log = self.write(
            "decision_log.md", decision_log(1, 2, 3) + "| **D4** | *reserved by Opus-PL-Alpha* |\n")
        output = self.check()
        self.assertEqual(output.code, 0)
        self.assertEqual(output.summary, "LIVING DOCS · no gap")

    def test_script_path_independent_of_the_current_folder(self):
        elsewhere = self.subfolder("elsewhere")
        output = self.check(cwd=elsewhere)
        self.assertEqual(output.code, 0, output.stdout + output.stderr)


class TestInvalidCalls(CheckerCase):
    def invalid(self, output, message: str):
        self.assertEqual(output.code, 2, output.stdout + output.stderr)
        self.assertEqual(output.stdout, "")
        self.assertTrue(output.stderr.startswith("check_living_docs: "), output.stderr)
        self.assertIn(message, output.stderr)

    def test_without_any_argument(self):
        self.invalid(self.run_script(CHECKER), "missing argument: --workstreams")

    def test_workstreams_option_missing(self):
        self.invalid(self.run_script(CHECKER, "--log", self.log), "missing argument: --workstreams")

    def test_log_option_missing(self):
        self.invalid(self.run_script(CHECKER, "--workstreams", self.workstreams), "missing argument: --log")

    def test_file_not_found(self):
        missing = self.folder / "missing.md"
        output = self.run_script(CHECKER, "--workstreams", self.workstreams, "--log", missing)
        self.invalid(output, f"file not found: --log {missing}")

    def test_workstreams_not_found(self):
        missing = self.folder / "missing.yaml"
        output = self.run_script(CHECKER, "--workstreams", missing, "--log", self.log)
        self.invalid(output, f"file not found: --workstreams {missing}")

    def test_archives_folder_not_found(self):
        output = self.check("--archives", self.folder / "nowhere")
        self.invalid(output, "file not found: --archives")

    def test_archives_that_is_a_file(self):
        output = self.check("--archives", self.log)
        self.invalid(output, "file not found: --archives")

    def test_domains_not_found(self):
        output = self.check("--domains", self.folder / "missing.yaml")
        self.invalid(output, "file not found: --domains")

    def test_root_not_found(self):
        table = self.write("domains.yaml", TWO_DOMAINS_TABLE)
        output = self.check("--domains", table, "--root", self.folder / "nowhere")
        self.invalid(output, "file not found: --root")

    def test_board_without_generator(self):
        board = self.write("workstreams.html", "<html></html>")
        self.invalid(self.check("--board", board), "--board and --generator go together")

    def test_generator_without_board(self):
        self.invalid(self.check("--generator", GENERATOR), "--board and --generator go together")

    def test_root_without_domains(self):
        self.invalid(self.check("--root", self.folder), "--root only goes with --domains")

    def test_cap_without_domains(self):
        self.invalid(self.check("--checkpoint-cap", "100"),
                     "--checkpoint-cap only goes with --domains")

    def test_cap_zero(self):
        table = self.write("domains.yaml", TWO_DOMAINS_TABLE)
        output = self.check("--domains", table, "--checkpoint-cap", "0")
        self.invalid(output, "--checkpoint-cap: a positive integer is expected (0)")

    def test_cap_not_an_integer(self):
        table = self.write("domains.yaml", TWO_DOMAINS_TABLE)
        for value in ("abc", "-5", "1.5", ""):
            with self.subTest(value=value):
                output = self.check("--domains", table, "--checkpoint-cap", value)
                self.invalid(output, "a positive integer is expected")

    def test_the_options_of_check_12_without_domains(self):
        for option in ("--workstream-cap", "--log-cap", "--log-from"):
            with self.subTest(option=option):
                self.invalid(self.check(option, "100"), f"{option} only goes with --domains")

    def test_the_options_of_check_12_want_a_positive_integer(self):
        table = self.write("domains.yaml", TWO_DOMAINS_TABLE)
        for option in ("--workstream-cap", "--log-cap", "--log-from"):
            for value in ("abc", "0", "-5", "1.5", "", "٣"):
                with self.subTest(option=option, value=value):
                    output = self.check("--domains", table, option, value)
                    self.invalid(output, f"{option}: a positive integer is expected ({value})")

    def test_unknown_argument(self):
        self.invalid(self.check("--unknown", "x"), "unknown argument: --unknown")

    def test_missing_value(self):
        output = self.run_script(CHECKER, "--log", self.log, "--workstreams")
        self.invalid(output, "missing value")

    def test_unreadable_file_is_an_invalid_call(self):
        unreadable = self.write("decision_log.md", b"\xff\xfe\x00 not utf-8", binary=True)
        output = self.run_script(CHECKER, "--workstreams", self.workstreams, "--log", unreadable)
        self.assertEqual(output.code, 2)
        self.assertTrue(output.stderr.startswith("check_living_docs: "))


class TestCheck1Numbers(CheckerCase):
    def with_log(self, text: str):
        self.log = self.write("decision_log.md", text)
        return self.check()

    def test_ok(self):
        output = self.with_log(decision_log(1, 2, 3, 4))
        self.assertEqual(output.verdict(1), "OK")
        self.assertEqual(output.count(1), "4 numbers, D1 to D4")
        self.assertEqual(output.details(1), [])

    def test_the_smallest_number_is_not_necessarily_1(self):
        output = self.with_log(decision_log(41, 42, 43))
        self.assertEqual(output.verdict(1), "OK")
        self.assertEqual(output.count(1), "3 numbers, D41 to D43")

    def test_gap_duplicate(self):
        output = self.with_log(decision_log(1, 2, 2, 3))
        self.assertEqual(output.verdict(1), GAP)
        self.assertEqual(output.details(1), ["D2 duplicated (lines 3, 4)"])
        self.assertEqual(output.count(1), "4 numbers, D1 to D3")
        self.assertEqual(output.code, 1)

    def test_gap_hole_of_one_number(self):
        output = self.with_log(decision_log(1, 3))
        self.assertEqual(output.verdict(1), GAP)
        self.assertEqual(output.details(1), ["D2 missing"])

    def test_gap_hole_of_several_numbers(self):
        output = self.with_log(decision_log(1, 2, 5))
        self.assertEqual(output.verdict(1), GAP)
        self.assertEqual(output.details(1), ["D3 to D4 (2 numbers) missing"])
        self.assertEqual(output.count(1), "3 numbers, D1 to D5")

    def test_gap_several_holes(self):
        output = self.with_log(decision_log(1, 3, 6, 7))
        self.assertEqual(output.details(1), ["D2 missing", "D4 to D5 (2 numbers) missing"])

    def test_gap_no_number(self):
        output = self.with_log("# Decision log\nnothing here\n")
        self.assertEqual(output.verdict(1), GAP)
        self.assertEqual(output.count(1), "no number found")
        self.assertEqual(output.details(1), ['no line "| **D<n>** |" in the decision log'])

    def test_lines_that_are_not_numbers_are_ignored(self):
        output = self.with_log(decision_log(1, 2) + "| D3 | not in bold |\n| **D9 | broken |\ntext | **D8** | outside a table\n")
        self.assertEqual(output.verdict(1), "OK")
        self.assertEqual(output.count(1), "2 numbers, D1 to D2")


class TestCheck2Reservations(CheckerCase):
    def with_log(self, text: str):
        self.log = self.write("decision_log.md", text)
        return self.check()

    def test_ok_no_reservation(self):
        output = self.check()
        self.assertEqual(output.verdict(2), "OK")
        self.assertEqual(output.count(2), "no reservation pending")

    def test_warning_one_reservation(self):
        output = self.with_log(decision_log(1, 2, 3) + "| **D4** | *reserved by Opus-PL-Alpha* |\n")
        self.assertEqual(output.verdict(2), WARNING)
        self.assertEqual(output.count(2), "1 reservation(s) pending")
        self.assertEqual(output.details(2), ["D4 reserved (line 5)"])
        self.assertEqual(output.verdict(1), "OK", "a reservation is indeed a number of the log")

    def test_warning_several_reservations(self):
        output = self.with_log(
            decision_log(1, 2) + "| **D3** | *reserved by Opus-PL-Alpha* |\n| **D4** |  *reserved by Opus-PL-Beta* |\n")
        self.assertEqual(output.verdict(2), WARNING)
        self.assertEqual(output.count(2), "2 reservation(s) pending")
        self.assertEqual(output.details(2), ["D3 reserved (line 4)", "D4 reserved (line 5)"])
        self.assertEqual(output.code, 0)

    def test_without_asterisk_it_is_not_a_reservation(self):
        output = self.with_log(decision_log(1, 2) + "| **D3** | reserved, without asterisk |\n")
        self.assertEqual(output.verdict(2), "OK")


class TestCheck3Ids(CheckerCase):
    def test_ok(self):
        output = self.check()
        self.assertEqual((output.verdict(3), output.count(3)), ("OK", "2 workstreams"))

    def test_gap_duplicated_id(self):
        self.with_workstreams(block("alpha-1", status="upcoming"), block("alpha-1", status="debt"))
        output = self.check()
        self.assertEqual(output.verdict(3), GAP)
        self.assertEqual(output.count(3), "2 workstreams")
        self.assertEqual(len(output.details(3)), 1)
        self.assertRegex(output.details(3)[0], r"^id alpha-1 duplicated \(lines 3, 6\)$")

    def test_entries_without_id_are_not_duplicates(self):
        self.workstreams = self.write(
            "workstreams.yaml", "# Workstreams — Test\n\n- title: No id\n  status: upcoming\n\n- title: Other\n  status: debt\n")
        self.assertEqual(self.check().verdict(3), "OK")

    def test_empty_archives_the_count_mentions_them(self):
        output = self.check("--archives", self.archives())
        self.assertEqual((output.verdict(3), output.count(3)), ("OK", "2 workstreams, 0 archived"))

    def test_archives_ok(self):
        folder = self.archives(**{"WORKSTREAMS_2026-03": [block("beta-1", status="accepted")]})
        output = self.check("--archives", folder)
        self.assertEqual((output.verdict(3), output.count(3)), ("OK", "2 workstreams, 1 archived"))

    def test_gap_living_id_also_archived(self):
        folder = self.archives(**{"WORKSTREAMS_2026-03": [block("alpha-1", status="accepted")]})
        output = self.check("--archives", folder)
        self.assertEqual(output.verdict(3), GAP)
        self.assertEqual(len(output.details(3)), 1)
        self.assertTrue(output.details(3)[0].startswith("id alpha-1 also archived (WORKSTREAMS_2026-03.yaml:"),
                        output.details(3))

    def test_gap_id_archived_twice(self):
        folder = self.archives(**{"WORKSTREAMS_2026-02": [block("beta-1", status="accepted")],
                                  "WORKSTREAMS_2026-03": [block("beta-1", status="accepted")]})
        output = self.check("--archives", folder)
        self.assertEqual(output.verdict(3), GAP)
        self.assertEqual(output.count(3), "2 workstreams, 2 archived")
        self.assertRegex(output.details(3)[0], r"^id beta-1 duplicated in the archives "
                                               r"\(WORKSTREAMS_2026-02\.yaml:\d+, WORKSTREAMS_2026-03\.yaml:\d+\)$")

    def test_without_archives_a_reused_archived_id_passes(self):
        self.archives(**{"WORKSTREAMS_2026-03": [block("alpha-1", status="accepted")]})
        self.assertEqual(self.check().verdict(3), "OK")

    def test_only_workstreams_yaml_files_are_archives(self):
        folder = self.archives(**{"OTHER": [block("alpha-1", status="accepted")]})
        output = self.check("--archives", folder)
        self.assertEqual((output.verdict(3), output.count(3)), ("OK", "2 workstreams, 0 archived"))


class TestCheck4Versions(CheckerCase):
    def test_ok(self):
        self.with_workstreams(block("alpha-1", status="accepted", version="v1.0.0"),
                              block("alpha-2", status="accepted", version="v1.1.0"),
                              block("alpha-3", status="upcoming"))
        output = self.check()
        self.assertEqual((output.verdict(4), output.count(4)), ("OK", "2 versions"))

    def test_gap_version_carried_twice(self):
        self.with_workstreams(block("alpha-1", status="accepted", version="v1.0.0"),
                              block("alpha-2", status="accepted", version="v1.0.0"))
        output = self.check()
        self.assertEqual(output.verdict(4), GAP)
        self.assertEqual(output.count(4), "1 versions")
        self.assertEqual(output.details(4), ["version v1.0.0 carried by alpha-1 and alpha-2"])

    # (b) the batch in flight carries a version higher than every other one of the same deliverable (the number of a fix)
    def test_in_flight_above_ok(self):
        self.with_workstreams(block("alpha-1", status="accepted", deliverable="App", version="v1.0009"),
                              block("alpha-2", status="in-flight", pl="Opus-PL-Alpha", deliverable="App", version="v1.0010"))
        output = self.check()
        self.assertEqual((output.verdict(4), output.count(4)), ("OK", "2 versions"))

    def test_gap_in_flight_equal_by_its_numbers(self):
        self.with_workstreams(block("alpha-1", status="accepted", deliverable="App", version="v1.0065"),
                              block("alpha-2", status="in-flight", pl="Opus-PL-Alpha", deliverable="App", version="v1.65"))
        output = self.check()
        self.assertEqual(output.verdict(4), GAP)
        self.assertEqual(output.details(4), ["alpha-2: v1.65 is not above v1.0065 (alpha-1)"])

    def test_gap_in_flight_below_names_the_highest(self):
        self.with_workstreams(block("alpha-1", status="accepted", deliverable="App", version="v1.9.0"),
                              block("alpha-2", status="to-brief", deliverable="App", version="v1.10.0"),
                              block("alpha-3", status="in-flight", pl="Opus-PL-Alpha", deliverable="App", version="v1.2.0"))
        output = self.check()
        self.assertEqual(output.verdict(4), GAP)
        self.assertEqual(output.details(4), ["alpha-3: v1.2.0 is not above v1.10.0 (alpha-2)"])

    def test_another_deliverable_is_ignored(self):
        self.with_workstreams(block("alpha-1", status="accepted", deliverable="Agent", version="agent-v2.0.0"),
                              block("alpha-2", status="in-flight", pl="Opus-PL-Alpha", deliverable="App", version="v1.0.0"))
        self.assertEqual(self.check().verdict(4), "OK")

    def test_without_deliverable_ignored(self):
        self.with_workstreams(block("alpha-1", status="accepted", version="v2.0.0"),
                              block("alpha-2", status="in-flight", pl="Opus-PL-Alpha", version="v1.0.0"),
                              block("alpha-3", status="accepted", deliverable="App", version="v3.0.0"),
                              block("alpha-4", status="in-flight", pl="Opus-PL-Alpha", deliverable="App", version="no-number"))
        self.assertEqual(self.check().verdict(4), "OK")

    def test_gap_found_in_an_archive(self):
        self.with_workstreams(block("alpha-2", status="in-flight", pl="Opus-PL-Alpha", deliverable="App", version="v1.1.0"))
        folder = self.archives(**{"WORKSTREAMS_2026-03": [block("alpha-1", status="accepted", deliverable="App",
                                                                version="v1.1.0")]})
        self.assertEqual(self.check().verdict(4), "OK", "without --archives, the archive is not read")
        output = self.check("--archives", folder)
        self.assertEqual(output.verdict(4), GAP)
        self.assertEqual(output.count(4), "1 versions")
        self.assertEqual(output.details(4), ["alpha-2: v1.1.0 is not above v1.1.0 (alpha-1)"])

    # (b) only the version token is compared (the first occurrence of [vV]?n.n[.n…] or of [vV]n)
    def test_a_value_with_a_hash_and_a_decision_number_is_not_compared(self):
        self.with_workstreams(block("alpha-1", status="accepted", deliverable="App",
                                    version="tool at public main 18a2957, no release (D188)"),
                              block("alpha-2", status="in-flight", pl="Opus-PL-Alpha", deliverable="App", version="v1.0.0"))
        self.assertEqual(self.check().verdict(4), "OK")

    def test_the_version_token_of_a_value(self):
        c = load(CHECKER, "check_living_docs_token")
        self.assertEqual(c.numbers("tool at public main 18a2957, no release (D188)"), ())
        self.assertEqual(c.numbers("v1.10 (D205)"), (1, 10))
        self.assertEqual(c.numbers("AC-V1.5.1"), (1, 5, 1))
        self.assertEqual(c.numbers("agent-v0.1.1"), (0, 1, 1))
        self.assertEqual(c.numbers("v19"), (19,))
        self.assertEqual(c.numbers("no-number"), ())

    def test_the_decision_number_of_a_value_does_not_count(self):
        # read (1, 10), not (1, 10, 205): above v1.9, below v1.11
        self.with_workstreams(block("alpha-1", status="accepted", deliverable="App", version="v1.9"),
                              block("alpha-2", status="in-flight", pl="Opus-PL-Alpha", deliverable="App", version="v1.10 (D205)"))
        self.assertEqual(self.check().verdict(4), "OK")
        self.with_workstreams(block("alpha-1", status="accepted", deliverable="App", version="v1.10.0"),
                              block("alpha-2", status="in-flight", pl="Opus-PL-Alpha", deliverable="App", version="v1.10 (D205)"))
        output = self.check()
        self.assertEqual(output.details(4), ["alpha-2: v1.10 (D205) is not above v1.10.0 (alpha-1)"])

    def test_a_token_with_an_upper_case_prefix(self):
        self.with_workstreams(block("alpha-1", status="accepted", deliverable="App", version="AC-V1.5.1"),
                              block("alpha-2", status="in-flight", pl="Opus-PL-Alpha", deliverable="App", version="AC-V1.5.0"))
        self.assertEqual(self.check().details(4), ["alpha-2: AC-V1.5.0 is not above AC-V1.5.1 (alpha-1)"])

    def test_a_token_without_a_dot(self):
        self.with_workstreams(block("alpha-1", status="accepted", deliverable="App", version="v19"),
                              block("alpha-2", status="in-flight", pl="Opus-PL-Alpha", deliverable="App", version="v20"))
        self.assertEqual(self.check().verdict(4), "OK")


class TestCheck5InFlight(CheckerCase):
    def test_ok_with_pl(self):
        self.with_workstreams(block("alpha-1", status="in-flight", pl="Opus-PL-Alpha"),
                              block("alpha-2", status="upcoming"))
        output = self.check()
        self.assertEqual((output.verdict(5), output.count(5)), ("OK", "1 in flight"))

    def test_gap_in_flight_without_pl(self):
        self.with_workstreams(block("alpha-1", status="in-flight"))
        output = self.check()
        self.assertEqual(output.verdict(5), GAP)
        self.assertEqual(output.count(5), "1 in flight")
        self.assertEqual(output.details(5), ["alpha-1 (line 3): pl missing or empty"])

    def test_gap_in_flight_with_empty_pl(self):
        self.with_workstreams(block("alpha-1", status="in-flight", pl=""))
        self.assertEqual(self.check().verdict(5), GAP)

    def test_an_entry_without_id_is_named_by_its_line(self):
        self.workstreams = self.write("workstreams.yaml", "# Workstreams — Test\n\n- title: No id\n  status: in-flight\n")
        output = self.check()
        self.assertEqual(output.verdict(5), GAP)
        self.assertEqual(output.details(5), ["(no id, line 3) (line 3): pl missing or empty"])

    def test_the_other_statuses_do_not_need_a_pl(self):
        self.with_workstreams(*(block(f"alpha-{n}", status=s) for n, s in
                                enumerate(("upcoming", "to-brief", "debt", "accepted"), start=1)))
        output = self.check()
        self.assertEqual((output.verdict(5), output.count(5)), ("OK", "0 in flight"))


class TestCheck6Board(CheckerCase):
    def setUp(self):
        super().setUp()
        self.board = self.folder / "workstreams.html"
        self.data = self.folder / "workstreams.json"
        self.regenerate()

    def regenerate(self):
        output = self.run_script(GENERATOR, self.workstreams, self.board)
        self.assertEqual(output.code, 0, output.stdout + output.stderr)

    def check_board(self):
        return self.check("--board", self.board, "--generator", GENERATOR)

    def test_ok(self):
        output = self.check_board()
        self.assertEqual(output.verdict(6), "OK", output.stdout)
        self.assertEqual(output.count(6), f"2 workstreams, page {self.board.stat().st_size} bytes and data "
                                          f"{self.data.stat().st_size} bytes identical except the date")
        self.assertEqual(output.code, 0)

    def test_ok_despite_another_date(self):
        text = self.data.read_text(encoding="utf-8")
        self.assertRegex(text, r"\d{2}/\d{2}/\d{4}")
        self.data.write_text(re.sub(r"\d{2}/\d{2}/\d{4}", "01/01/2000", text), encoding="utf-8")
        self.assertEqual(self.check_board().verdict(6), "OK")

    def test_ok_with_a_page_published_in_another_folder_under_another_name(self):
        other = self.subfolder("published")
        board = other / "board.html"
        self.assertEqual(self.run_script(GENERATOR, self.workstreams, board).code, 0)
        output = self.check("--board", board, "--generator", GENERATOR)
        self.assertEqual(output.verdict(6), "OK", output.stdout)

    def test_gap_page_out_of_sync_with_another_project(self):
        self.workstreams = self.write("workstreams.yaml", yaml(
            block("alpha-1", title="First", status="upcoming", module="module-a"),
            block("alpha-2", title="Second", status="accepted", module="module-a", version="v1.0.0"),
            header="# Workstreams — Other project"))
        output = self.check_board()
        self.assertEqual(output.verdict(6), GAP)
        self.assertEqual(output.count(6), "2 workstreams")
        details = output.details(6)
        self.assertEqual(len(details), 2, details)
        self.assertTrue(details[0].startswith("the board page differs from its regeneration (dates masked): "
                                              "first difference at byte "), details)
        self.assertTrue(details[1].startswith("the data file differs from its regeneration (dates masked): "
                                              "first difference at byte "), details)
        self.assertEqual(output.code, 1)

    def test_gap_data_out_of_sync_page_intact(self):
        self.with_workstreams(block("alpha-1", title="First", status="upcoming"),
                              block("alpha-2", title="Second", status="accepted"),
                              block("alpha-3", title="Added later", status="debt"))
        output = self.check_board()
        self.assertEqual(output.verdict(6), GAP)
        self.assertEqual(output.count(6), "3 workstreams")
        self.assertEqual(len(output.details(6)), 1, "the page is fixed: it does not differ, only the data")
        self.assertTrue(output.details(6)[0].startswith("the data file differs from its regeneration "
                                                        "(dates masked): first difference at byte "), output.details(6))
        self.assertRegex(output.details(6)[0], r"\(line \d+\); \d+ bytes against \d+ regenerated$")
        self.assertEqual(output.code, 1)

    def test_gap_data_edited_by_hand_page_intact(self):
        self.data.write_text(self.data.read_text(encoding="utf-8").replace("First", "Touched"), encoding="utf-8")
        output = self.check_board()
        self.assertEqual(output.verdict(6), GAP)
        self.assertEqual(len(output.details(6)), 1)
        self.assertTrue(output.details(6)[0].startswith("the data file differs"), output.details(6))

    def test_gap_page_edited_by_hand_data_intact(self):
        self.board.write_text(self.board.read_text(encoding="utf-8") + "<!-- touch-up -->\n", encoding="utf-8")
        output = self.check_board()
        self.assertEqual(output.verdict(6), GAP)
        self.assertEqual(len(output.details(6)), 1)
        self.assertTrue(output.details(6)[0].startswith("the board page differs"), output.details(6))

    def test_gap_data_file_missing(self):
        self.data.unlink()
        output = self.check_board()
        self.assertEqual(output.verdict(6), GAP)
        self.assertEqual(output.details(6), [f"data file missing: {self.data}"])
        self.assertEqual(output.code, 1)

    def test_gap_data_missing_and_page_edited_give_two_lines(self):
        self.data.unlink()
        self.board.write_text(self.board.read_text(encoding="utf-8") + "<!-- touch-up -->\n", encoding="utf-8")
        details = self.check_board().details(6)
        self.assertEqual(len(details), 2, details)
        self.assertTrue(details[0].startswith("data file missing: "), details)
        self.assertTrue(details[1].startswith("the board page differs"), details)

    def test_gap_generator_that_fails(self):
        fake = self.write("fake_generator.py", "import sys\nsys.exit(3)\n")
        output = self.check("--board", self.board, "--generator", fake)
        self.assertEqual(output.verdict(6), GAP)
        self.assertEqual(output.details(6), ["the generator failed (code 3): no message"])

    def test_gap_generator_that_refuses_the_source(self):
        self.with_workstreams(block("alpha-1", status="unknown-status"))
        output = self.check_board()
        self.assertEqual(output.verdict(6), GAP)
        self.assertTrue(output.details(6)[0].startswith("the generator failed (code 1): STOP: unknown status"),
                        output.details(6))

    def test_generator_that_produces_nothing(self):
        empty = self.write("empty.py", "pass\n")
        output = self.check("--board", self.board, "--generator", empty)
        self.assertEqual(output.verdict(6), GAP)
        self.assertTrue(output.details(6)[0].startswith("the generator failed (code 0)"), output.details(6))

    def test_generator_that_writes_only_the_page(self):
        only = self.write("page_only.py", "import sys\nopen(sys.argv[2], 'w').write('<html></html>')\n")
        output = self.check("--board", self.board, "--generator", only)
        self.assertEqual(output.verdict(6), GAP)
        self.assertEqual(output.details(6), ["the generator did not write the data file workstreams.json"])


class TestCheck7VersionLog(CheckerCase):
    PLAN = "# Plan\n\n| Version | Content |\n|---|---|\n| `v1.0.0` | first |\n| `v1.1.0` | second |\n"

    def setUp(self):
        super().setUp()
        self.plan = self.write("plan.md", self.PLAN)

    def check_log(self, *options):
        return self.check("--plan", self.plan, *options)

    def test_ok_version_accepted(self):
        self.with_workstreams(block("alpha-1", status="accepted", version="v1.1.0"))
        output = self.check_log()
        self.assertEqual((output.verdict(7), output.count(7)), ("OK", "last version v1.1.0"))

    def test_ok_when_the_id_contains_the_version(self):
        self.with_workstreams(block("batch-v1.1.0", status="accepted"))
        self.assertEqual(self.check_log().verdict(7), "OK")

    def test_only_the_last_version_counts(self):
        self.with_workstreams(block("alpha-1", status="accepted", version="v1.0.0"))
        output = self.check_log()
        self.assertEqual(output.verdict(7), GAP)
        self.assertEqual(output.count(7), "last version v1.1.0")

    def test_gap_no_accepted_entry(self):
        output = self.check_log()
        self.assertEqual(output.verdict(7), GAP)
        self.assertEqual(output.details(7), ["v1.1.0: no entry in status accepted carries this version"])

    def test_gap_the_entry_exists_but_is_not_accepted(self):
        self.with_workstreams(block("alpha-1", status="in-flight", pl="Opus-PL-Alpha", version="v1.1.0"))
        output = self.check_log()
        self.assertEqual(output.verdict(7), GAP)
        self.assertEqual(output.details(7), [
            "v1.1.0: no entry in status accepted carries this version",
            "alpha-1 carries it but is in status in-flight"])

    def test_gap_no_version_in_the_log(self):
        self.plan = self.write("plan.md", "# Plan\n\nnothing versioned\n")
        output = self.check_log()
        self.assertEqual(output.verdict(7), GAP)
        self.assertEqual(output.count(7), "no version")
        self.assertEqual(output.details(7), ['no line "| `v…` |" in the version log'])

    def test_with_archives_the_archived_entry_was_accepted(self):
        self.with_workstreams(block("alpha-1", status="upcoming"))
        folder = self.archives(**{"WORKSTREAMS_2026-03": [block("alpha-9", status="accepted", version="v1.1.0")]})
        self.assertEqual(self.check_log().verdict(7), GAP, "without --archives, the archived entry is invisible")
        self.assertEqual(self.check_log("--archives", folder).verdict(7), "OK")


class TestCheck8Deliverables(CheckerCase):
    def check8(self, *blocks: str):
        self.with_workstreams(*blocks)
        return self.check()

    def test_ok_a_single_batch_in_flight_per_deliverable_and_per_resource(self):
        output = self.check8(
            block("alpha-1", status="in-flight", pl="Opus-PL-Alpha", deliverable="app-x"),
            block("alpha-2", status="upcoming", deliverable="app-x"),
            block("alpha-3", status="in-flight", pl="Opus-PL-Beta", resource="machine-1"))
        self.assertEqual(output.verdict(8), "OK")
        self.assertEqual(output.count(8), "1 deliverables, 1 resources, 2 in flight, 0 waiting")

    def test_gap_two_batches_in_flight_on_a_deliverable(self):
        output = self.check8(
            block("alpha-1", status="in-flight", pl="Opus-PL-Alpha", deliverable="app-x"),
            block("alpha-2", status="in-flight", pl="Opus-PL-Beta", deliverable="app-x"))
        self.assertEqual(output.verdict(8), GAP)
        self.assertEqual(output.details(8), ["deliverable app-x: 2 batches in flight (alpha-1, alpha-2)"])
        self.assertEqual(output.count(8), "1 deliverables, 0 resources, 2 in flight, 0 waiting")

    def test_gap_two_batches_in_flight_on_a_resource(self):
        output = self.check8(
            block("alpha-1", status="in-flight", pl="Opus-PL-Alpha", resource="machine-1"),
            block("alpha-2", status="in-flight", pl="Opus-PL-Beta", resource="machine-1"))
        self.assertEqual(output.verdict(8), GAP)
        self.assertEqual(output.details(8), ["resource machine-1: 2 batches in flight (alpha-1, alpha-2)"])

    def test_a_deliverable_and_a_resource_of_the_same_name_do_not_mix(self):
        output = self.check8(
            block("alpha-1", status="in-flight", pl="Opus-PL-Alpha", deliverable="shared"),
            block("alpha-2", status="in-flight", pl="Opus-PL-Beta", resource="shared"))
        self.assertEqual(output.verdict(8), "OK")
        self.assertEqual(output.count(8), "1 deliverables, 1 resources, 2 in flight, 0 waiting")

    def test_an_entry_that_carries_both_counts_for_each_and_once_in_flight(self):
        output = self.check8(
            block("alpha-1", status="in-flight", pl="Opus-PL-Alpha", deliverable="app-x", resource="machine-1"),
            block("alpha-2", status="in-flight", pl="Opus-PL-Beta", resource="machine-1"))
        self.assertEqual(output.verdict(8), GAP)
        self.assertEqual(output.details(8), ["resource machine-1: 2 batches in flight (alpha-1, alpha-2)"])
        self.assertEqual(output.count(8), "1 deliverables, 1 resources, 2 in flight, 0 waiting")

    def test_gap_waits_for_an_id_that_does_not_exist(self):
        output = self.check8(block("alpha-1", status="upcoming", waits="unknown"))
        self.assertEqual(output.verdict(8), GAP)
        self.assertEqual(output.details(8), ["alpha-1 waits for unknown, which does not exist"])
        self.assertEqual(output.count(8), "0 deliverables, 0 resources, 0 in flight, 1 waiting")

    def test_gap_a_batch_in_flight_that_waits(self):
        output = self.check8(
            block("alpha-1", status="upcoming"),
            block("alpha-2", status="in-flight", pl="Opus-PL-Alpha", waits="alpha-1"))
        self.assertEqual(output.verdict(8), GAP)
        self.assertEqual(output.details(8), ["alpha-2 is in flight but waits for alpha-1"])

    def test_ok_a_suspended_batch_that_waits_for_an_existing_id(self):
        output = self.check8(
            block("alpha-1", status="in-flight", pl="Opus-PL-Alpha", deliverable="app-x"),
            block("alpha-2", status="upcoming", deliverable="app-x", waits="alpha-1"))
        self.assertEqual(output.verdict(8), "OK")
        self.assertEqual(output.count(8), "1 deliverables, 0 resources, 1 in flight, 1 waiting")

    def test_check_8_runs_without_any_other_option(self):
        self.with_workstreams(block("alpha-1", status="upcoming", waits="unknown"))
        output = self.run_script(CHECKER, "--workstreams", self.workstreams, "--log", self.log)
        self.assertEqual(output.verdict(8), GAP)


TEXT_CITED_IN_ZERO = "# Checkpoint\n## §0 · State\nWe are working on `alpha-1`.\n## The queue\n- nothing\n"


class CheckpointsCase(CheckerCase):
    """Two domains (alpha, beta), their checkpoints and a few workstreams; each test changes one piece."""

    def setUp(self):
        super().setUp()
        self.table = self.write("domains.yaml", TWO_DOMAINS_TABLE)
        self.write("CHECKPOINT_ALPHA.md", checkpoint("alpha-1"))
        self.write("CHECKPOINT_BETA.md", checkpoint("beta-1"))
        self.with_workstreams(block("alpha-1", status="upcoming", module="module-a"),
                              block("beta-1", status="to-brief", module="module-b"))

    def check_domains(self, *options, cwd=None):
        return self.check("--domains", self.table, "--root", self.folder, *options, cwd=cwd)


class TestCheck9Checkpoints(CheckpointsCase):
    def test_ok(self):
        output = self.check_domains()
        self.assertEqual(output.verdict(9), "OK", output.stdout)
        self.assertEqual(output.count(9), "2 domains, 0 cited closed, 0 not cited, 0 without a queue section")

    def test_default_root_the_current_folder(self):
        output = self.check("--domains", self.table, cwd=self.folder)
        self.assertEqual(output.verdict(9), "OK", output.stdout)
        output = self.check("--domains", self.table, cwd=self.subfolder("elsewhere"))
        self.assertEqual(output.verdict(9), GAP)
        self.assertIn("alpha: checkpoint not found CHECKPOINT_ALPHA.md", output.details(9))

    def test_gap_the_queue_cites_a_closed_workstream_accepted(self):
        self.with_workstreams(block("alpha-1", status="upcoming", module="module-a"),
                              block("alpha-0", status="accepted", module="module-a"),
                              block("beta-1", status="to-brief", module="module-b"))
        self.write("CHECKPOINT_ALPHA.md", checkpoint("alpha-1", "alpha-0"))
        output = self.check_domains()
        self.assertEqual(output.verdict(9), GAP)
        self.assertEqual(output.details(9), ["alpha: the queue cites alpha-0, closed (accepted)"])
        self.assertEqual(output.count(9), "2 domains, 1 cited closed, 0 not cited, 0 without a queue section")

    def test_gap_the_queue_cites_a_workstream_only_archived(self):
        folder = self.archives(**{"WORKSTREAMS_2026-03": [block("alpha-0", status="accepted")]})
        self.write("CHECKPOINT_ALPHA.md", checkpoint("alpha-1", "alpha-0"))
        self.assertEqual(self.check_domains().verdict(9), "OK", "without --archives, alpha-0 is unknown")
        output = self.check_domains("--archives", folder)
        self.assertEqual(output.verdict(9), GAP)
        self.assertEqual(output.details(9), ["alpha: the queue cites alpha-0, closed (archived)"])

    def test_a_closed_one_cited_outside_the_queue_section_does_not_count(self):
        self.with_workstreams(block("alpha-1", status="upcoming", module="module-a"),
                              block("alpha-0", status="accepted", module="module-a"),
                              block("beta-1", status="to-brief", module="module-b"))
        self.write("CHECKPOINT_ALPHA.md", checkpoint("alpha-1", history=("alpha-0",)))
        self.assertEqual(self.check_domains().verdict(9), "OK")

    def test_the_queue_section_stops_at_the_next_title(self):
        text = "# Checkpoint\n## The queue\n- `alpha-1`\n## Other\n- `alpha-0` closed, but no longer in the queue\n"
        self.write("CHECKPOINT_ALPHA.md", text)
        self.with_workstreams(block("alpha-1", status="upcoming", module="module-a"),
                              block("alpha-0", status="accepted", module="module-a"),
                              block("beta-1", status="to-brief", module="module-b"))
        self.assertEqual(self.check_domains().verdict(9), "OK")

    def test_the_queue_title_is_a_line_start(self):
        table = TWO_DOMAINS_TABLE.replace('queue: "## The queue"\n  modules: module-a', 'queue: "## §3 · The queue"\n  modules: module-a')
        self.table = self.write("domains.yaml", table)
        self.write("CHECKPOINT_ALPHA.md", "# Checkpoint\n## §3 · The queue (what comes next)\n- `alpha-1`\n")
        self.assertEqual(self.check_domains().verdict(9), "OK")

    def test_gap_an_open_one_not_cited(self):
        self.write("CHECKPOINT_ALPHA.md", checkpoint())
        output = self.check_domains()
        self.assertEqual(output.verdict(9), GAP)
        self.assertEqual(output.details(9), ["alpha: alpha-1 (upcoming) is not cited in the checkpoint"])
        self.assertEqual(output.count(9), "2 domains, 0 cited closed, 1 not cited, 0 without a queue section")

    def test_each_open_status_must_be_cited_but_not_accepted(self):
        self.with_workstreams(*(block(f"alpha-{n}", status=s, module="module-a") for n, s in
                                enumerate(("upcoming", "to-brief", "debt", "in-flight", "accepted"), start=1)),
                              block("beta-1", status="to-brief", module="module-b"))
        self.write("CHECKPOINT_ALPHA.md", checkpoint())
        output = self.check_domains()
        self.assertEqual(output.details(9), [
            "alpha: alpha-1 (upcoming) is not cited in the checkpoint",
            "alpha: alpha-2 (to-brief) is not cited in the checkpoint",
            "alpha: alpha-3 (debt) is not cited in the checkpoint",
            "alpha: alpha-4 (in-flight) is not cited in the checkpoint"])

    def test_gap_an_open_one_cited_only_outside_the_queue(self):
        """9c: the citation is looked for in the queue section, not in the whole checkpoint."""
        self.write("CHECKPOINT_ALPHA.md", TEXT_CITED_IN_ZERO)
        output = self.check_domains()
        self.assertEqual(output.verdict(9), GAP, output.stdout)
        self.assertEqual(output.details(9), ["alpha: alpha-1 (upcoming) is not cited in the checkpoint"])
        self.assertEqual(output.count(9), "2 domains, 0 cited closed, 1 not cited, 0 without a queue section")

    def test_gap_an_open_one_cited_only_in_the_history(self):
        self.write("CHECKPOINT_ALPHA.md", checkpoint(history=("alpha-1",)))
        output = self.check_domains()
        self.assertEqual(output.verdict(9), GAP)
        self.assertEqual(output.details(9), ["alpha: alpha-1 (upcoming) is not cited in the checkpoint"])

    def test_an_open_one_cited_in_the_queue_is_cited_even_if_it_is_also_cited_in_zero(self):
        self.write("CHECKPOINT_ALPHA.md", TEXT_CITED_IN_ZERO.replace("- nothing", "- `alpha-1` to do"))
        self.assertEqual(self.check_domains().verdict(9), "OK")
        self.write("CHECKPOINT_ALPHA.md", checkpoint("alpha-1"))
        self.assertEqual(self.check_domains().verdict(9), "OK")

    def test_without_a_declared_queue_section_the_citation_is_looked_for_in_the_whole_checkpoint(self):
        """The behaviour of before does not change when the table declares no queue section."""
        self.table = self.write("domains.yaml", TWO_DOMAINS_TABLE.replace('queue: "## The queue"\n  modules: module-a',
                                                                            'queue:\n  modules: module-a'))
        self.write("CHECKPOINT_ALPHA.md", TEXT_CITED_IN_ZERO)
        output = self.check_domains()
        self.assertEqual(output.details(9), ["alpha: no queue section declared (queue: empty)"])
        self.assertEqual(output.count(9), "2 domains, 0 cited closed, 0 not cited, 1 without a queue section")

    def test_the_citation_is_made_between_backticks(self):
        self.write("CHECKPOINT_ALPHA.md", "# Checkpoint\n## The queue\n- alpha-1 without backticks\n")
        output = self.check_domains()
        self.assertEqual(output.verdict(9), GAP)
        self.assertEqual(output.details(9), ["alpha: alpha-1 (upcoming) is not cited in the checkpoint"])

    def test_an_entry_with_for_is_not_a_subject(self):
        self.with_workstreams(block("alpha-1", status="upcoming", module="module-a"),
                              block("alpha-msg", status="upcoming", module="module-a", **{"for": "Opus-PL-Beta"}),
                              block("beta-1", status="to-brief", module="module-b"))
        self.assertEqual(self.check_domains().verdict(9), "OK")

    def test_gap_empty_queue_in_the_table(self):
        table = TWO_DOMAINS_TABLE.replace('queue: "## The queue"\n  modules: module-a', "queue:\n  modules: module-a")
        self.table = self.write("domains.yaml", table)
        output = self.check_domains()
        self.assertEqual(output.verdict(9), GAP)
        self.assertEqual(output.details(9), ["alpha: no queue section declared (queue: empty)"])
        self.assertEqual(output.count(9), "2 domains, 0 cited closed, 0 not cited, 1 without a queue section")

    def test_empty_queue_the_line_comes_before_the_not_cited_and_9b_does_not_apply(self):
        table = TWO_DOMAINS_TABLE.replace('queue: "## The queue"\n  modules: module-a', "queue:\n  modules: module-a")
        self.table = self.write("domains.yaml", table)
        self.with_workstreams(block("alpha-1", status="upcoming", module="module-a"),
                              block("alpha-0", status="accepted", module="module-a"),
                              block("beta-1", status="to-brief", module="module-b"))
        self.write("CHECKPOINT_ALPHA.md", checkpoint(history=("alpha-0",)))
        output = self.check_domains()
        self.assertEqual(output.details(9), [
            "alpha: no queue section declared (queue: empty)",
            "alpha: alpha-1 (upcoming) is not cited in the checkpoint"])

    def test_gap_checkpoint_not_found(self):
        (self.folder / "CHECKPOINT_BETA.md").unlink()
        output = self.check_domains()
        self.assertEqual(output.verdict(9), GAP)
        self.assertEqual(output.details(9), ["beta: checkpoint not found CHECKPOINT_BETA.md"])

    def test_gap_checkpoint_unreadable(self):
        self.write("CHECKPOINT_BETA.md", b"\xff\xfe\x00 not utf-8", binary=True)
        output = self.check_domains()
        self.assertEqual(output.verdict(9), GAP)
        self.assertEqual(output.details(9), ["beta: checkpoint unreadable CHECKPOINT_BETA.md"])

    def test_gap_queue_section_not_found(self):
        self.write("CHECKPOINT_BETA.md", "# Checkpoint\n## Something else\n- `beta-1`\n")
        output = self.check_domains()
        self.assertEqual(output.verdict(9), GAP)
        self.assertEqual(output.details(9), ["beta: queue section not found “## The queue”"])

    def test_gap_table_entry_without_checkpoint(self):
        table = TWO_DOMAINS_TABLE + "\n- domain: gamma\n  pl: Opus-PL-Gamma\n"
        self.table = self.write("domains.yaml", table)
        output = self.check_domains()
        self.assertEqual(output.verdict(9), GAP)
        self.assertEqual(output.details(9), ["entry on line 15: domain or checkpoint missing"])
        self.assertEqual(output.count(9), "3 domains, 0 cited closed, 0 not cited, 0 without a queue section")

    def test_gap_table_entry_without_domain(self):
        table = TWO_DOMAINS_TABLE + "\n- pl: Opus-PL-Gamma\n  checkpoint: CHECKPOINT_GAMMA.md\n"
        self.table = self.write("domains.yaml", table)
        output = self.check_domains()
        self.assertEqual(output.details(9), ["entry on line 15: domain or checkpoint missing"])

    def test_a_faulty_domain_is_not_checked_any_further(self):
        self.write("CHECKPOINT_BETA.md", "# Checkpoint\n## Something else\n")
        self.with_workstreams(block("beta-1", status="to-brief", module="module-b"),
                              block("alpha-1", status="upcoming", module="module-a"))
        self.write("CHECKPOINT_ALPHA.md", checkpoint())
        output = self.check_domains()
        self.assertEqual(output.details(9), [
            "alpha: alpha-1 (upcoming) is not cited in the checkpoint",
            "beta: queue section not found “## The queue”"])

    def test_assignment_to_the_domain_by_pl(self):
        self.with_workstreams(block("beta-1", status="to-brief", module="module-b"),
                              block("zzz-1", status="upcoming", pl="Opus-PL-Alpha"))
        output = self.check_domains()
        self.assertEqual(output.details(9), ["alpha: zzz-1 (upcoming) is not cited in the checkpoint"])

    def test_assignment_to_the_domain_by_prefix(self):
        self.with_workstreams(block("beta-1", status="to-brief", module="module-b"),
                              block("alpha-9", status="upcoming"))
        self.write("CHECKPOINT_ALPHA.md", checkpoint())
        output = self.check_domains()
        self.assertEqual(output.details(9), ["alpha: alpha-9 (upcoming) is not cited in the checkpoint"])

    def test_assignment_to_the_domain_by_module(self):
        self.with_workstreams(block("alpha-1", status="upcoming", module="module-a"),
                              block("zzz-1", status="to-brief", module="module-b"))
        output = self.check_domains()
        self.assertEqual(output.details(9), ["beta: zzz-1 (to-brief) is not cited in the checkpoint"])

    def test_the_pl_takes_precedence_over_the_prefix_and_the_module(self):
        self.with_workstreams(block("alpha-1", status="upcoming", module="module-a"),
                              block("alpha-2", status="upcoming", module="module-a", pl="Opus-PL-Beta"),
                              block("beta-1", status="to-brief", module="module-b"))
        self.write("CHECKPOINT_BETA.md", checkpoint("beta-1"))
        output = self.check_domains()
        self.assertEqual(output.details(9), ["beta: alpha-2 (upcoming) is not cited in the checkpoint"])

    def test_an_entry_without_domain_is_required_nowhere(self):
        self.with_workstreams(block("alpha-1", status="upcoming", module="module-a"),
                              block("beta-1", status="to-brief", module="module-b"),
                              block("zzz-1", status="upcoming", module="module-z"))
        self.assertEqual(self.check_domains().verdict(9), "OK")

    def test_modules_and_prefixes_may_be_empty(self):
        table = ("- domain: only\n  pl: Opus-PL-Alpha\n  checkpoint: CHECKPOINT_ALPHA.md\n"
                 "  queue: ## The queue\n  modules:\n")
        self.table = self.write("domains.yaml", table)
        self.with_workstreams(block("alpha-1", status="upcoming", pl="Opus-PL-Alpha"))
        output = self.check_domains()
        self.assertEqual((output.verdict(9), output.count(9)),
                         ("OK", "1 domains, 0 cited closed, 0 not cited, 0 without a queue section"))

    def test_the_checkpoint_is_read_from_the_root(self):
        sub = self.subfolder("living")
        (self.folder / "CHECKPOINT_ALPHA.md").rename(sub / "CHECKPOINT_ALPHA.md")
        (self.folder / "CHECKPOINT_BETA.md").rename(sub / "CHECKPOINT_BETA.md")
        output = self.check("--domains", self.table, "--root", sub)
        self.assertEqual(output.verdict(9), "OK")


class TestCheck10Size(CheckpointsCase):
    def checkpoint_of(self, size: int, name: str = "CHECKPOINT_ALPHA.md"):
        base = checkpoint("alpha-1").encode("utf-8")
        self.assertLess(len(base), size)
        path = self.write(name, base + b"z" * (size - len(base)), binary=True)
        self.assertEqual(path.stat().st_size, size)

    def test_ok(self):
        output = self.check_domains()
        self.assertEqual((output.verdict(10), output.count(10)), ("OK", "2 domains, 0 above 10240 bytes"))

    def test_ok_exactly_at_the_default_cap(self):
        self.checkpoint_of(10240)
        output = self.check_domains()
        self.assertEqual((output.verdict(10), output.count(10)), ("OK", "2 domains, 0 above 10240 bytes"))

    def test_gap_one_byte_above_the_default_cap(self):
        self.checkpoint_of(10241)
        output = self.check_domains()
        self.assertEqual(output.verdict(10), GAP)
        self.assertEqual(output.count(10), "2 domains, 1 above 10240 bytes")
        self.assertEqual(output.details(10), ["alpha: CHECKPOINT_ALPHA.md weighs 10241 bytes, cap 10240"])
        self.assertEqual(output.code, 1)

    def test_cap_given_by_the_option(self):
        self.checkpoint_of(200)
        output = self.check_domains("--checkpoint-cap", "199")
        self.assertEqual(output.verdict(10), GAP)
        self.assertEqual(output.count(10), "2 domains, 1 above 199 bytes")
        self.assertEqual(output.details(10), ["alpha: CHECKPOINT_ALPHA.md weighs 200 bytes, cap 199"])
        output = self.check_domains("--checkpoint-cap", "200")
        self.assertEqual(output.verdict(10), "OK")

    def test_cap_of_one_byte_every_checkpoint(self):
        output = self.check_domains("--checkpoint-cap", "1")
        self.assertEqual(output.verdict(10), GAP)
        self.assertEqual(len(output.details(10)), 2)
        self.assertEqual(output.count(10), "2 domains, 2 above 1 bytes")

    def test_the_cap_is_measured_in_bytes_not_characters(self):
        # "é" weighs two bytes: the text has one more byte than characters
        self.write("CHECKPOINT_ALPHA.md", "abcdé\n" + "## The queue\n- `alpha-1`\n")
        size = (self.folder / "CHECKPOINT_ALPHA.md").stat().st_size
        output = self.check_domains("--checkpoint-cap", str(size - 1))
        self.assertEqual(output.verdict(10), GAP)

    def test_a_checkpoint_not_found_is_ignored(self):
        (self.folder / "CHECKPOINT_BETA.md").unlink()
        output = self.check_domains("--checkpoint-cap", "1")
        self.assertEqual(output.verdict(10), GAP)
        self.assertEqual(output.details(10), ["alpha: CHECKPOINT_ALPHA.md weighs "
                                              f"{(self.folder / 'CHECKPOINT_ALPHA.md').stat().st_size} bytes, cap 1"])
        self.assertEqual(output.count(10), "2 domains, 1 above 1 bytes")

    def test_an_entry_without_checkpoint_is_not_counted(self):
        table = TWO_DOMAINS_TABLE + "\n- domain: gamma\n  pl: Opus-PL-Gamma\n"
        self.table = self.write("domains.yaml", table)
        output = self.check_domains()
        self.assertEqual((output.verdict(10), output.count(10)), ("OK", "2 domains, 0 above 10240 bytes"))

    def test_the_path_is_the_one_of_the_table(self):
        table = TWO_DOMAINS_TABLE.replace("checkpoint: CHECKPOINT_ALPHA.md", "checkpoint: sub/CHECKPOINT_ALPHA.md")
        self.table = self.write("domains.yaml", table)
        self.write("sub/CHECKPOINT_ALPHA.md", checkpoint("alpha-1") + "z" * 300)
        output = self.check_domains("--checkpoint-cap", "300")
        self.assertEqual(output.verdict(10), GAP)
        self.assertTrue(output.details(10)[0].startswith("alpha: sub/CHECKPOINT_ALPHA.md weighs "), output.details(10))


class TestCheck11Format(CheckpointsCase):
    """Check 11: every value is a safe YAML scalar (bare and safe, or between double quotes)."""

    def line_of(self, path, fragment: str) -> int:
        lines = path.read_text(encoding="utf-8").split("\n")
        return next(i for i, line in enumerate(lines, start=1) if fragment in line)

    def lines(self, *paths) -> int:
        return sum(len(p.read_text(encoding="utf-8").split("\n")) - 1 for p in paths)

    def test_ok_on_a_conforming_file(self):
        self.with_workstreams(block("alpha-1", title="A title", status="upcoming", rank="5", accepted_on="2026-10-30",
                                    basis='"text : continued, with \\" and \\\\"', cost=""),
                              block("alpha-2", status="accepted", refs="D12 · briefing - report"))
        output = self.check()
        self.assertEqual(output.verdict(11), "OK", output.stdout)
        self.assertEqual(output.count(11), f"1 files, {self.lines(self.workstreams)} lines read")
        self.assertEqual(output.details(11), [])

    def test_gap_on_a_value_that_starts_with_a_hash(self):
        """The case of the domain table: "queue: ## §1 · The queue"."""
        table = TWO_DOMAINS_TABLE.replace('queue: "## The queue"\n  modules: module-a', "queue: ## §1 · The queue\n  modules: module-a")
        self.table = self.write("domains.yaml", table)
        self.write("CHECKPOINT_ALPHA.md", checkpoint("alpha-1").replace("## The queue", "## §1 · The queue"))
        output = self.check_domains()
        self.assertEqual(output.verdict(9), "OK")
        self.assertEqual(output.verdict(11), GAP, output.stdout)
        self.assertEqual(output.details(11)[0], f"{self.table}:{self.line_of(self.table, '§1')} : key queue")
        self.assertEqual(output.count(11), "1 non-conforming value(s), 2 files, "
                                           f"{self.lines(self.workstreams, self.table)} lines read")

    def test_gap_on_a_colon_followed_by_a_space(self):
        self.with_workstreams(block("alpha-1", status="upcoming", basis="text : continued"))
        output = self.check()
        self.assertEqual(output.verdict(11), GAP)
        self.assertEqual(output.details(11)[0], f"{self.workstreams}:{self.line_of(self.workstreams, 'text : continued')} : key basis")

    def test_gap_on_a_value_that_ends_with_a_colon(self):
        self.with_workstreams(block("alpha-1", status="upcoming"), block("alpha-2", status="upcoming", title="Careful:"))
        output = self.check()
        self.assertEqual(output.verdict(11), GAP)
        self.assertEqual(output.details(11)[0], f"{self.workstreams}:{self.line_of(self.workstreams, 'Careful:')} : key title")
        self.assertEqual(output.code, 1)
        self.assertEqual(output.summary, "LIVING DOCS · 1 gap(s)")

    def test_the_detail_gives_the_command_that_normalizes(self):
        self.with_workstreams(block("alpha-1", status="upcoming", basis="a : b"))
        output = self.check()
        self.assertEqual(output.details(11)[-1],
                         f"to normalize: python3 -B archive_workstreams.py normalize --workstreams {self.workstreams}")

    def test_the_first_five_non_conforming_values_are_given_and_all_counted(self):
        self.with_workstreams(*(block(f"alpha-{n}", status="upcoming", basis=f"basis {n} : continued") for n in range(1, 8)))
        output = self.check()
        self.assertTrue(output.count(11).startswith("7 non-conforming value(s), 1 files, "), output.count(11))
        self.assertEqual(len(output.details(11)), 5 + 1, "five values, then the command")
        lines = [self.line_of(self.workstreams, f"basis {n} :") for n in range(1, 6)]
        self.assertEqual([d.split(" : ")[0] for d in output.details(11)[:5]], [f"{self.workstreams}:{n}" for n in lines])

    def test_the_archives_are_read_with_their_option_only(self):
        folder = self.archives(**{"WORKSTREAMS_2026-03": [block("old-1", status="accepted", title="Done : almost")],
                                  "WORKSTREAMS_2026-04": [block("old-2", status="accepted")]})
        without = self.check()
        self.assertEqual(without.verdict(11), "OK")
        self.assertTrue(without.count(11).startswith("1 files, "), without.count(11))
        with_ = self.check("--archives", folder)
        self.assertEqual(with_.verdict(11), GAP, with_.stdout)
        self.assertTrue(with_.count(11).startswith("1 non-conforming value(s), 3 files, "), with_.count(11))
        archive = self.folder / "archives" / "WORKSTREAMS_2026-03.yaml"
        self.assertEqual(with_.details(11)[0], f"{archive}:{self.line_of(archive, 'Done')} : key title")
        self.assertEqual(with_.details(11)[-1], "to normalize: python3 -B archive_workstreams.py normalize "
                                                f"--workstreams {self.workstreams} --archives {folder}")

    def test_the_table_is_read_with_its_option_only(self):
        self.table = self.write("domains.yaml", TWO_DOMAINS_TABLE.replace("modules: module-b", "modules: module-b : x"))
        self.assertEqual(self.check().verdict(11), "OK")
        with_ = self.check("--domains", self.table, "--root", self.folder)
        self.assertEqual(with_.verdict(11), GAP, with_.stdout)
        self.assertEqual(with_.details(11)[0], f"{self.table}:{self.line_of(self.table, 'module-b : x')} : key modules")
        self.assertEqual(with_.details(11)[-1], "to normalize: python3 -B archive_workstreams.py normalize "
                                                f"--workstreams {self.workstreams} --domains {self.table}")

    def test_the_check_does_not_change_the_others(self):
        self.with_workstreams(block("alpha-1", status="upcoming", module="module-a", basis="a : b"),
                              block("beta-1", status="to-brief", module="module-b"))
        output = self.check_domains()
        self.assertEqual([output.verdict(r) for r in range(1, 11)],
                         ["OK", "OK", "OK", "OK", "OK", NOT_REQUESTED, NOT_REQUESTED, "OK", "OK", "OK"])


def octets(text: str) -> int:
    return len(text.encode("utf-8"))


def entry_of(id: str, size: int, **keys) -> str:
    """A workstream entry that weighs exactly "size" bytes in the sense of check 12: its "basis" key is filled with "x"
    (its lines, each followed by a line break)."""
    base = block(id, **keys, basis="")
    empty = sum(octets(line) + 1 for line in base.split("\n"))
    assert size >= empty, (size, empty)
    return block(id, **keys, basis="x" * (size - empty))


def log_line(number: int, characters: int) -> str:
    """A line "| **D<n>** | … |" of exactly "characters" characters (line break excluded)."""
    start, end = f"| **D{number}** | ", " |"
    return start + "é" * (characters - len(start) - len(end)) + end


class TestCheck12Entries(CheckpointsCase):
    """The table: alpha (module-a, prefix alpha-), beta (module-b); an unknown module is "outside any domain"."""

    def setUp(self):
        super().setUp()
        self.write_log()

    def write_log(self, *lines: str):
        """A log D1 to D3 short, then the given lines (in the order given)."""
        self.log = self.write("decision_log.md", decision_log(1, 2, 3) + "".join(line + "\n" for line in lines))

    def check12(self, *options):
        output = self.check_domains(*options)
        return output.verdict(12), output.count(12), output.details(12)

    def test_without_domains_not_requested_and_nothing_else_changes(self):
        without = self.check()
        self.assertEqual(without.verdict(12), NOT_REQUESTED)
        self.assertEqual(re.findall(r"^12 entry sizes +—  not requested$", without.stdout, flags=re.M),
                         ["12 entry sizes                —  not requested"])
        self.assertEqual(without.code, 0)
        self.assertEqual(without.summary, "LIVING DOCS · no gap")
        # the line of check 12 comes after that of 11 and before the last one
        lines = without.stdout.rstrip("\n").split("\n")
        self.assertTrue(lines[-3].startswith("11 "), lines)
        self.assertTrue(lines[-2].startswith("12 "), lines)
        self.assertTrue(lines[-1].startswith("LIVING DOCS · "), lines)

    def test_ok_without_log_from_the_log_is_not_measured(self):
        self.write_log(log_line(4, 5000))
        self.assertEqual(self.check12(), ("OK", "2 open workstreams, decision log not measured, 0 above", []))

    def test_ok_with_log_from(self):
        self.assertEqual(self.check12("--log-from", "1"),
                         ("OK", "2 open workstreams, 3 decision log entries, 0 above", []))

    def test_the_cap_of_a_workstream_is_1536_bytes_strictly(self):
        self.with_workstreams(entry_of("alpha-1", 1536, status="upcoming", module="module-a"),
                              block("beta-1", status="to-brief", module="module-b"))
        self.assertEqual(self.check12()[0], "OK")
        self.with_workstreams(entry_of("alpha-1", 1537, status="upcoming", module="module-a"),
                              block("beta-1", status="to-brief", module="module-b"))
        self.assertEqual(self.check12(), (GAP, "2 open workstreams, decision log not measured, 1 above",
                                          ["alpha: workstream alpha-1 weighs 1537 bytes, cap 1536"]))

    def test_the_exit_code_counts_check_12(self):
        self.with_workstreams(entry_of("alpha-1", 1600, status="upcoming", module="module-a"),
                              block("beta-1", status="to-brief", module="module-b"))
        output = self.check_domains()
        self.assertEqual((output.code, output.summary), (1, "LIVING DOCS · 1 gap(s)"))

    def test_the_size_is_measured_in_utf_8_bytes(self):
        # every "é" weighs two bytes: 1000 characters make 2000
        text = block("alpha-1", status="upcoming", module="module-a", basis="é" * 1000)
        self.with_workstreams(text, block("beta-1", status="to-brief", module="module-b"))
        size = sum(octets(line) + 1 for line in text.split("\n"))
        self.assertGreater(size, 2000)
        self.assertEqual(self.check12()[2], [f"alpha: workstream alpha-1 weighs {size} bytes, cap 1536"])

    def test_empty_lines_and_hash_lines_do_not_count(self):
        # the 1536-byte entry, plus empty lines, an indented comment and a section banner that follows
        entry = entry_of("alpha-1", 1536, status="upcoming", module="module-a")
        lines = entry.split("\n")
        entry = "\n".join([lines[0], "", "  # a note that does not count", *lines[1:], "   "])
        text = ("# Workstreams\n\n" + entry + "\n\n# ═══════ a section ═══════\n# " + "x" * 3000 + "\n\n"
                + block("beta-1", status="to-brief", module="module-b") + "\n")
        self.workstreams = self.write("workstreams.yaml", text)
        self.assertEqual(self.check12()[0], "OK", self.check_domains().stdout)

    def test_the_last_entry_runs_to_the_end_of_the_file(self):
        self.with_workstreams(block("beta-1", status="to-brief", module="module-b"),
                              entry_of("alpha-1", 1700, status="upcoming", module="module-a"))
        self.assertEqual(self.check12()[2], ["alpha: workstream alpha-1 weighs 1700 bytes, cap 1536"])

    def test_open_statuses_are_measured_and_accepted_is_not(self):
        for status in ("upcoming", "to-brief", "debt", "in-flight"):
            with self.subTest(status=status):
                self.with_workstreams(entry_of("alpha-1", 1600, status=status, module="module-a", pl="Opus-PL-Alpha"))
                self.assertEqual(self.check12(), (GAP, "1 open workstreams, decision log not measured, 1 above",
                                                  ["alpha: workstream alpha-1 weighs 1600 bytes, cap 1536"]))
        for status in ("accepted", "other", ""):
            with self.subTest(status=status):
                self.with_workstreams(entry_of("alpha-1", 1600, status=status or None, module="module-a"))
                self.assertEqual(self.check12(), ("OK", "0 open workstreams, decision log not measured, 0 above", []))

    def test_an_open_workstream_then_accepted_the_line_disappears(self):
        self.with_workstreams(entry_of("alpha-1", 1700, status="upcoming", module="module-a"))
        self.assertEqual(len(self.check12()[2]), 1)
        self.with_workstreams(entry_of("alpha-1", 1700, status="accepted", module="module-a"))
        self.assertEqual(self.check12()[2], [])

    def test_an_arbiter_id_is_neither_measured_nor_counted(self):
        self.with_workstreams(entry_of("arbiter-c9-checkpoint-alpha-20260101", 2000, status="to-brief", module="method",
                                       **{"for": "Opus-PL-Alpha"}),
                              block("alpha-1", status="upcoming", module="module-a"))
        self.assertEqual(self.check12(), ("OK", "1 open workstreams, decision log not measured, 0 above", []))

    def test_an_id_that_contains_arbiter_without_starting_with_it_is_measured(self):
        self.with_workstreams(entry_of("alpha-arbiter-1", 2000, status="upcoming", module="module-a"))
        self.assertEqual(len(self.check12()[2]), 1)

    def test_an_entry_with_for_is_measured(self):
        self.with_workstreams(entry_of("alpha-1", 1600, status="to-brief", module="module-a", **{"for": "Opus-PL-Alpha"}))
        self.assertEqual(self.check12()[1], "1 open workstreams, decision log not measured, 1 above")

    def test_the_archives_are_not_measured(self):
        folder = self.archives(**{"WORKSTREAMS_2026-01": [entry_of("old-1", 5000, status="accepted", module="module-a")]})
        output = self.check_domains("--archives", folder)
        self.assertEqual((output.verdict(12), output.count(12)),
                         ("OK", "2 open workstreams, decision log not measured, 0 above"))

    def test_the_domain_is_read_as_in_check_9_and_the_rest_is_outside_any_domain(self):
        self.with_workstreams(
            entry_of("x-by-pl", 1600, status="upcoming", module="module-b", pl="Opus-PL-Alpha"),
            entry_of("alpha-by-prefix", 1601, status="upcoming", module="module-b"),
            entry_of("y-by-module", 1602, status="debt", module="module-b"),
            entry_of("z-orphan", 1603, status="to-brief", module="unknown"),
            entry_of("w-no-module", 1604, status="to-brief"))
        self.assertEqual(self.check12()[2], [
            "alpha: workstream x-by-pl weighs 1600 bytes, cap 1536",
            "alpha: workstream alpha-by-prefix weighs 1601 bytes, cap 1536",
            "beta: workstream y-by-module weighs 1602 bytes, cap 1536",
            "outside any domain: workstream z-orphan weighs 1603 bytes, cap 1536",
            "outside any domain: workstream w-no-module weighs 1604 bytes, cap 1536"])

    def test_an_entry_without_id_is_named_by_its_line_and_outside_any_domain(self):
        base = block("beta-1", status="to-brief", module="module-b")
        no_id = "- status: upcoming\n  basis: " + "x" * 1600
        self.with_workstreams(base, no_id)
        line = (self.folder / "workstreams.yaml").read_text(encoding="utf-8").split("\n").index("- status: upcoming") + 1
        self.assertEqual(self.check12()[2], [
            f"outside any domain: workstream (no id, line {line}) weighs {octets(no_id) + 1} bytes, cap 1536"])

    def test_workstream_lines_follow_the_file_order_then_come_those_of_the_log(self):
        self.with_workstreams(entry_of("beta-1", 1700, status="upcoming", module="module-b"),
                              entry_of("alpha-1", 1800, status="upcoming", module="module-a"))
        self.write_log(log_line(4, 900), log_line(5, 801))
        verdict, count, lines = self.check12("--log-from", "4")
        self.assertEqual((verdict, count), (GAP, "2 open workstreams, 2 decision log entries, 4 above"))
        self.assertEqual(lines, ["beta: workstream beta-1 weighs 1700 bytes, cap 1536",
                                 "alpha: workstream alpha-1 weighs 1800 bytes, cap 1536",
                                 "decision log: D4 counts 900 characters, cap 800",
                                 "decision log: D5 counts 801 characters, cap 800"])

    def test_the_workstream_cap_is_that_of_the_option(self):
        self.with_workstreams(entry_of("alpha-1", 2000, status="upcoming", module="module-a"),
                              entry_of("beta-1", 1500, status="upcoming", module="module-b"))
        self.assertEqual(self.check12("--workstream-cap", "1499")[2], [
            "alpha: workstream alpha-1 weighs 2000 bytes, cap 1499", "beta: workstream beta-1 weighs 1500 bytes, cap 1499"])
        self.assertEqual(self.check12("--workstream-cap", "1500")[2],
                         ["alpha: workstream alpha-1 weighs 2000 bytes, cap 1500"])
        self.assertEqual(self.check12("--workstream-cap", "2000")[0], "OK")

    def test_the_log_cap_is_800_characters_strictly_and_without_the_line_break(self):
        self.write_log(log_line(4, 800))
        self.assertEqual(self.check12("--log-from", "4"),
                         ("OK", "2 open workstreams, 1 decision log entries, 0 above", []))
        self.write_log(log_line(4, 801))
        self.assertEqual(self.check12("--log-from", "4"), (
            GAP, "2 open workstreams, 1 decision log entries, 1 above",
            ["decision log: D4 counts 801 characters, cap 800"]))

    def test_the_log_is_measured_in_characters_not_bytes(self):
        line = log_line(4, 700)
        self.assertGreater(octets(line), 800)
        self.write_log(line)
        self.assertEqual(self.check12("--log-from", "4")[0], "OK")

    def test_the_log_cap_is_that_of_the_option(self):
        self.write_log(log_line(4, 500), log_line(5, 1001))
        self.assertEqual(self.check12("--log-from", "4", "--log-cap", "499")[2], [
            "decision log: D4 counts 500 characters, cap 499", "decision log: D5 counts 1001 characters, cap 499"])
        self.assertEqual(self.check12("--log-from", "4", "--log-cap", "1000")[2],
                         ["decision log: D5 counts 1001 characters, cap 1000"])

    def test_only_the_entries_from_the_given_number_are_measured(self):
        self.write_log(log_line(4, 900), log_line(5, 900), log_line(6, 900))
        self.assertEqual(self.check12("--log-from", "5"), (
            GAP, "2 open workstreams, 2 decision log entries, 2 above",
            ["decision log: D5 counts 900 characters, cap 800", "decision log: D6 counts 900 characters, cap 800"]))
        self.assertEqual(self.check12("--log-from", "7"),
                         ("OK", "2 open workstreams, 0 decision log entries, 0 above", []))

    def test_a_reservation_is_neither_measured_nor_counted(self):
        self.write_log("| **D4** | *reserved by Opus-PL-Alpha, " + "x" * 2000 + "* |")
        output = self.check_domains("--log-from", "4")
        self.assertEqual((output.verdict(12), output.count(12)),
                         ("OK", "2 open workstreams, 0 decision log entries, 0 above"))
        self.assertEqual(output.verdict(2), WARNING)

    def test_lines_that_are_not_log_entries_do_not_count(self):
        self.write_log("A sentence " + "x" * 2000, "| decision without a number | " + "x" * 2000 + " |")
        self.assertEqual(self.check12("--log-from", "1")[1], "2 open workstreams, 3 decision log entries, 0 above")

    def test_a_log_entry_has_no_domain_even_if_it_names_a_pl(self):
        line = "| **D4** | " + "Opus-PL-Alpha " * 100 + " |"
        self.write_log(line)
        self.assertEqual(self.check12("--log-from", "4")[2], [
            f"decision log: D4 counts {len(line)} characters, cap 800"])

    def test_checks_1_to_11_do_not_change(self):
        with_ = self.check_domains("--log-from", "1", "--workstream-cap", "10")
        without = self.check_domains()
        self.assertEqual([(with_.verdict(r), with_.count(r), with_.details(r)) for r in range(1, 12)],
                         [(without.verdict(r), without.count(r), without.details(r)) for r in range(1, 12)])

    def test_the_docstring_describes_check_12_and_its_options(self):
        doc = load(CHECKER, "check_living_docs_doc").__doc__
        for expected in ("The twelve checks", "12. entry sizes", "--workstream-cap", "--log-cap",
                         "--log-from", "1536 by default", "800 by default"):
            self.assertIn(expected, doc)


class TestFunctions(TempCase):
    """Direct calls to the script's functions, when that is clearer than the command line."""

    @classmethod
    def setUpClass(cls):
        cls.c = load(CHECKER, "check_living_docs_under_test")

    def test_ranges(self):
        self.assertEqual(self.c.ranges([20, 25, 26, 27]), ["D20", "D25 to D27 (3 numbers)"])
        self.assertEqual(self.c.ranges([]), [])
        self.assertEqual(self.c.ranges([1, 2]), ["D1 to D2 (2 numbers)"])

    def test_read_workstreams_keeps_the_line_and_ignores_comments_and_empty_lines(self):
        path = self.write("workstreams.yaml", "# comment\n\n- id: a\n  status: debt\n# other\n  title: A title: with colons\n")
        entries = self.c.read_workstreams(path)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["id"], "a")
        self.assertEqual(entries[0]["_line"], 3)
        self.assertEqual(entries[0]["_file"], "workstreams.yaml")
        self.assertEqual(entries[0]["title"], "A title: with colons")

    def test_read_workstreams_returns_a_quoted_value_without_quotes_or_escapes(self):
        path = self.write("workstreams.yaml", '- id: a\n  title: "A \\"title\\" with \\\\ and : colons"\n  empty: ""\n')
        entry = self.c.read_workstreams(path)[0]
        self.assertEqual(entry["title"], 'A "title" with \\ and : colons')
        self.assertEqual(entry["empty"], "")

    def test_read_workstreams_reads_a_non_conforming_bare_value_as_before(self):
        path = self.write("workstreams.yaml", '- id: a\n  title: text : continued\n  open: "no end\n  mid: "a" b\n'
                                                '  end: "a\\"\n  other: "a\\n"\n  hash: ## title\n')
        entry = self.c.read_workstreams(path)[0]
        self.assertEqual((entry["title"], entry["open"], entry["mid"]), ("text : continued", '"no end', '"a" b'))
        self.assertEqual((entry["end"], entry["other"], entry["hash"]), ('"a\\"', '"a\\n"', "## title"))

    def test_read_workstreams_reads_the_domain_table_between_quotes(self):
        path = self.write("domains.yaml", '- domain: alpha\n  queue: "## §1 · The queue"\n')
        self.assertEqual(self.c.read_workstreams(path)[0]["queue"], "## §1 · The queue")

    def test_value_conforms(self):
        conforming = ["", "text", "a:b", "a#b", "5", "2026-10-30", "D12 · briefing", "x - y", "text with `code`", "à é · —",
                      'x"y"', "it's", '"x : y"', '"## title"', '"a \\" b \\\\ c"', '""', "http://example.com/a"]
        for value in conforming:
            self.assertTrue(self.c.value_conforms(value), f"conforming: {value!r}")
        non_conforming = ["a: b", "a :", "end:", "x # y", "## title", "- item", "? q", ": x", ",x", "[x]", "]x", "{x}", "}x",
                          "&x", "*x", "!x", "|x", ">x", "'x'", '"x', '"a" b', '"a\\n"', "%x", "@x", "`x`",
                          "a\tb", "a\x01b", "a\x85b", "a\u2028b"]
        for value in non_conforming:
            self.assertFalse(self.c.value_conforms(value), f"non-conforming: {value!r}")

    @NO_PYYAML
    def test_a_conforming_file_is_read_as_by_pyyaml(self):
        text = yaml(block("alpha-1", title='"A \\"title\\" : continued"', rank="5", accepted_on="2026-10-30", basis="",
                          refs="D1 · D2"),
                    block("alpha-2", title="Careful:oh", queue='"## §1 · The queue"'))
        path = self.write("workstreams.yaml", text)
        self.assertEqual(without_position(self.c.read_workstreams(path)), pyyaml_reading(text))

    def test_read_workstreams_ignores_what_precedes_the_first_entry(self):
        path = self.write("workstreams.yaml", "orphan: value\n- id: a\n")
        self.assertEqual([e["id"] for e in self.c.read_workstreams(path)], ["a"])

    def test_queue_section(self):
        text = "# T\n## The queue\none\ntwo\n## Next\nthree\n"
        self.assertEqual(self.c.queue_section(text, "## The queue"), "## The queue\none\ntwo")
        self.assertEqual(self.c.queue_section(text, "## Next"), "## Next\nthree\n")
        self.assertIsNone(self.c.queue_section(text, "## Absent"))

    def test_domain_of_first_that_fits_rule_after_rule(self):
        domains = [{"domain": "one", "pl": "X", "modules": "m1", "prefixes": "p-"},
                   {"domain": "two", "pl": "Y", "modules": "m2"}]
        domain_of = self.c.domain_of
        self.assertEqual(domain_of({"id": "p-1", "pl": "Y", "module": "m1"}, domains), "two")
        self.assertEqual(domain_of({"id": "p-1", "module": "m2"}, domains), "one")
        self.assertEqual(domain_of({"id": "q-1", "module": "m2"}, domains), "two")
        self.assertIsNone(domain_of({"id": "q-1", "module": "m3"}, domains))
        self.assertIsNone(domain_of({"id": "q-1"}, domains))

    def test_check_numbers_on_an_empty_log(self):
        path = self.write("decision_log.md", "")
        verdict, count, _ = self.c.check_numbers(path)
        self.assertEqual((verdict, count), (GAP, "no number found"))


if __name__ == "__main__":
    unittest.main()
