"""Tests of make_board.py: a fixed page and a data file drawn from workstreams.yaml, deterministic.

The page holds no workstream data; the workstreams are in the .json file written next to it. Every
test builds its source in a temporary folder (see test_tools.py) and calls the script on the command
line. The JavaScript of the page does not run here (standard library only): the tests read the data
in the JSON and check the page as a text.
"""
import json
import re
import unittest
from datetime import date

from .test_tools import GENERATOR, TempCase, block, yaml

STATUSES = [("upcoming", "Upcoming"), ("to-brief", "To brief"), ("in-flight", "In flight"),
            ("debt", "Debt"), ("accepted", "Accepted")]
RE_DATE = re.compile(r"\d{2}/\d{2}/\d{4}")
DEFAULT_LABELS = {"screen": "Screen", "data": "Data", "doc": "Documentation", "tooling": "Tooling",
                  "engine": "Engine", "operations": "Operations", "core": "Core"}


def constant(page: str, name: str):
    """The JSON value of a constant "const NAME = …;" of the script of the page."""
    m = re.search(rf"^const {name} = (.*);$", page, flags=re.M)
    assert m, f"constant {name} missing from the page"
    return json.loads(m.group(1))


class GeneratorCase(TempCase):
    def setUp(self):
        super().setUp()
        self.html = self.folder / "workstreams.html"
        self.json = self.folder / "workstreams.json"

    def generate(self, *blocks: str, header: str = "# Workstreams — Test", source_name: str = "workstreams.yaml"):
        self.source = self.write(source_name, yaml(*blocks, header=header))
        output = self.run_script(GENERATOR, self.source, self.html)
        self.assertEqual(output.code, 0, output.stdout + output.stderr)
        return output

    def page(self) -> str:
        return self.html.read_text(encoding="utf-8")

    def data_text(self) -> str:
        return self.json.read_text(encoding="utf-8")

    def data(self) -> dict:
        return json.loads(self.data_text())

    def workstreams(self) -> list:
        return self.data()["workstreams"]


