"""Tests of archive_workstreams.py: date, move out, lose nothing, search; the invalid calls.

Every test builds its fixtures in a temporary folder (see test_tools.py) and calls the script on the
command line with "--date", so that days are counted without depending on the clock.
"""
import re
import unittest
from collections import Counter

from .test_tools import ARCHIVER, TempCase, block, load, yaml

TODAY = "2026-03-15"            # today's date for the tests
SEVEN_DAYS_AGO = "2026-03-08"
SIX_DAYS_AGO = "2026-03-09"


def non_empty(text: str) -> Counter:
    return Counter(line for line in text.split("\n") if line.strip())


class ArchiverCase(TempCase):
    def setUp(self):
        super().setUp()
        self.archives_folder = self.subfolder("archives")
        self.archive = self.archives_folder / "WORKSTREAMS_2026-03.yaml"

    def write_workstreams(self, *blocks: str, header: str = "# Workstreams — Test") -> str:
        self.workstreams = self.write("workstreams.yaml", yaml(*blocks, header=header))
        return self.workstreams.read_text(encoding="utf-8")

    def read_workstreams(self) -> str:
        return self.workstreams.read_bytes().decode("utf-8")

    def archive_run(self, *options, date=TODAY):
        arguments = ["archive", "--workstreams", self.workstreams, "--archives", self.archives_folder]
        if date:
            arguments += ["--date", date]
        return self.run_script(ARCHIVER, *arguments, *options)

    def search(self, pattern, *options):
        return self.run_script(ARCHIVER, "search", pattern, "--workstreams", self.workstreams,
                               "--archives", self.archives_folder, *options)


class TestDate(ArchiverCase):
    def test_an_accepted_entry_without_a_date_is_dated_right_after_its_status(self):
        self.write_workstreams(block("alpha-1", title="First", status="accepted", module="module-a"))
        output = self.archive_run()
        self.assertEqual(output.code, 0, output.stdout + output.stderr)
        self.assertEqual(self.read_workstreams(), yaml(
            "- id: alpha-1\n  title: First\n  status: accepted\n  accepted-on: 2026-03-15\n  module: module-a"))
        self.assertEqual(output.stdout, "archive · 1 dated, 0 date(s) removed, 0 archived\n")
        self.assertFalse(self.archive.exists(), "an entry dated in this very run does not leave")

    def test_the_other_statuses_are_not_dated(self):
        before = self.write_workstreams(*(block(f"alpha-{n}", status=s) for n, s in
                                          enumerate(("upcoming", "to-brief", "in-flight", "debt"), start=1)))
        output = self.archive_run()
        self.assertEqual(output.code, 0)
        self.assertEqual(self.read_workstreams(), before)
        self.assertEqual(output.stdout, "archive · 0 dated, 0 date(s) removed, 0 archived\n")

    def test_undate_a_reopened_entry(self):
        self.write_workstreams(block("alpha-1", status="in-flight", accepted_on=SIX_DAYS_AGO, pl="Opus-PL-Alpha"))
        output = self.archive_run()
        self.assertEqual(output.code, 0)
        self.assertEqual(self.read_workstreams(), yaml(block("alpha-1", status="in-flight", pl="Opus-PL-Alpha")))
        self.assertEqual(output.stdout, "archive · 0 dated, 1 date(s) removed, 0 archived\n")

    def test_date_and_undate_in_the_same_run(self):
        self.write_workstreams(block("alpha-1", status="accepted"),
                               block("alpha-2", status="debt", accepted_on=SEVEN_DAYS_AGO))
        output = self.archive_run()
        self.assertEqual(output.stdout, "archive · 1 dated, 1 date(s) removed, 0 archived\n")
        self.assertEqual(self.read_workstreams(), yaml(block("alpha-1", status="accepted", accepted_on=TODAY),
                                                       block("alpha-2", status="debt")))

    def test_the_default_date_is_the_clock_s(self):
        from datetime import date
        self.write_workstreams(block("alpha-1", status="accepted"))
        before = date.today().isoformat()
        output = self.archive_run(date=None)
        after = date.today().isoformat()  # the day may have changed during the call: either date will do
        self.assertEqual(output.code, 0)
        self.assertTrue(any(f"  accepted-on: {day}\n" in self.read_workstreams() for day in {before, after}),
                        self.read_workstreams())

    def test_windows_line_ending_kept(self):
        text = "# Workstreams — Test\r\n\r\n- id: alpha-1\r\n  status: accepted\r\n"
        self.workstreams = self.write("workstreams.yaml", text)
        self.archive_run()
        self.assertEqual(self.read_workstreams(),
                         "# Workstreams — Test\r\n\r\n- id: alpha-1\r\n  status: accepted\r\n  accepted-on: 2026-03-15\r\n")

    def test_file_without_a_final_line_ending_kept(self):
        self.workstreams = self.write("workstreams.yaml", "- id: alpha-1\n  status: accepted")
        self.archive_run()
        self.assertEqual(self.read_workstreams(), "- id: alpha-1\n  status: accepted\n  accepted-on: 2026-03-15")


