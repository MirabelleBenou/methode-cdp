"""Tests of context.py: the measure of the context at the last turn of the main session.

Every test builds, in a temporary folder taken as "HOME", synthetic logs under
.claude/projects/<project>/ (see test_tools.py) and runs the script on the command line.
"""
import json
import os
import unittest

from .test_tools import CONTEXT, TempCase


def usage(input=0, read=0, created=0, **others) -> dict:
    """A log line: a message with its usage counters; others: keys of the line (isSidechain…)."""
    return {"type": "assistant", "message": {"role": "assistant", "usage": {
        "input_tokens": input, "cache_read_input_tokens": read, "cache_creation_input_tokens": created,
        "output_tokens": 77}}, **others}


class ContextCase(TempCase):
    def setUp(self):
        super().setUp()
        self.home = self.subfolder("home")
        self.clock = 1_700_000_000

    def log(self, path: str, *lines, mtime=None):
        """A log under HOME/.claude/projects/<path>; a line is a dict (written as JSON) or a raw text."""
        file = self.home / ".claude" / "projects" / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text("".join((json.dumps(l) if isinstance(l, dict) else l) + "\n" for l in lines), encoding="utf-8")
        self.clock += 10
        os.utime(file, (mtime or self.clock, mtime or self.clock))
        return file

    def context(self, *arguments):
        return self.run_script(CONTEXT, *arguments, env={"HOME": str(self.home), "USERPROFILE": str(self.home)})

    @staticmethod
    def first(output) -> str:
        """The first line of the output, without its line end: the context at the last turn."""
        return output.stdout.split("\n")[0]

    def assertOneLine(self, output, fragment: str):
        """A clean failure: code 1, a single line, no Python traceback."""
        self.assertEqual(output.code, 1, output.stdout + output.stderr)
        text = (output.stdout + output.stderr).strip()
        self.assertEqual(len(text.split("\n")), 1, text)
        self.assertNotIn("Traceback", text)
        self.assertIn(fragment, text)


class TestMeasure(ContextCase):
    def test_right_measure_on_a_simple_case(self):
        self.log("p/session.jsonl", usage(10, 200, 30))
        output = self.context()
        self.assertEqual((output.code, self.first(output), output.stderr), (0, "context at the last turn: 240 tokens", ""))

    def test_the_last_turn_counts_not_the_total(self):
        self.log("p/session.jsonl", usage(1, 1000, 100), {"type": "user"}, usage(5, 4000, 300), {"type": "user"})
        self.assertEqual(self.first(self.context()), "context at the last turn: 4 305 tokens")

    def test_thousands_are_separated_by_spaces(self):
        self.log("p/session.jsonl", usage(2, 1_234_000, 565))
        self.assertEqual(self.first(self.context()), "context at the last turn: 1 234 567 tokens")

    def test_a_missing_counter_is_zero(self):
        self.log("p/session.jsonl", {"message": {"usage": {"input_tokens": 7, "cache_read_input_tokens": 3}}})
        self.assertEqual(self.first(self.context()), "context at the last turn: 10 tokens")

    def test_the_most_recent_log_is_taken(self):
        self.log("p/old.jsonl", usage(1, 1, 1))
        self.log("q/recent.jsonl", usage(2, 2, 2))
        self.assertEqual(self.first(self.context()), "context at the last turn: 6 tokens")

    def test_a_log_given_as_an_argument_wins(self):
        wanted = self.log("p/wanted.jsonl", usage(1, 1, 1))
        self.log("q/more-recent.jsonl", usage(9, 9, 9))
        self.assertEqual(self.first(self.context(wanted)), "context at the last turn: 3 tokens")

    def test_a_log_given_as_an_argument_outside_home(self):
        other = self.write("elsewhere/log.jsonl", json.dumps(usage(4, 5, 6)) + "\n")
        output = self.context(other)
        self.assertEqual((output.code, self.first(output)), (0, "context at the last turn: 15 tokens"))


class TestRobustness(ContextCase):
    def test_no_log(self):
        self.assertOneLine(self.context(), "no log")

    def test_empty_projects_folder(self):
        (self.home / ".claude" / "projects" / "p").mkdir(parents=True)
        self.assertOneLine(self.context(), "no log")

    def test_log_without_a_usage_line(self):
        self.log("p/session.jsonl", {"type": "user", "message": {"content": "hello"}}, {"type": "summary"})
        self.assertOneLine(self.context(), "no usage line")

    def test_empty_log(self):
        self.log("p/session.jsonl")
        self.assertOneLine(self.context(), "no usage line")

    def test_an_empty_usage_does_not_count(self):
        self.log("p/session.jsonl", {"message": {"usage": {}}}, {"message": {"usage": None}})
        self.assertOneLine(self.context(), "no usage line")

    def test_an_unreadable_line_is_skipped(self):
        self.log("p/session.jsonl", usage(10, 20, 30), "{this is not json", "", "[1, 2]", "null", usage(1, 2, 3),
                 "{\"truncated\": ")
        output = self.context()
        self.assertEqual((output.code, self.first(output)), (0, "context at the last turn: 6 tokens"))

    def test_an_unreadable_log_as_an_argument(self):
        missing = self.folder / "absent.jsonl"
        self.assertOneLine(self.context(missing), "unreadable")
        binary = self.write("binary.jsonl", b"\xff\xfe\x00\x01 not utf-8\n", binary=True)
        self.assertOneLine(self.context(binary), "no usage line")

    def test_a_folder_as_an_argument(self):
        self.assertOneLine(self.context(self.subfolder("a-folder")), "unreadable")