class TestGeneration(GeneratorCase):
    def test_the_output_summarizes_what_was_read(self):
        output = self.generate(block("alpha-1", status="upcoming"), block("alpha-2", status="debt"),
                               block("alpha-3", status="debt"))
        self.assertTrue(output.stdout.startswith("3 workstreams read · "), output.stdout)
        self.assertIn('"upcoming": 1', output.stdout)
        self.assertIn('"debt": 2', output.stdout)
        self.assertIn('"accepted": 0', output.stdout)
        self.assertTrue(output.stdout.rstrip().endswith(f"written to {self.html} and {self.json}"), output.stdout)

    def test_two_files_are_written_and_the_second_has_the_same_name_in_json(self):
        self.generate(block("alpha-1", status="upcoming"))
        self.assertTrue(self.html.is_file())
        self.assertTrue(self.json.is_file())
        self.assertEqual(sorted(p.name for p in self.folder.iterdir()),
                         ["workstreams.html", "workstreams.json", "workstreams.yaml"])

    def test_the_data_file_is_put_next_to_the_page_under_its_name(self):
        source = self.write("workstreams.yaml", yaml(block("alpha-1", status="upcoming")))
        (self.folder / "x").mkdir()
        output = self.run_script(GENERATOR, source, self.folder / "x" / "board.html")
        self.assertEqual(output.code, 0, output.stdout + output.stderr)
        self.assertEqual(sorted(p.name for p in (self.folder / "x").iterdir()), ["board.html", "board.json"])
        self.assertTrue(output.stdout.rstrip().endswith(
            f"written to {self.folder / 'x' / 'board.html'} and {self.folder / 'x' / 'board.json'}"), output.stdout)
        self.assertIn('"board.json"', (self.folder / "x" / "board.html").read_text(encoding="utf-8"))

    def test_two_generations_of_the_same_source_are_identical_except_the_date(self):
        self.generate(block("alpha-1", title="First", status="upcoming", module="module-a", priority="high"),
                      block("alpha-2", title="Second", status="accepted", module="module-b", complexity="high"))
        first, first_data = self.page(), self.data_text()
        second_page = self.folder / "second.html"
        self.assertEqual(self.run_script(GENERATOR, self.source, second_page).code, 0)
        second = second_page.read_text(encoding="utf-8")
        second_data = (self.folder / "second.json").read_text(encoding="utf-8")
        self.assertEqual(RE_DATE.sub("<date>", first_data), RE_DATE.sub("<date>", second_data))
        self.assertEqual(len(RE_DATE.findall(first_data)), 1)
        # the page holds no date; it differs only by the name of the data file
        self.assertEqual(RE_DATE.findall(first), [])
        self.assertEqual(first.replace("workstreams.json", "second.json"), second)

    def test_the_data_is_dated_with_the_day(self):
        before = date.today().strftime("%d/%m/%Y")
        self.generate(block("alpha-1", status="upcoming"))
        after = date.today().strftime("%d/%m/%Y")  # the day may have changed during the call
        self.assertIn(self.data()["generated"], {before, after})

    def test_the_page_is_a_complete_html_document(self):
        self.generate(block("alpha-1", status="upcoming"))
        page = self.page()
        self.assertTrue(page.startswith("<!doctype html>"))
        self.assertTrue(page.rstrip().endswith("</html>"))
        for marker in ("%PROJECT%", "%DATA%", "%STATUSES%", "%PRIORITIES%", "%COMPLEXITIES%"):
            self.assertNotIn(marker, page)

    def test_the_page_is_the_same_for_two_sources_with_the_same_header(self):
        self.generate(block("alpha-1", title="First", status="upcoming", module="module-a"))
        first = self.page()
        self.generate(block("beta-1", title="Other", status="debt", module="module-z", priority="high"),
                      block("beta-2", title="Again", status="accepted"), block("beta-3", status="in-flight", pl="X"))
        self.assertEqual(self.page(), first)

    def test_the_page_holds_no_workstream_data(self):
        self.generate(block("zeta-one", title="Unique title", status="upcoming", module="module-q", basis="Rare basis",
                            cost="Rare cost", refs="RARE-REF", rank="3", category="doc"),
                      block("zeta-two", title="Other title", status="debt"), block("zeta-three", status="accepted"))
        page = self.page()
        for value in ("zeta-one", "Unique title", "module-q", "Rare basis", "Rare cost", "RARE-REF",
                      "zeta-two", "Other title", "zeta-three"):
            self.assertNotIn(value, page)

    def test_the_page_depends_only_on_the_project_name(self):
        self.generate(block("alpha-1", status="upcoming"), header="# Workstreams — Project One · more\n# label: x = Y")
        one = self.page()
        self.generate(block("beta-1", status="debt"), header="# Workstreams — Project One · any other text")
        self.assertEqual(self.page(), one)
        self.generate(block("alpha-1", status="upcoming"), header="# Workstreams — Project Two")
        self.assertNotEqual(self.page(), one)

    def test_the_page_does_not_contain_innerhtml(self):
        self.generate(block("alpha-1", title="First", status="upcoming"))
        self.assertNotIn("innerHTML", self.page())
        self.assertNotIn("insertAdjacentHTML", self.page())
        self.assertNotIn("document.write", self.page())

    def test_the_page_builds_the_dom_with_createelement_and_textcontent(self):
        self.generate(block("alpha-1", status="upcoming"))
        page = self.page()
        self.assertIn("document.createElement(", page)
        self.assertIn(".textContent", page)

    def test_the_page_contains_the_name_of_the_data_file_and_reads_it_with_fetch(self):
        self.generate(block("alpha-1", status="upcoming"))
        page = self.page()
        self.assertEqual(constant(page, "DATA_NAME"), "workstreams.json")
        self.assertIn("fetch(DATA_NAME", page)

    def test_the_page_shows_a_visible_failure_when_the_data_is_missing(self):
        self.generate(block("alpha-1", status="upcoming"))
        page = self.page()
        self.assertIn('"Cannot load " + DATA_NAME + " ("', page)
        self.assertIn(".catch(", page)

    def test_the_page_carries_the_statuses_priorities_and_complexities_of_the_method(self):
        self.generate(block("alpha-1", status="upcoming"))
        page = self.page()
        self.assertEqual(constant(page, "STATUSES"), [list(x) for x in STATUSES])
        self.assertEqual([v for v, _ in constant(page, "PRIORITIES")], ["high", "medium", "low"])
        self.assertEqual([v for v, _ in constant(page, "COMPLEXITIES")], ["high", "medium", "low"])

    def test_the_page_prevents_horizontal_overflow_on_a_phone(self):
        self.generate(block("alpha-1", status="upcoming"))
        css = re.search(r"<style>(.*?)</style>", self.page(), flags=re.S).group(1)
        self.assertRegex(css, r"(?m)^\.column\{[^}]*min-width:0[;}]")
        self.assertRegex(css, r"(?m)^\.card\{[^}]*overflow-wrap:anywhere[;}]")

    def test_the_page_carries_the_light_and_dark_themes(self):
        self.generate(block("alpha-1", status="upcoming"))
        page = self.page()
        self.assertIn("--bg:#EFE9DC;", page)
        self.assertIn("@media (prefers-color-scheme:dark)", page)
        self.assertIn(':root[data-theme="dark"]', page)

    def test_the_data_file_has_its_four_keys_in_order(self):
        self.generate(block("alpha-1", status="upcoming"))
        data = self.data()
        self.assertEqual(list(data), ["project", "generated", "labels", "workstreams"])
        self.assertEqual(data["project"], "Test")
        self.assertRegex(data["generated"], r"^\d{2}/\d{2}/\d{4}$")

    def test_the_data_file_is_utf8_indented_with_a_final_newline(self):
        self.generate(block("alpha-1", title="Élan à l'île", status="upcoming"))
        raw = self.json.read_bytes()
        self.assertTrue(raw.endswith(b"}\n"))
        text = raw.decode("utf-8")
        self.assertIn("Élan à l'île", text, "accents are written as they are, not as \\u00c9")
        self.assertIn('\n "project": "Test",\n', text, "indent=1")
        self.assertEqual(text, json.dumps(json.loads(text), ensure_ascii=False, indent=1) + "\n")

    def test_the_entries_are_in_the_order_of_the_file_without_sorting_or_filtering(self):
        ids = ["zeta", "alpha", "mu", "beta", "omega"]
        statuses = ["accepted", "debt", "upcoming", "in-flight", "to-brief"]
        self.generate(*(block(i, status=s, pl="X" if s == "in-flight" else None, rank=str(n))
                        for n, (i, s) in enumerate(zip(ids, statuses), start=1)))
        self.assertEqual([w["id"] for w in self.workstreams()], ids)

    def test_every_entry_keeps_all_its_keys_as_read(self):
        self.generate(block("alpha-1", title="First", status="in-flight", pl="Opus-PL-Alpha", module="module-a",
                            category="doc", priority="high", complexity="high", rank="2", basis="A basis",
                            cost="2 days", refs="R1 R2", version="v1.0.0", deliverable="repo", waits="alpha-2"),
                      block("alpha-2", status="upcoming", unknown_key="value"))
        first, second = self.workstreams()
        self.assertEqual(first, {"id": "alpha-1", "title": "First", "status": "in-flight", "pl": "Opus-PL-Alpha",
                                 "module": "module-a", "category": "doc", "priority": "high", "complexity": "high",
                                 "rank": "2", "basis": "A basis", "cost": "2 days", "refs": "R1 R2",
                                 "version": "v1.0.0", "deliverable": "repo", "waits": "alpha-2"})
        self.assertEqual(list(first), ["id", "title", "status", "pl", "module", "category", "priority", "complexity",
                                       "rank", "basis", "cost", "refs", "version", "deliverable", "waits"])
        self.assertEqual(second, {"id": "alpha-2", "status": "upcoming", "unknown-key": "value"})
        for entry in (first, second):
            self.assertTrue(all(isinstance(v, str) for v in entry.values()), entry)

    def test_the_default_labels_are_in_the_data(self):
        self.generate(block("alpha-1", status="upcoming"))
        self.assertEqual(self.data()["labels"], DEFAULT_LABELS)

    def test_the_labels_of_the_header_are_added_to_the_defaults_and_replace_them(self):
        self.generate(block("alpha-1", status="upcoming", module="module-a", category="doc"),
                      header="# Workstreams — Test\n# label: module-a = Module Alpha\n# label: doc = Notices")
        labels = self.data()["labels"]
        self.assertEqual(labels["module-a"], "Module Alpha")
        self.assertEqual(labels["doc"], "Notices")
        self.assertEqual(labels["screen"], "Screen")
        self.assertEqual(list(labels), list(DEFAULT_LABELS) + ["module-a"])

    def test_an_added_entry_appears_in_the_data(self):
        self.generate(block("alpha-1", title="First", status="upcoming"))
        self.assertEqual([w["id"] for w in self.workstreams()], ["alpha-1"])
        output = self.generate(block("alpha-1", title="First", status="upcoming"),
                               block("alpha-2", title="Added later", status="debt"))
        self.assertTrue(output.stdout.startswith("2 workstreams read"))
        self.assertEqual([w["title"] for w in self.workstreams() if w["status"] == "debt"], ["Added later"])
        self.assertNotIn("Added later", self.page())

    def test_the_source_is_re_read_at_every_generation(self):
        self.generate(block("alpha-1", title="Old title", status="upcoming"))
        self.generate(block("alpha-1", title="New title", status="upcoming"))
        self.assertNotIn("Old title", self.data_text())
        self.assertIn("New title", self.data_text())