class TestMoveOut(ArchiverCase):
    def test_seven_days_leaves_six_days_stays(self):
        self.write_workstreams(block("alpha-1", status="accepted", accepted_on=SEVEN_DAYS_AGO),
                               block("alpha-2", status="accepted", accepted_on=SIX_DAYS_AGO))
        output = self.archive_run()
        self.assertEqual(output.code, 0, output.stdout + output.stderr)
        self.assertEqual(self.read_workstreams(), yaml(block("alpha-2", status="accepted", accepted_on=SIX_DAYS_AGO)))
        archive = self.archive.read_text(encoding="utf-8")
        self.assertIn("- id: alpha-1\n", archive)
        self.assertNotIn("alpha-2", archive)
        self.assertEqual(output.stdout.split("\n")[0],
                         f"archive · 0 dated, 0 date(s) removed, 1 archived to {self.archive}")
        self.assertEqual(output.stdout.split("\n")[1:], ["  alpha-1", ""])

    def test_the_default_delay_is_seven_days(self):
        self.write_workstreams(block("alpha-1", status="accepted", accepted_on="2026-03-08"),
                               block("alpha-2", status="accepted", accepted_on="2026-03-09"),
                               block("alpha-3", status="accepted", accepted_on="2026-03-01"))
        self.archive_run()
        remaining = self.read_workstreams()
        self.assertNotIn("alpha-1", remaining)
        self.assertIn("alpha-2", remaining)
        self.assertNotIn("alpha-3", remaining)

    def test_the_archive_is_the_one_of_the_month_of_the_day_with_its_header(self):
        self.write_workstreams(block("alpha-1", status="accepted", accepted_on="2026-03-20"))
        output = self.archive_run(date="2026-04-02")
        self.assertEqual(output.code, 0, output.stdout + output.stderr)
        archive = self.archives_folder / "WORKSTREAMS_2026-04.yaml"
        self.assertTrue(archive.is_file())
        text = archive.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("# Archived workstreams — April 2026\n"), text)
        self.assertIn("at least 7 days", text)
        self.assertTrue(text.endswith("\n\n- id: alpha-1\n  status: accepted\n  accepted-on: 2026-03-20\n"), text)
        self.assertEqual([p.name for p in self.archives_folder.iterdir()], ["WORKSTREAMS_2026-04.yaml"])

    def test_the_month_name_in_the_header(self):
        months = ["January", "February", "March", "April", "May", "June", "July", "August",
                  "September", "October", "November", "December"]
        for number, name in enumerate(months, start=1):
            with self.subTest(month=name):
                folder = self.subfolder(f"archives-{number}")
                self.write_workstreams(block("alpha-1", status="accepted", accepted_on="2025-01-01"))
                self.run_script(ARCHIVER, "archive", "--workstreams", self.workstreams, "--archives", folder,
                                "--date", f"2026-{number:02d}-10")
                text = (folder / f"WORKSTREAMS_2026-{number:02d}.yaml").read_text(encoding="utf-8")
                self.assertTrue(text.startswith(f"# Archived workstreams — {name} 2026\n"), text)

    def test_delay_given_by_the_option(self):
        self.write_workstreams(block("alpha-1", status="accepted", accepted_on="2026-03-12"),
                               block("alpha-2", status="accepted", accepted_on="2026-03-13"))
        output = self.archive_run("--delay", "3")
        self.assertEqual(output.code, 0, output.stdout + output.stderr)
        remaining = self.read_workstreams()
        self.assertNotIn("alpha-1", remaining)
        self.assertIn("alpha-2", remaining)
        self.assertIn("at least 3 days", self.archive.read_text(encoding="utf-8"))

    def test_a_longer_delay_keeps_an_entry_that_would_leave_by_default(self):
        before = self.write_workstreams(block("alpha-1", status="accepted", accepted_on="2026-03-01"))
        output = self.archive_run("--delay", "30")
        self.assertEqual(output.stdout, "archive · 0 dated, 0 date(s) removed, 0 archived\n")
        self.assertEqual(self.read_workstreams(), before)
        self.assertFalse(self.archive.exists())

    def test_delay_zero_moves_out_an_entry_dated_today_but_not_one_dated_in_this_run(self):
        self.write_workstreams(block("alpha-1", status="accepted", accepted_on=TODAY),
                               block("alpha-2", status="accepted"))
        output = self.archive_run("--delay", "0")
        self.assertEqual(output.code, 0, output.stdout + output.stderr)
        self.assertEqual(self.read_workstreams(), yaml(block("alpha-2", status="accepted", accepted_on=TODAY)))
        self.assertIn("- id: alpha-1\n", self.archive.read_text(encoding="utf-8"))
        self.assertEqual(output.stdout.split("\n")[0].split(" to ")[0], "archive · 1 dated, 0 date(s) removed, 1 archived")

    def test_only_accepted_entries_leave(self):
        before = self.write_workstreams(block("alpha-1", status="debt", accepted_on=SEVEN_DAYS_AGO))
        self.archive_run()
        self.assertNotEqual(self.read_workstreams(), before, "the date of an entry that is not accepted is removed")
        self.assertFalse(self.archive.exists())

    def test_several_entries_leave_in_the_order_of_the_file(self):
        self.write_workstreams(block("alpha-1", status="accepted", accepted_on="2026-03-01"),
                               block("alpha-2", status="upcoming"),
                               block("alpha-3", status="accepted", accepted_on="2026-02-01"))
        output = self.archive_run()
        self.assertEqual(output.stdout.split("\n")[1:], ["  alpha-1", "  alpha-3", ""])
        archive = self.archive.read_text(encoding="utf-8")
        self.assertEqual(re.findall(r"^- id: (\S+)$", archive, flags=re.M), ["alpha-1", "alpha-3"])
        self.assertTrue(archive.endswith(
            "- id: alpha-1\n  status: accepted\n  accepted-on: 2026-03-01\n\n"
            "- id: alpha-3\n  status: accepted\n  accepted-on: 2026-02-01\n"))

    def test_each_entry_moved_out_is_found_in_the_archive_and_no_longer_in_workstreams(self):
        ids = [f"alpha-{n}" for n in range(1, 6)]
        self.write_workstreams(*(block(i, title=f"Title of {i}", status="accepted", accepted_on="2026-03-01",
                                       module="module-a") for i in ids))
        self.archive_run()
        archive = self.archive.read_text(encoding="utf-8")
        for i in ids:
            self.assertEqual(archive.count(f"- id: {i}\n"), 1, i)
            self.assertNotIn(i, self.read_workstreams())

    def test_removal_in_the_middle_at_the_head_and_at_the_end_never_leaves_two_empty_lines(self):
        old = block("old", status="accepted", accepted_on="2026-03-01")
        a = block("alpha-1", status="upcoming")
        b = block("alpha-2", status="debt")
        for name, blocks, rest in (("middle", (a, old, b), (a, b)),
                                   ("head", (old, a, b), (a, b)),
                                   ("end", (a, b, old), (a, b)),
                                   ("alone", (old,), ())):
            with self.subTest(position=name):
                self.write_workstreams(*blocks)
                self.archive_run()
                text = self.read_workstreams()
                self.assertNotIn("\n\n\n", text)
                if rest:
                    self.assertEqual(text, yaml(*rest))
                else:
                    self.assertNotIn("- id:", text)
                self.archive.unlink()

    def test_comments_and_empty_lines_between_blocks_are_never_touched(self):
        text = ("# Workstreams — Test\n# label: module-a = Module Alpha\n\n"
                "# --- delivered batches ---\n"
                "- id: old\n  status: accepted\n  accepted-on: 2026-03-01\n\n"
                "# --- upcoming batches ---\n"
                "- id: alpha-1\n  status: upcoming\n")
        self.workstreams = self.write("workstreams.yaml", text)
        self.archive_run()
        self.assertEqual(self.read_workstreams(), "# Workstreams — Test\n# label: module-a = Module Alpha\n\n"
                                                  "# --- delivered batches ---\n\n"
                                                  "# --- upcoming batches ---\n"
                                                  "- id: alpha-1\n  status: upcoming\n")

    def test_the_block_leaves_as_is_with_all_its_keys(self):
        entry = block("alpha-1", title="A title: with colons", status="accepted", accepted_on="2026-03-01",
                      module="module-a", basis="a < b & c", version="v1.0.0")
        self.write_workstreams(entry)
        self.archive_run()
        self.assertTrue(self.archive.read_text(encoding="utf-8").endswith("\n\n" + entry + "\n"))


