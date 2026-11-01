"""Cross-reference test: no French cross-reference is left in the translation.

French writes “§1 bis”, “§2 ter”; English writes “§1a”, “§2b” (`outils/GLOSSARY_EN.md`). The parity test compares “§1 bis”
and “§1a” as equivalent, so it cannot see a cross-reference left in French inside an English text. This test fails if an
English file contains:
  - a cross-reference “§<n> bis”, “§<n> ter” or “§<n> quater” (with a sub-section number, “§1.4 ter”, too);
  - the key “`file:`” of a domain table (English calls it `queue:`), in the text between backticks or as a key of
    `templates/domains.yaml`.
It reads the text files of the translation: the root of `en/` in the private repository, the repository root in the
public copy (except `fr/`, `.git/` and `templates/server-runner/`, French code that is not translated). The two tests
that carry these strings as data (this one and the parity test) are not read. Standard library only.

Run from the repository root:
    python3 -B -m unittest discover -s en/templates/tests -t .
"""
import re
import tempfile
import unittest
from pathlib import Path

# The English root: `en/` in the private repository, the repository root in the public copy — in both cases two levels
# above this file.
ROOT = Path(__file__).resolve().parents[2]
SUFFIXES = {".md", ".py", ".yml", ".yaml"}
# What the test does not read: (path relative to the English root, folder prefix ending in "/" or file name).
SKIPPED = (
    "fr/", ".git/", "templates/server-runner/",
    "templates/tests/test_parity.py", "templates/tests/test_cross_refs.py",
)
RE_XREF = re.compile(r"§\s*\d+(?:\.\d+)*\s+(?:bis|ter|quater)\b", re.IGNORECASE)
RE_FILE_KEY_YAML = re.compile(r"^\s*(?:-\s*)?file\s*:", re.IGNORECASE)
FILE_KEY_IN_TEXT = "`file:`"


def files(root: Path = ROOT) -> list[Path]:
    found = []
    for p in sorted(root.rglob("*")):
        name = p.relative_to(root).as_posix()
        if p.is_file() and p.suffix in SUFFIXES and not any(
                name == s or (s.endswith("/") and name.startswith(s)) for s in SKIPPED):
            found.append(p)
    return found


def gaps(root: Path = ROOT) -> list[str]:
    """One line per French cross-reference or `file:` key in the translation; empty if all is right."""
    errors = []
    for p in files(root):
        name = p.relative_to(root).as_posix()
        for number, line in enumerate(p.read_text(encoding="utf-8").split("\n"), 1):
            for m in RE_XREF.finditer(line):
                errors.append(f"{name}:{number}: French cross-reference “{m.group()}” (English writes §1a, §2b…)")
            if FILE_KEY_IN_TEXT in line or (p.name == "domains.yaml" and RE_FILE_KEY_YAML.match(line)):
                errors.append(f"{name}:{number}: the key “file:” of a domain table (English: queue:)")
    return errors


class CrossRefCase(unittest.TestCase):
    def test_the_translation_carries_files(self):
        self.assertGreater(len(files()), 20, "few files found: is the English root wrong?")

    def test_no_french_cross_reference_is_left_in_the_english(self):
        errors = gaps()
        self.assertEqual(errors, [], "\n" + "\n".join(errors))

    def test_the_test_sees_a_french_cross_reference_and_the_file_key(self):
        with tempfile.TemporaryDirectory() as t:
            folder = Path(t)
            (folder / "templates").mkdir()
            (folder / "A.md").write_text("method §4a, §1.4b, a missing file: code 2\n", encoding="utf-8")
            self.assertEqual(gaps(folder), [])
            (folder / "A.md").write_text("ok\nmethod §1 bis\nsee §1.4 ter and §2 quater\nwhich `file:` names\n",
                                         encoding="utf-8")
            (folder / "templates" / "domains.yaml").write_text("- domain: a\n  file: \"## §1 · x\"\n", encoding="utf-8")
            self.assertEqual([g.split(":")[0] + ":" + g.split(":")[1] for g in gaps(folder)],
                             ["A.md:2", "A.md:3", "A.md:3", "A.md:4", "templates/domains.yaml:2"])

    def test_the_files_that_carry_these_strings_as_data_are_not_read(self):
        with tempfile.TemporaryDirectory() as t:
            folder = Path(t)
            for path in ("templates/tests/test_parity.py", "templates/tests/test_cross_refs.py",
                         "templates/server-runner/docs/A.md", "fr/A.md"):
                (folder / path).parent.mkdir(parents=True, exist_ok=True)
                (folder / path).write_text("§1 bis `file:`\n", encoding="utf-8")
            self.assertEqual(gaps(folder), [])


if __name__ == "__main__":
    unittest.main()