class TestEscaping(GeneratorCase):
    def test_the_project_name_is_escaped_in_the_page(self):
        self.generate(block("alpha-1", status="upcoming"), header="# Workstreams — Test & <Co> · more")
        page = self.page()
        self.assertIn("<title>Workstreams Test &amp; &lt;Co&gt;</title>", page)
        self.assertIn("<h1>Workstreams — Test &amp; &lt;Co&gt;</h1>", page)
        self.assertNotIn("<Co>", page)
        self.assertEqual(self.data()["project"], "Test & <Co>", "the JSON carries the value read, without HTML escaping")

    def test_a_project_name_that_looks_like_a_marker_is_not_substituted(self):
        self.generate(block("alpha-1", status="upcoming"), header="# Workstreams — %DATA% %STATUSES% · more")
        page = self.page()
        self.assertIn("<title>Workstreams %DATA% %STATUSES%</title>", page)
        self.assertEqual(constant(page, "DATA_NAME"), "workstreams.json")

    def test_values_with_html_characters_are_in_the_json_as_they_are_and_absent_from_the_page(self):
        self.generate(block("alpha-1", title="Title <b>bold</b> & more", status="upcoming",
                            basis="<script>alert(1)</script>", cost="cost < 5 & > 2", refs="R<1>",
                            category="a&b", module='x"y'))
        entry = self.workstreams()[0]
        self.assertEqual(entry["title"], "Title <b>bold</b> & more")
        self.assertEqual(entry["basis"], "<script>alert(1)</script>")
        self.assertEqual(entry["module"], 'x"y')
        page = self.page()
        for value in ("<b>bold</b>", "alert(1)", "cost < 5", "R<1>", "a&b"):
            self.assertNotIn(value, page)

    def test_the_json_cannot_close_a_script_of_the_page(self):
        self.generate(block("alpha-1", title="</script><b>x</b>", status="upcoming"))
        self.assertNotIn("</script><b>", self.page())
        self.assertEqual(self.workstreams()[0]["title"], "</script><b>x</b>")