class TestDryRun(ArchiverCase):
    def test_dry_run_writes_nothing_and_says_what_would_be_done(self):
        before = self.write_workstreams(block("alpha-1", status="accepted", accepted_on="2026-03-01"),
                                        block("alpha-2", status="accepted"),
                                        block("alpha-3", status="debt", accepted_on="2026-03-01"))
        output = self.archive_run("--dry-run")
        self.assertEqual(output.code, 0, output.stdout + output.stderr)
        self.assertEqual(self.read_workstreams(), before)
        self.assertEqual(list(self.archives_folder.iterdir()), [])
        self.assertEqual(output.stdout.split("\n")[0].split(" to ")[0],
                         "archive · 1 dated, 1 date(s) removed, 1 archived")
        self.assertIn("  alpha-1", output.stdout)

    def test_dry_run_does_not_touch_an_existing_archive(self):
        existing = "# Archives\n\n" + block("alpha-0", status="accepted", accepted_on="2026-02-01") + "\n"
        self.archive.write_text(existing, encoding="utf-8")
        before = self.write_workstreams(block("alpha-1", status="accepted", accepted_on="2026-03-01"))
        self.archive_run("--dry-run")
        self.assertEqual(self.archive.read_text(encoding="utf-8"), existing)
        self.assertEqual(self.read_workstreams(), before)

    def test_dry_run_and_real_run_announce_the_same_thing(self):
        self.write_workstreams(block("alpha-1", status="accepted", accepted_on="2026-03-01"),
                               block("alpha-2", status="accepted"))
        dry = self.archive_run("--dry-run")
        real = self.archive_run()
        self.assertEqual(dry.stdout, real.stdout)