class TestMainSession(ContextCase):
    def test_a_more_recent_subagent_line_is_ignored(self):
        self.log("p/session.jsonl", usage(10, 20, 30), usage(900, 900, 900, isSidechain=True))
        self.assertEqual(self.first(self.context()), "context at the last turn: 60 tokens")

    def test_an_isSidechain_false_line_counts(self):
        self.log("p/session.jsonl", usage(10, 20, 30), usage(1, 2, 3, isSidechain=False))
        self.assertEqual(self.first(self.context()), "context at the last turn: 6 tokens")

    def test_a_log_made_only_of_subagent_lines(self):
        self.log("p/session.jsonl", usage(1, 2, 3, isSidechain=True))
        self.assertOneLine(self.context(), "no usage line")

    def test_a_file_under_subagents_is_left_out(self):
        self.log("p/main.jsonl", usage(10, 20, 30))
        self.log("subagents/agent-1.jsonl", usage(500, 500, 500))
        self.assertEqual(self.first(self.context()), "context at the last turn: 60 tokens")

    def test_only_files_under_subagents(self):
        self.log("subagents/agent-1.jsonl", usage(500, 500, 500))
        self.assertOneLine(self.context(), "no log")


class TestFixedLoad(ContextCase):
    """The first turn is the fixed load; the work is what the last turn adds to it."""

    def test_three_turns_and_a_subagent_between_them(self):
        self.log("p/session.jsonl", usage(1, 150_000, 82), usage(999_999, isSidechain=True),
                 usage(3, 183_000, 937), usage(0, 254_000, 0))
        output = self.context()
        self.assertEqual((output.code, output.stderr), (0, ""))
        self.assertEqual(output.stdout, "context at the last turn: 254 000 tokens\n"
                                        "fixed load (first turn): 150 083 tokens\n"
                                        "work above the fixed load: 103 917 tokens\n")

    def test_the_figures_of_the_brief(self):
        self.log("p/session.jsonl", usage(83, 151_000, 0), usage(999_999, 0, 0, isSidechain=True),
                 usage(940, 183_000, 0), usage(0, 254_000, 0))
        self.assertEqual(self.context().stdout, "context at the last turn: 254 000 tokens\n"
                                                "fixed load (first turn): 151 083 tokens\n"
                                                "work above the fixed load: 102 917 tokens\n")

    def test_a_single_turn_gives_a_work_of_zero(self):
        self.log("p/session.jsonl", usage(10, 200, 30))
        self.assertEqual(self.context().stdout, "context at the last turn: 240 tokens\n"
                                                "fixed load (first turn): 240 tokens\n"
                                                "work above the fixed load: 0 tokens\n")

    def test_the_first_turn_skips_a_leading_subagent_and_an_unreadable_line(self):
        self.log("p/session.jsonl", usage(900, 900, 900, isSidechain=True), "{unreadable", usage(1, 2, 3),
                 usage(4, 5, 6))
        self.assertEqual(self.context().stdout, "context at the last turn: 15 tokens\n"
                                                "fixed load (first turn): 6 tokens\n"
                                                "work above the fixed load: 9 tokens\n")

    def test_the_fixed_load_takes_the_same_thousands_separators(self):
        self.log("p/session.jsonl", usage(2, 1_234_000, 565), usage(0, 2_000_000, 0))
        self.assertEqual(self.context().stdout, "context at the last turn: 2 000 000 tokens\n"
                                                "fixed load (first turn): 1 234 567 tokens\n"
                                                "work above the fixed load: 765 433 tokens\n")


class TestCompaction(ContextCase):
    def test_no_mark_no_mention(self):
        self.log("p/session.jsonl", usage(1, 2, 3))
        self.assertNotIn("compaction", self.context().stdout)

    def test_the_isCompactSummary_mark_is_reported(self):
        self.log("p/session.jsonl", usage(1, 2, 3), {"type": "user", "isCompactSummary": True}, usage(4, 5, 6))
        output = self.context()
        self.assertEqual(output.code, 0)
        self.assertEqual(output.stdout, "context at the last turn: 15 tokens\n"
                                        "fixed load (first turn): 6 tokens\n"
                                        "work above the fixed load: 9 tokens\n"
                                        "compaction seen: the measure is of the compacted context\n")

    def test_the_compact_boundary_mark_is_reported(self):
        self.log("p/session.jsonl", {"type": "system", "subtype": "compact_boundary"}, usage(4, 5, 6))
        self.assertEqual(self.context().stdout, "context at the last turn: 15 tokens\n"
                                                "fixed load (first turn): 15 tokens\n"
                                                "work above the fixed load: 0 tokens\n"
                                                "compaction seen: the measure is of the compacted context\n")

    def test_a_subagent_mark_is_not_reported(self):
        self.log("p/session.jsonl", usage(4, 5, 6), {"isCompactSummary": True, "isSidechain": True})
        self.assertNotIn("compaction", self.context().stdout)

    def test_isCompactSummary_false_is_not_a_mark(self):
        self.log("p/session.jsonl", usage(4, 5, 6), {"isCompactSummary": False, "subtype": "other"})
        self.assertNotIn("compaction", self.context().stdout)


if __name__ == "__main__":
    unittest.main()
