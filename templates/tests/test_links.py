"""Links test: every relative link of every Markdown document of the package leads to a file that exists.

The test reads all the `.md` files under the package root (two levels above this file: the `en/` folder of the private
repository, or the root of the public copy), outside code blocks and inline code. A link to an address (`https:`,
`mailto:`) or a bare anchor (`#…`) is not relative: it is not checked. A link that starts with “/” is not relative
either: it is an error. No dependency.

Run from the repository root:
    python3 -B -m unittest discover -s en/templates/tests -t .
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RE_LINK = re.compile(r"\[[^\]\n]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
RE_INLINE_CODE = re.compile(r"`[^`\n]*`")
RE_ADDRESS = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")


def documents(root: Path = ROOT) -> list[Path]:
    """All the .md files under the root, sorted; the .git folder is left out."""
    return sorted(p for p in root.rglob("*.md") if ".git" not in p.relative_to(root).parts)


def links(path: Path) -> list[tuple[int, str]]:
    """The links (line number, target) of a document, outside code blocks and inline code."""
    found, in_block = [], False
    for number, line in enumerate(path.read_text(encoding="utf-8").split("\n"), 1):
        if line.lstrip().startswith("```"):
            in_block = not in_block
            continue
        if in_block:
            continue
        codes = [(m.start(), m.end()) for m in RE_INLINE_CODE.finditer(line)]
        for m in RE_LINK.finditer(line):
            if any(start < m.start() < end for start, end in codes):
                continue
            found.append((number, m.group(1)))
    return found


def gaps(root: Path = ROOT) -> list[str]:
    """One line per relative link that leads nowhere; empty if everything is right."""
    errors = []
    for path in documents(root):
        for number, target in links(path):
            if target.startswith("#") or RE_ADDRESS.match(target):
                continue
            name = path.relative_to(root)
            if target.startswith("/"):
                errors.append(f"{name}:{number}: non-relative link “{target}”")
                continue
            file = (path.parent / target.split("#", 1)[0]).resolve()
            if not file.exists():
                errors.append(f"{name}:{number}: “{target}” does not exist")
    return errors


class LinksCase(unittest.TestCase):
    def test_the_package_holds_documents_and_links(self):
        docs = documents()
        self.assertGreater(len(docs), 5, "no document found: is the root wrong?")
        self.assertTrue(any(links(d) for d in docs), "no link found: the test would be empty")

    def test_every_relative_link_leads_to_a_file_that_exists(self):
        errors = gaps()
        self.assertEqual(errors, [], "\n" + "\n".join(errors))

    def test_the_test_sees_a_dead_link(self):
        import tempfile
        with tempfile.TemporaryDirectory() as t:
            folder = Path(t)
            (folder / "a.md").write_text(
                "[ok](b.md) [dead](c.md#x) [web](https://example.org) `[code](d.md)`\n```\n[block](e.md)\n```\n",
                encoding="utf-8")
            (folder / "b.md").write_text("end\n", encoding="utf-8")
            self.assertEqual(gaps(folder), ["a.md:1: “c.md#x” does not exist"])


if __name__ == "__main__":
    unittest.main()