class TestIdempotence(ArchiverCase):
    def test_a_second_run_at_the_same_date_changes_nothing(self):
        self.write_workstreams(block("alpha-1", status="accepted", accepted_on="2026-03-01"),
                               block("alpha-2", status="accepted"),
                               block("alpha-3", status="debt", accepted_on="2026-03-01"),
                               block("alpha-4", status="upcoming"))
        first = self.archive_run()
        self.assertEqual(first.code, 0, first.stdout + first.stderr)
        workstreams, archive = self.workstreams.read_bytes(), self.archive.read_bytes()
        second = self.archive_run()
        self.assertEqual(second.code, 0)
        self.assertEqual(second.stdout, "archive · 0 dated, 0 date(s) removed, 0 archived\n")
        self.assertEqual(self.workstreams.read_bytes(), workstreams)
        self.assertEqual(self.archive.read_bytes(), archive)

    def test_nothing_is_rewritten_when_nothing_changes(self):
        self.write_workstreams(block("alpha-1", status="upcoming"))
        self.workstreams.chmod(0o644)
        before = self.workstreams.stat().st_mtime_ns
        self.archive_run()
        self.assertEqual(self.workstreams.stat().st_mtime_ns, before)


class TestNoLineLost(ArchiverCase):
    def test_workstreams_plus_archive_equal_the_before(self):
        before = self.write_workstreams(
            block("alpha-1", title="First", status="accepted", accepted_on="2026-03-01", module="module-a"),
            block("alpha-2", title="Second", status="accepted", module="module-a"),
            block("alpha-3", title="Third", status="in-flight", accepted_on="2026-03-02", pl="Opus-PL-Alpha"),
            block("alpha-4", title="Fourth", status="accepted", accepted_on=SIX_DAYS_AGO),
            block("alpha-5", title="Fifth", status="accepted", accepted_on=SEVEN_DAYS_AGO, version="v1.0.0"),
            block("alpha-6", title="Sixth", status="to-brief"))
        output = self.archive_run()
        self.assertEqual(output.code, 0, output.stdout + output.stderr)
        after = self.read_workstreams()
        addition = self.archive.read_text(encoding="utf-8").split("\n\n", 1)[1]  # after the header
        expected = non_empty(before)
        expected["  accepted-on: 2026-03-15"] += 1      # alpha-2, dated in this run
        expected["  accepted-on: 2026-03-02"] -= 1      # alpha-3, reopened, undated
        self.assertEqual(+expected, non_empty(after) + non_empty(addition))

    def test_no_line_lost_with_comments_and_empty_lines_at_the_head_and_the_end(self):
        before = ("\n# Workstreams — Test\n\n\n# note\n"
                  "- id: alpha-1\n  status: accepted\n  accepted-on: 2026-03-01\n"
                  "# note between two blocks\n\n\n"
                  "- id: alpha-2\n  status: debt\n\n\n")
        self.workstreams = self.write("workstreams.yaml", before)
        self.archive_run()
        addition = self.archive.read_text(encoding="utf-8").split("\n\n", 1)[1]
        self.assertEqual(non_empty(before), non_empty(self.read_workstreams()) + non_empty(addition))


