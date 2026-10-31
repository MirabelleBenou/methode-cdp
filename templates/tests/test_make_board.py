"""Tests of make_board.py: a page drawn from workstreams.yaml, deterministic, escaped, one column per status.

Every test builds its source in a temporary folder (see test_tools.py) and calls the script on the
command line.
"""
import re
import unittest
from datetime import date

from .test_tools import GENERATOR, TempCase, block, yaml

STATUSES = [("upcoming", "Upcoming"), ("to-brief", "To brief"), ("in-flight", "In flight"),
            ("debt", "Debt"), ("accepted", "Accepted")]
RE_DATE = re.compile(r"\d{2}/\d{2}/\d{4}")


def columns(html: str) -> dict:
    """{status: (label, total shown, [titles of the cards])} from the sections of the page."""
    found = {}
    for m in re.finditer(r'<section class="column st-(\S+?)" data-status="\S+?"><h2>(.*?)<b>(\d+)</b></h2>(.*?)</section>',
                         html, flags=re.S):
        found[m.group(1)] = (m.group(2), int(m.group(3)), re.findall(r"<h3>(.*?)</h3>", m.group(4)))
    return found


class GeneratorCase(TempCase):
    def setUp(self):
        super().setUp()
        self.html = self.folder / "workstreams.html"

    def generate(self, *blocks: str, header: str = "# Workstreams — Test", source_name: str = "workstreams.yaml"):
        self.source = self.write(source_name, yaml(*blocks, header=header))
        output = self.run_script(GENERATOR, self.source, self.html)
        self.assertEqual(output.code, 0, output.stdout + output.stderr)
        return output

    def page(self) -> str:
        return self.html.read_text(encoding="utf-8")