class TestHeader(GeneratorCase):
    def test_the_title_comes_from_the_first_line(self):
        self.generate(block("alpha-1", status="upcoming"), header="# Workstreams — Witness Project · something else")
        page = self.page()
        self.assertIn("<title>Workstreams Witness Project</title>", page)
        self.assertIn("<h1>Workstreams — Witness Project</h1>", page)
        self.assertEqual(self.data()["project"], "Witness Project")

    def test_without_a_title_it_is_the_name_of_the_source_folder(self):
        self.generate(block("alpha-1", status="upcoming"), header="# No title here", source_name="project-without-title/workstreams.yaml")
        self.assertIn("<title>Workstreams project-without-title</title>", self.page())
        self.assertEqual(self.data()["project"], "project-without-title")


class TestRefusals(GeneratorCase):
    def refuses(self, text: str, message: str):
        self.source = self.write("workstreams.yaml", text)
        output = self.run_script(GENERATOR, self.source, self.html)
        self.assertNotEqual(output.code, 0, output.stdout)
        self.assertIn(message, output.stderr)
        self.assertFalse(self.html.exists(), "no page is written")
        self.assertFalse(self.json.exists(), "no data file is written")

    def test_unknown_status(self):
        self.refuses(yaml(block("alpha-1", status="finished")), "STOP: unknown status ['finished'].")

    def test_unknown_priority(self):
        self.refuses(yaml(block("alpha-1", status="debt", priority="urgent")), "STOP: unknown priority ['urgent'].")

    def test_unknown_complexity(self):
        self.refuses(yaml(block("alpha-1", status="debt", complexity="enormous")), "STOP: unknown complexity ['enormous'].")

    def test_entry_without_status(self):
        self.refuses(yaml(block("alpha-1")), "STOP: 1 entry(ies) without id or without status.")

    def test_entry_without_id(self):
        self.refuses("# Workstreams — Test\n\n- title: No id\n  status: debt\n", "STOP: 1 entry(ies) without id or without status.")

    def test_duplicate_id(self):
        self.refuses(yaml(block("alpha-1", status="debt"), block("alpha-1", status="upcoming")),
                     "STOP: duplicate id ['alpha-1'].")

    def test_wrong_number_of_arguments(self):
        for arguments in ((), ("only.yaml",), ("a.yaml", "b.html", "c")):
            with self.subTest(arguments=arguments):
                output = self.run_script(GENERATOR, *arguments)
                self.assertNotEqual(output.code, 0)
                self.assertIn("usage: make_board.py <workstreams.yaml> <workstreams.html>", output.stderr)

    def test_source_not_found(self):
        output = self.run_script(GENERATOR, self.folder / "missing.yaml", self.html)
        self.assertNotEqual(output.code, 0)
        self.assertFalse(self.html.exists())
        self.assertFalse(self.json.exists())

    def test_a_page_that_would_carry_the_data_extension_is_refused(self):
        self.source = self.write("workstreams.yaml", yaml(block("alpha-1", status="debt")))
        output = self.run_script(GENERATOR, self.source, self.folder / "board.json")
        self.assertNotEqual(output.code, 0)
        self.assertIn("STOP: the page cannot have the .json extension", output.stderr)
        self.assertFalse((self.folder / "board.json").exists())


if __name__ == "__main__":
    unittest.main()