class TestMonthArchive(ArchiverCase):
    def test_the_existing_archive_receives_the_addition_without_being_rewritten(self):
        existing = "# Archives\n\n" + block("alpha-0", status="accepted", accepted_on="2026-03-01") + "\n"
        self.archive.write_text(existing, encoding="utf-8")
        self.write_workstreams(block("alpha-1", status="accepted", accepted_on="2026-03-02"))
        output = self.archive_run()
        self.assertEqual(output.code, 0, output.stdout + output.stderr)
        new = block("alpha-1", status="accepted", accepted_on="2026-03-02") + "\n"
        self.assertEqual(self.archive.read_text(encoding="utf-8"), existing + "\n" + new)

    def test_the_existing_archive_without_a_line_ending_still_gets_an_empty_line(self):
        existing = "# Archives\n\n- id: alpha-0\n  status: accepted"
        self.archive.write_text(existing, encoding="utf-8")
        self.write_workstreams(block("alpha-1", status="accepted", accepted_on="2026-03-02"))
        self.archive_run()
        self.assertEqual(self.archive.read_text(encoding="utf-8"),
                         existing + "\n\n- id: alpha-1\n  status: accepted\n  accepted-on: 2026-03-02\n")

    def test_the_archive_that_ends_with_an_empty_line_does_not_get_one_more(self):
        existing = "# Archives\n\n- id: alpha-0\n  status: accepted\n\n"
        self.archive.write_text(existing, encoding="utf-8")
        self.write_workstreams(block("alpha-1", status="accepted", accepted_on="2026-03-02"))
        self.archive_run()
        self.assertEqual(self.archive.read_text(encoding="utf-8"),
                         existing + "- id: alpha-1\n  status: accepted\n  accepted-on: 2026-03-02\n")

    def test_two_successive_runs_accumulate_in_the_same_archive(self):
        self.write_workstreams(block("alpha-1", status="accepted", accepted_on="2026-03-01"))
        self.archive_run(date="2026-03-10")
        self.write_workstreams(block("alpha-2", status="accepted", accepted_on="2026-03-02"))
        self.archive_run(date="2026-03-20")
        archive = self.archive.read_text(encoding="utf-8")
        self.assertEqual(re.findall(r"^- id: (\S+)$", archive, flags=re.M), ["alpha-1", "alpha-2"])
        self.assertEqual(archive.count("# Archived workstreams"), 1, "the header is only written at creation")

    def test_the_archives_of_another_month_are_not_touched(self):
        other = self.archives_folder / "WORKSTREAMS_2026-02.yaml"
        other.write_text("# February\n\n- id: alpha-0\n  status: accepted\n", encoding="utf-8")
        self.write_workstreams(block("alpha-1", status="accepted", accepted_on="2026-03-01"))
        self.archive_run()
        self.assertEqual(other.read_text(encoding="utf-8"), "# February\n\n- id: alpha-0\n  status: accepted\n")