class TestGeneration(GeneratorCase):
    def test_the_output_summarizes_what_was_read(self):
        output = self.generate(block("alpha-1", status="upcoming"), block("alpha-2", status="debt"),
                               block("alpha-3", status="debt"))
        self.assertTrue(output.stdout.startswith("3 workstreams read · "), output.stdout)
        self.assertIn('"upcoming": 1', output.stdout)
        self.assertIn('"debt": 2', output.stdout)
        self.assertIn('"accepted": 0', output.stdout)
        self.assertTrue(output.stdout.rstrip().endswith(f"written to {self.html}"), output.stdout)

    def test_two_generations_of_the_same_source_are_identical_except_the_date(self):
        self.generate(block("alpha-1", title="First", status="upcoming", module="module-a", priority="high"),
                      block("alpha-2", title="Second", status="accepted", module="module-b", complexity="high"))
        first = self.page()
        second_output = self.folder / "second.html"
        self.assertEqual(self.run_script(GENERATOR, self.source, second_output).code, 0)
        second = second_output.read_text(encoding="utf-8")
        self.assertEqual(RE_DATE.sub("<date>", first), RE_DATE.sub("<date>", second))
        self.assertEqual(len(RE_DATE.findall(first)), 1)

    def test_the_page_is_dated_with_the_day(self):
        self.generate(block("alpha-1", status="upcoming"))
        self.assertIn(f"generated on {date.today().strftime('%d/%m/%Y')}", self.page())

    def test_the_page_is_a_complete_html_document(self):
        self.generate(block("alpha-1", status="upcoming"))
        page = self.page()
        self.assertTrue(page.startswith("<!doctype html>"))
        self.assertTrue(page.rstrip().endswith("</html>"))
        for marker in ("%PROJECT%", "%COLUMNS%", "%CHIPS%", "%DATE%", "%TOTAL%", "%DEBTS%"):
            self.assertNotIn(marker, page)

    def test_each_status_has_its_column_in_the_order_of_the_method(self):
        self.generate(*(block(f"alpha-{n}", title=f"Title {status}", status=status)
                        for n, (status, _) in enumerate(STATUSES, start=1)))
        found = columns(self.page())
        self.assertEqual(list(found), [status for status, _ in STATUSES])
        for status, label in STATUSES:
            self.assertEqual(found[status], (label, 1, [f"Title {status}"]), status)

    def test_a_column_without_entries_is_shown_empty(self):
        self.generate(block("alpha-1", title="Alone", status="debt"))
        found = columns(self.page())
        self.assertEqual(len(found), 5)
        self.assertEqual(found["debt"], ("Debt", 1, ["Alone"]))
        for status in ("upcoming", "to-brief", "in-flight", "accepted"):
            self.assertEqual(found[status][1:], (0, []), status)

    def test_the_cards_go_in_the_column_of_their_status(self):
        self.generate(block("alpha-1", title="One", status="in-flight", pl="Opus-PL-Alpha"),
                      block("alpha-2", title="Two", status="in-flight", pl="Opus-PL-Alpha"),
                      block("alpha-3", title="Three", status="to-brief"))
        found = columns(self.page())
        self.assertEqual(found["in-flight"][1:], (2, ["One", "Two"]))
        self.assertEqual(found["to-brief"][1:], (1, ["Three"]))

    def test_a_card_without_a_title_carries_its_id(self):
        self.generate(block("alpha-1", status="upcoming"))
        self.assertEqual(columns(self.page())["upcoming"][2], ["alpha-1"])

    def test_sorted_by_rank_then_file_order(self):
        self.generate(block("a", title="No rank", status="upcoming"),
                      block("b", title="Rank 2", status="upcoming", rank="2"),
                      block("c", title="Rank 1", status="upcoming", rank="1"),
                      block("d", title="No rank bis", status="upcoming"))
        self.assertEqual(columns(self.page())["upcoming"][2], ["Rank 1", "Rank 2", "No rank", "No rank bis"])

    def test_an_added_entry_appears(self):
        self.generate(block("alpha-1", title="First", status="upcoming"))
        before = self.page()
        self.assertNotIn("Added afterwards", before)
        self.assertIn('<b id="count">1</b>', before)
        output = self.generate(block("alpha-1", title="First", status="upcoming"),
                               block("alpha-2", title="Added afterwards", status="debt"))
        after = self.page()
        self.assertTrue(output.stdout.startswith("2 workstreams read"))
        self.assertEqual(columns(after)["debt"][1:], (1, ["Added afterwards"]))
        self.assertIn('<b id="count">2</b>', after)
        self.assertIn("entries shown out of 2 · 1 in debt", after)

    def test_the_count_of_debts_is_in_the_header(self):
        self.generate(block("alpha-1", status="debt"), block("alpha-2", status="debt"), block("alpha-3", status="upcoming"))
        self.assertIn("entries shown out of 3 · 2 in debt", self.page())

    def test_the_source_is_read_again_at_every_generation(self):
        self.generate(block("alpha-1", title="Old title", status="upcoming"))
        self.generate(block("alpha-1", title="New title", status="upcoming"))
        self.assertNotIn("Old title", self.page())
        self.assertIn("New title", self.page())


class TestEscaping(GeneratorCase):
    def test_a_title_with_html_characters_comes_out_escaped(self):
        self.generate(block("alpha-1", title="Title <b>bold</b> & more", status="upcoming"))
        page = self.page()
        self.assertIn("<h3>Title &lt;b&gt;bold&lt;/b&gt; &amp; more</h3>", page)
        self.assertNotIn("<b>bold</b>", page)
        self.assertNotIn("& more", page)

    def test_the_less_than_character_alone_is_escaped(self):
        self.generate(block("alpha-1", title="a<b", status="upcoming"))
        page = self.page()
        self.assertIn("<h3>a&lt;b</h3>", page)
        self.assertNotIn("<h3>a<b", page)

    def test_the_other_fields_of_the_card_are_escaped(self):
        self.generate(block("alpha-1", title="T", status="upcoming", basis="<script>alert(1)</script>",
                            cost="cost < 5 & > 2", refs="R<1>", category="a&b", module="mod<x>"))
        page = self.page()
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", page)
        self.assertNotIn("<script>alert(1)", page)
        self.assertIn("cost &lt; 5 &amp; &gt; 2", page)
        self.assertIn('<span class="ref">R&lt;1&gt;</span>', page)
        self.assertIn('<span class="cat">A&amp;b</span>', page)
        self.assertIn('data-mod="mod&lt;x&gt;"', page)

    def test_a_quote_in_an_attribute_is_escaped(self):
        self.generate(block("alpha-1", title="T", status="upcoming", module='x"y'))
        page = self.page()
        self.assertIn('data-mod="x&quot;y"', page)
        self.assertNotIn('data-mod="x"y"', page)

    def test_the_project_name_is_escaped(self):
        self.generate(block("alpha-1", status="upcoming"), header="# Workstreams — Test & <Co> · more")
        page = self.page()
        self.assertIn("<title>Workstreams Test &amp; &lt;Co&gt;</title>", page)
        self.assertNotIn("<Co>", page)

    def test_the_labels_are_escaped(self):
        self.generate(block("alpha-1", status="upcoming", module="module-a"),
                      header="# Workstreams — Test\n# label: module-a = Module <A> & Co")
        page = self.page()
        self.assertIn("Module &lt;A&gt; &amp; Co", page)
        self.assertNotIn("Module <A>", page)