class TestUnreadableDate(ArchiverCase):
    def test_an_unreadable_date_gives_code_1_a_warning_and_leaves_the_entry(self):
        before = self.write_workstreams(block("alpha-1", status="accepted", accepted_on="not-a-date"))
        output = self.archive_run()
        self.assertEqual(output.code, 1)
        self.assertIn("id alpha-1: unreadable accepted-on “not-a-date”", output.stdout)
        self.assertEqual(self.read_workstreams(), before)
        self.assertFalse(self.archive.exists())

    def test_the_refused_date_forms(self):
        for value in ("15/03/2026", "2026-02-30", "2026-13-01", "2026-3-1", "", "2026-03-01x"):
            with self.subTest(value=value):
                before = self.write_workstreams(block("alpha-1", status="accepted", accepted_on=value))
                output = self.archive_run()
                self.assertEqual(output.code, 1, output.stdout)
                self.assertIn(f"unreadable accepted-on “{value}”", output.stdout)
                self.assertEqual(self.read_workstreams(), before)

    def test_the_other_entries_are_processed_despite_the_warning(self):
        self.write_workstreams(block("alpha-1", status="accepted", accepted_on="not-a-date"),
                               block("alpha-2", status="accepted", accepted_on="2026-03-01"),
                               block("alpha-3", status="accepted"))
        output = self.archive_run()
        self.assertEqual(output.code, 1)
        remaining = self.read_workstreams()
        self.assertIn("alpha-1", remaining)
        self.assertNotIn("alpha-2", remaining)
        self.assertIn("accepted-on: 2026-03-15", remaining)
        self.assertIn("- id: alpha-2\n", self.archive.read_text(encoding="utf-8"))

    def test_an_entry_that_is_not_accepted_with_an_unreadable_date_is_simply_undated(self):
        self.write_workstreams(block("alpha-1", status="debt", accepted_on="not-a-date"))
        output = self.archive_run()
        self.assertEqual(output.code, 0)
        self.assertEqual(self.read_workstreams(), yaml(block("alpha-1", status="debt")))