class TestHeaderAndLabels(GeneratorCase):
    def test_the_title_comes_from_the_first_line(self):
        self.generate(block("alpha-1", status="upcoming"), header="# Workstreams — Witness Project · something else")
        page = self.page()
        self.assertIn("<title>Workstreams Witness Project</title>", page)
        self.assertIn("<h1>Workstreams — Witness Project</h1>", page)

    def test_without_a_title_it_is_the_name_of_the_source_folder(self):
        self.generate(block("alpha-1", status="upcoming"), header="# No title here", source_name="untitled-project/workstreams.yaml")
        self.assertIn("<title>Workstreams untitled-project</title>", self.page())

    def test_label_given_by_the_header(self):
        self.generate(block("alpha-1", status="upcoming", module="module-a", category="doc"),
                      header="# Workstreams — Test\n# label: module-a = Module Alpha\n# label: doc = Notices")
        page = self.page()
        self.assertIn('<span class="mod">Module Alpha</span>', page)
        self.assertIn('<span class="cat">Notices</span>', page)
        self.assertIn("Module Alpha<b>1</b>", page, "the filter carries the label too")

    def test_default_label(self):
        self.generate(block("alpha-1", status="upcoming", module="module-a", category="tooling"),
                      block("alpha-2", status="upcoming", module="screen"))
        page = self.page()
        self.assertIn('<span class="mod">Module a</span>', page, "dashes as spaces, first letter capitalized")
        self.assertIn('<span class="cat">Tooling</span>', page)
        self.assertIn('<span class="mod">Screen</span>', page)

    def test_priority_and_complexity_by_default_and_given(self):
        self.generate(block("alpha-1", status="upcoming"),
                      block("alpha-2", status="upcoming", priority="high", complexity="high"),
                      block("alpha-3", status="upcoming", priority="low", complexity="low"))
        page = self.page()
        self.assertIn('class="card pr-medium" data-mod="" data-pr="medium" data-cx="medium"', page)
        self.assertIn('class="card pr-high" data-mod="" data-pr="high" data-cx="high"', page)
        self.assertIn('class="card pr-low" data-mod="" data-pr="low" data-cx="low"', page)
        for dots in ('">●●●</span>', '">●●</span>', '">●</span>'):
            self.assertIn(dots, page)

    def test_the_filters_only_offer_the_values_present(self):
        self.generate(block("alpha-1", status="upcoming", module="module-a", priority="high"),
                      block("alpha-2", status="debt", module="module-b", priority="high"))
        page = self.page()
        self.assertIn('data-field="mod" data-val="module-a"', page)
        self.assertIn('data-field="mod" data-val="module-b"', page)
        self.assertIn('data-field="pr" data-val="high"', page)
        self.assertNotIn('data-field="pr" data-val="low"', page)
        self.assertIn('data-field="st" data-val="debt"', page)
        self.assertNotIn('data-field="st" data-val="accepted"', page)


class TestRefusals(GeneratorCase):
    def refuses(self, text: str, message: str):
        self.source = self.write("workstreams.yaml", text)
        output = self.run_script(GENERATOR, self.source, self.html)
        self.assertNotEqual(output.code, 0, output.stdout)
        self.assertIn(message, output.stderr)
        self.assertFalse(self.html.exists(), "no page is written")

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


if __name__ == "__main__":
    unittest.main()