class TestSearch(ArchiverCase):
    def setUp(self):
        super().setUp()
        self.write_workstreams(block("alpha-1", title="First batch", status="upcoming", module="module-a"),
                               block("alpha-2", title="Second batch", status="debt", module="module-b"))
        self.archive.write_text(
            "# Archives\n\n" + block("beta-1", title="Old workstream", status="accepted", accepted_on="2026-03-01") + "\n",
            encoding="utf-8")

    def test_a_living_id_gives_that_single_workstream_and_its_block(self):
        output = self.search("alpha-1")
        self.assertEqual(output.code, 0, output.stdout + output.stderr)
        lines = output.stdout.split("\n")
        self.assertEqual(lines[0], f"{self.workstreams}:3 · alpha-1 · upcoming · First batch")
        self.assertEqual(lines[1:-2], ["- id: alpha-1", "  title: First batch", "  status: upcoming", "  module: module-a"])
        self.assertEqual(lines[-2], "search · 1 found")

    def test_an_archived_id_is_found_in_the_archive(self):
        output = self.search("beta-1")
        self.assertEqual(output.code, 0)
        self.assertTrue(output.stdout.startswith(f"{self.archive}:3 · beta-1 · accepted · Old workstream\n"), output.stdout)
        self.assertIn("  accepted-on: 2026-03-01", output.stdout)
        self.assertIn("search · 1 found", output.stdout)

    def test_a_pattern_is_looked_for_case_insensitively_in_the_id_and_the_title(self):
        output = self.search("OLD")
        self.assertEqual(output.code, 0)
        self.assertIn("beta-1 · accepted · Old workstream", output.stdout)
        output = self.search("second")
        self.assertIn("alpha-2 · debt · Second batch", output.stdout)

    def test_several_results_one_line_each_without_a_block(self):
        output = self.search("batch")
        self.assertEqual(output.code, 0)
        self.assertEqual(len(output.stdout.strip().split("\n")), 3, "two entry lines and the total")
        self.assertNotIn("- id:", output.stdout)
        self.assertTrue(output.stdout.endswith("search · 2 found\n"))

    def test_results_in_the_order_workstreams_then_archives(self):
        self.write_workstreams(block("alpha-1", title="A batch", status="upcoming"))
        (self.archives_folder / "WORKSTREAMS_2026-02.yaml").write_text(
            "# A\n\n- id: zeta-1\n  title: An old batch\n  status: accepted\n", encoding="utf-8")
        output = self.search("batch")
        ids = re.findall(r" · (\S+) · ", output.stdout)
        self.assertEqual(ids, ["alpha-1", "zeta-1"])

    def test_a_pattern_equal_to_an_id_gives_that_single_workstream(self):
        self.write_workstreams(block("alpha", title="Short", status="upcoming"),
                               block("alpha-2", title="Long", status="upcoming"))
        output = self.search("alpha")
        self.assertEqual(len(re.findall(r"^\S+:\d+ · ", output.stdout, flags=re.M)), 1)
        self.assertIn("alpha · upcoming · Short", output.stdout)
        self.assertIn("search · 1 found", output.stdout)

    def test_the_id_equality_respects_the_case(self):
        self.write_workstreams(block("Alpha", title="Capital", status="upcoming"),
                               block("alpha-2", title="Lower case", status="upcoming"))
        output = self.search("alpha")
        self.assertIn("search · 2 found", output.stdout, "no exact equality: case-insensitive substring search")
        output = self.search("Alpha")
        self.assertIn("search · 1 found", output.stdout)

    def test_everywhere_looks_in_all_the_values(self):
        self.assertEqual(self.search("module-a").code, 1)
        output = self.search("module-a", "--everywhere")
        self.assertEqual(output.code, 0)
        self.assertIn("alpha-1 · upcoming · First batch", output.stdout)
        self.assertIn("search · 1 found", output.stdout)

    def test_no_result_gives_code_1(self):
        output = self.search("nothing-like-it")
        self.assertEqual(output.code, 1)
        self.assertEqual(output.stdout, "search · 0 found\n")

    def test_search_modifies_nothing(self):
        before = (self.workstreams.read_bytes(), self.archive.read_bytes())
        self.search("batch")
        self.search("beta-1")
        self.assertEqual((self.workstreams.read_bytes(), self.archive.read_bytes()), before)


class TestInvalidCalls(ArchiverCase):
    def setUp(self):
        super().setUp()
        self.write_workstreams(block("alpha-1", status="upcoming"))

    def invalid(self, output, message: str):
        self.assertEqual(output.code, 2, output.stdout + output.stderr)
        self.assertEqual(output.stdout, "")
        self.assertTrue(output.stderr.startswith("archive_workstreams: "), output.stderr)
        self.assertIn(message, output.stderr)

    def test_without_a_command(self):
        self.invalid(self.run_script(ARCHIVER), "missing argument")

    def test_unknown_command(self):
        output = self.run_script(ARCHIVER, "erase")
        self.invalid(output, "unknown command: ")
        self.assertRegex(output.stderr, r"unknown command: '?erase'? \(archive or search\)")

    def test_workstreams_missing(self):
        self.invalid(self.run_script(ARCHIVER, "archive", "--archives", self.archives_folder), "missing argument")

    def test_archives_missing(self):
        self.invalid(self.run_script(ARCHIVER, "archive", "--workstreams", self.workstreams), "missing argument")

    def test_pattern_missing(self):
        self.invalid(self.run_script(ARCHIVER, "search", "--workstreams", self.workstreams,
                                     "--archives", self.archives_folder), "missing argument")

    def test_unknown_argument(self):
        self.invalid(self.archive_run("--everywhere"), "unknown argument: --everywhere")

    def test_missing_value(self):
        self.invalid(self.run_script(ARCHIVER, "archive", "--archives", self.archives_folder, "--workstreams"),
                     "--workstreams: missing value")

    def test_workstreams_not_found(self):
        missing = self.folder / "missing.yaml"
        output = self.run_script(ARCHIVER, "archive", "--workstreams", missing, "--archives", self.archives_folder)
        self.invalid(output, f"file not found: --workstreams {missing}")

    def test_archives_folder_not_found_is_never_created(self):
        missing = self.folder / "nowhere"
        output = self.run_script(ARCHIVER, "archive", "--workstreams", self.workstreams, "--archives", missing)
        self.invalid(output, f"folder not found: --archives {missing}")
        self.assertFalse(missing.exists())

    def test_search_workstreams_not_found(self):
        missing = self.folder / "missing.yaml"
        output = self.run_script(ARCHIVER, "search", "x", "--workstreams", missing, "--archives", self.archives_folder)
        self.invalid(output, f"file not found: --workstreams {missing}")

    def test_search_archives_folder_not_found(self):
        missing = self.folder / "nowhere"
        output = self.run_script(ARCHIVER, "search", "x", "--workstreams", self.workstreams, "--archives", missing)
        self.invalid(output, f"folder not found: --archives {missing}")

    def test_invalid_date(self):
        for value in ("15/03/2026", "2026-02-30", "tomorrow"):
            with self.subTest(value=value):
                self.invalid(self.archive_run(date=value), f"--date: YYYY-MM-DD expected, got “{value}”")

    def test_negative_delay(self):
        self.invalid(self.archive_run("--delay", "-1"), "--delay: a positive number of days or zero is expected")

    def test_delay_not_an_integer(self):
        output = self.archive_run("--delay", "seven")
        self.invalid(output, "--delay: an integer is expected, got ")
        self.assertRegex(output.stderr, r"got '?seven'?")

    def test_unreadable_file(self):
        self.workstreams = self.write("workstreams.yaml", b"\xff\xfe\x00 not utf-8", binary=True)
        output = self.archive_run()
        self.assertEqual(output.code, 2)
        self.assertTrue(output.stderr.startswith("archive_workstreams: "))


class TestFunctions(TempCase):
    @classmethod
    def setUpClass(cls):
        cls.a = load(ARCHIVER, "archive_workstreams_under_test")

    def test_read_date(self):
        from datetime import date
        self.assertEqual(self.a.read_date("2026-03-15"), date(2026, 3, 15))
        for value in ("", "2026-3-15", "2026-02-30", "15/03/2026", "2026-03-15 ", "abcd-ef-gh"):
            self.assertIsNone(self.a.read_date(value), value)

    def test_find_blocks(self):
        lines = ["# t", "", "- id: a", "  status: debt", "  status: accepted", "", "- id: b", "  title: x", "free text",
                 "  module: lost"]
        blocks = self.a.find_blocks(lines)
        self.assertEqual([(b.id, b.start, b.end) for b in blocks], [("a", 2, 4 + 1), ("b", 6, 8)])
        self.assertEqual(blocks[0].value("status"), "debt", "the first occurrence of a key counts")
        self.assertEqual(blocks[1].value("module"), "", "a key line after a line out of shape is no longer in the block")
        self.assertEqual(blocks[0].line, 3)

    def test_tighten_at_most_one_empty_line_around_a_marker(self):
        self.assertEqual(self.a.tighten(["a", "", "", None, "", "b"], 0, 0), ["a", "", "b"])
        self.assertEqual(self.a.tighten(["a", "", None], 0, 0), ["a"])

    def test_reworded_rewords_the_messages_of_the_argument_parser(self):
        self.assertEqual(self.a.reworded("the following arguments are required: --workstreams"),
                         "missing argument: --workstreams")
        self.assertEqual(self.a.reworded("an unknown message"), "an unknown message")


if __name__ == "__main__":
    unittest.main()
