"""Parity test: a single source per figure of the method, and the same headings in French and in English.

(a) Each figure of the table “The method's figures” (`templates/METHOD.md` §6) appears, in the package's English `.md`
    files, only at its source — a line of that table, from its header to its last line (not another table of the
    method). Everywhere else, a pointer (“the cap in the method §6”). The patterns are looked for case-insensitively,
    with the space, the no-break space or the narrow no-break space, and in their abbreviated forms (“250 k”,
    “10 kb”); the patterns, their source and the exceptions are written below; each exception carries its reason.
(b) Each French / English pair of the neutralizer's map has the same headings (`#` to `####`), at the same rank, at the
    same level, with the same numbers (a number stuck to a letter, such as “F10” or “v2”, does not count; “§1 bis” and
    “§1a” both give 1).

It runs in the private repository (the root is `en/`, the French is one level up, the map is read from
`outils/neutraliser.py`) and in the public copy (the root is the repository's, the French is under `fr/`; the
neutralizer, which is not published, has written its map into PUBLIC_MAP). Standard library only.

Run from the repository root:
    python3 -B -m unittest discover -s en/templates/tests -t .
"""
import ast
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# In the public copy, the neutralizer replaces this line with its map (a dictionary): see `pairs()`.
PUBLIC_MAP = {'.gitignore': '.gitignore', 'README.md': 'README.md', 'NOYAU.md': 'CORE.md', 'GLOSSAIRE.md': 'GLOSSARY.md', 'DEPENDANCES_CLAUDE.md': 'CLAUDE_DEPENDENCIES.md', 'LISEZ_MOI.md': 'GUIDE.md', '1_INSTRUCTIONS_PROJET.md': '1_PROJECT_INSTRUCTIONS.md', '2_PROMPT_AMORCAGE_CDP.md': '2_PL_BOOTSTRAP_PROMPT.md', '3_GITHUB.md': '3_GITHUB.md', 'modeles/METHODE.md': 'templates/METHOD.md', 'modeles/PROMPT_DEV.md': 'templates/DEV_PROMPT.md', 'modeles/CADRAGE.md': 'templates/BRIEF.md', 'modeles/LOT_FICHIERS.md': 'templates/BATCH_FILES.md', 'modeles/COMMANDE_DEV.md': 'templates/DEV_COMMAND.md', 'modeles/CHECKPOINT.md': 'templates/CHECKPOINT.md', 'modeles/REGISTRE_ARBITRAGES.md': 'templates/DECISION_LOG.md', 'modeles/PLAN.md': 'templates/PLAN.md', 'modeles/chantiers.yaml': 'templates/workstreams.yaml', 'modeles/contexte.py': 'templates/context.py', 'modeles/generer_tableau.py': 'templates/make_board.py', 'modeles/verifier_vivants.py': 'templates/check_living_docs.py', 'modeles/archiver_chantiers.py': 'templates/archive_workstreams.py', 'modeles/ARBITRE.md': 'templates/ARBITER.md', 'modeles/CONTROLEUR.md': 'templates/CONTROLLER.md', 'modeles/arbitre.py': 'templates/arbiter.py', 'modeles/domaines.yaml': 'templates/domains.yaml', 'modeles/tests/__init__.py': 'templates/tests/__init__.py', 'modeles/tests/outils_tests.py': 'templates/tests/test_tools.py', 'modeles/tests/test_arbitre.py': 'templates/tests/test_arbiter.py', 'modeles/tests/test_contexte.py': 'templates/tests/test_context.py', 'modeles/tests/test_liens.py': 'templates/tests/test_links.py', 'modeles/tests/test_parite.py': 'templates/tests/test_parity.py', 'modeles/tests/test_verifier_vivants.py': 'templates/tests/test_check_living_docs.py', 'modeles/tests/test_archiver_chantiers.py': 'templates/tests/test_archive_workstreams.py', 'modeles/tests/test_generer_tableau.py': 'templates/tests/test_make_board.py', 'modeles/EXECUTANT_LOCAL.md': 'templates/LOCAL_RUNNER.md', 'modeles/EXECUTANT_SERVEUR.md': 'templates/SERVER_RUNNER.md', 'modeles/depot-vivants/README.md': 'templates/living-docs-repo/README.md', 'modeles/depot-vivants/arbitre.yml': 'templates/living-docs-repo/arbiter.yml', 'modeles/depot-app/.gitattributes': 'templates/code-repo/.gitattributes', 'modeles/depot-app/.gitignore': 'templates/code-repo/.gitignore', 'modeles/depot-app/CHANGELOG.md': 'templates/code-repo/CHANGELOG.md', 'skill/SKILL.md': 'skill/SKILL.md'}
FRENCH = ROOT.parent if PUBLIC_MAP is None else ROOT / "fr"

SOURCE = "templates/METHOD.md"
# The source's table: from its header line to its last line (the "|" lines that follow it without a break).
TABLE_HEADER = "| figure | value |"
# An optional separator between a number and its unit: the space, the no-break space (U+00A0), the narrow no-break
# space (U+202F).
S = "[ \u00a0\u202f]?"
# The figures of the table in the method §6, by pattern. A pattern is looked for, case-insensitively, in every line of
# every English .md; it also takes the abbreviated forms ("250 k", "350k", "10 kb").
FIGURES = {
    "handover thresholds": rf"\b(?:[2-5]50|[34]00)(?:[,\u00a0\u202f ]?000|{S}k)\b|\b450/550\b|\b1{S}M tokens\b",
    "cap of a checkpoint": rf"\b10{S}kb\b|\b10[,\u00a0\u202f ]?240\b",
    "cap of a workstream entry": rf"\b1\.5{S}kb\b",
    "cap of a decision log entry": rf"\b800{S}characters\b",
    "cut of the decision log": rf"\bfifty numbers\b|\b50{S}numbers\b|\b150{S}kb\b",
    "archiving delay of an accepted workstream": rf"\b(?:seven|7){S}days\b",
    "default model and effort of the dev": rf"Sonnet{S}·{S}Medium|\b(?:Sonnet|Medium) by default\b",
}
# The exceptions: (path, start of the excepted zone — None for the whole file) -> the reason.
EXCEPTIONS = {
    ("GUIDE.md", "**History**"):
        "the history of the guide §7 says what each version did, with the values of its time (15 days in v12): it is "
        "a dated account, not a rule in force",
    ("templates/server-runner/", None):
        "the reference implementation (public copy only), which is not translated and does not follow the project's "
        "method: its figures are its own",
}
# The root folders that (a) does not read: fr/ has its own test (test_parite.py), .git is not part of the package.
EXCLUDED = {"fr", ".git"}


def pairs() -> dict:
    """The neutralizer's map: read from outils/neutraliser.py (private), or written here by it (public copy)."""
    if PUBLIC_MAP is not None:
        return PUBLIC_MAP
    tree = ast.parse((ROOT.parent / "outils" / "neutraliser.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == "CARTE" for t in node.targets):
            return ast.literal_eval(node.value)
    raise AssertionError("CARTE not found in outils/neutraliser.py")


def documents(root: Path = ROOT) -> list[Path]:
    return sorted(p for p in root.rglob("*.md") if p.relative_to(root).parts[0] not in EXCLUDED)


def counted_lines(path: Path, root: Path = ROOT):
    """(number, line) of each line of the document that test (a) looks at: outside the excepted zones."""
    name = path.relative_to(root).as_posix()
    excepted_from = None
    for (file, zone) in EXCEPTIONS:
        if name == file or (file.endswith("/") and name.startswith(file)):
            if zone is None:
                return []
            excepted_from = zone
    out = []
    for number, line in enumerate(path.read_text(encoding="utf-8").split("\n"), 1):
        if excepted_from and line.startswith(excepted_from):
            break
        out.append((number, line))
    return out


def table_lines(path: Path, header: str = TABLE_HEADER) -> set[int]:
    """The numbers of the lines of the table of figures: from its header to its last line; empty without a header."""
    numbers, inside = set(), False
    for number, line in enumerate(path.read_text(encoding="utf-8").split("\n"), 1):
        if line.startswith(header):
            inside = True
        elif inside and not line.startswith("|"):
            break
        if inside:
            numbers.add(number)
    return numbers


def figure_gaps(root: Path = ROOT, figures: dict = FIGURES, source: str = SOURCE) -> list[str]:
    """One line per figure written outside its source, or missing from its table; empty if all is right."""
    errors, seen_at_source = [], set()
    table = table_lines(root / source) if (root / source).is_file() else set()
    for path in documents(root):
        name = path.relative_to(root).as_posix()
        for number, line in counted_lines(path, root):
            for key, pattern in figures.items():
                if not re.search(pattern, line, re.IGNORECASE):
                    continue
                if name == source and number in table:
                    seen_at_source.add(key)
                    continue
                errors.append(f"{name}:{number}: “{key}” outside its source ({source} §6): {line.strip()[:90]}")
    errors += [f"{source}: “{key}” missing from the table of figures" for key in figures if key not in seen_at_source]
    return errors


RE_HEADING = re.compile(r"^(#{1,4}) (.*)$")
RE_NUMBER = re.compile(r"(?<![A-Za-z0-9])\d+")


def headings(path: Path) -> list[tuple[int, list[str]]]:
    """(level, numbers) of each heading # to ####, outside code blocks."""
    out, in_block = [], False
    for line in path.read_text(encoding="utf-8").split("\n"):
        if line.lstrip().startswith("```"):
            in_block = not in_block
            continue
        m = None if in_block else RE_HEADING.match(line)
        if m:
            out.append((len(m.group(1)), RE_NUMBER.findall(m.group(2))))
    return out


def heading_gaps(french: Path = FRENCH, english: Path = ROOT, the_pairs: dict | None = None) -> list[str]:
    errors = []
    for fr, en in (the_pairs if the_pairs is not None else pairs()).items():
        if not fr.endswith(".md"):
            continue
        a, b = headings(french / fr), headings(english / en)
        if len(a) != len(b):
            errors.append(f"{fr} → {en}: {len(a)} headings against {len(b)}")
        for rank, (x, y) in enumerate(zip(a, b), 1):
            if x != y:
                errors.append(f"{fr} → {en}: heading {rank}, level and numbers {x} against {y}")
    return errors


class ParityCase(unittest.TestCase):
    def test_each_figure_is_written_only_at_its_source(self):
        errors = figure_gaps()
        self.assertEqual(errors, [], "\n" + "\n".join(errors))

    def test_each_pair_has_the_same_headings(self):
        self.assertGreater(len([f for f in pairs() if f.endswith(".md")]), 10, "empty map: is the root wrong?")
        errors = heading_gaps()
        self.assertEqual(errors, [], "\n" + "\n".join(errors))

    def test_the_test_sees_a_figure_outside_its_source_and_an_empty_table(self):
        import tempfile
        with tempfile.TemporaryDirectory() as t:
            folder = Path(t)
            (folder / "templates").mkdir()
            (folder / "templates" / "METHOD.md").write_text(
                "| figure | value |\n|---|---|\n| cap | **10 KB** |\n\na checkpoint of 10 KB\n"
                "| another table | 10 KB |\n", encoding="utf-8")
            (folder / "a.md").write_text("ok\nseven days later\n", encoding="utf-8")
            errors = figure_gaps(folder, {"ckpt": r"\b10 KB\b", "delay": r"\bseven days\b",
                                          "threshold": r"\b250,000\b"})
            self.assertEqual([e.split(": ")[0] for e in errors],
                             ["a.md:2", "templates/METHOD.md:5", "templates/METHOD.md:6", "templates/METHOD.md",
                              "templates/METHOD.md"])

    def test_the_patterns_take_no_break_spaces_case_and_abbreviated_forms(self):
        seen = {
            "handover thresholds": ["250\u00a0000 tokens", "350\u202f000", "250,000", "250 k", "350k", "450 K", "300\u00a0000 tokens", "400,000", "400 k"],
            "cap of a checkpoint": ["10 kb", "10\u00a0KB", "10\u202fKb", "10KB", "10,240 bytes"],
            "cap of a workstream entry": ["~1.5\u00a0kb"],
            "cap of a decision log entry": ["800\u00a0characters"],
            "cut of the decision log": ["150\u202fkb", "Fifty numbers"],
            "archiving delay of an accepted workstream": ["Seven\u00a0days", "7\u202fdays"],
            "default model and effort of the dev": ["sonnet\u00a0·\u00a0medium", "Sonnet by default"],
        }
        for key, forms in seen.items():
            for form in forms:
                self.assertTrue(re.search(FIGURES[key], form, re.IGNORECASE), f"{key}: {form!r}")
        for form in ("1,250 tokens", "10 kilometres", "v1.10", "D250", "2500 k"):
            self.assertFalse(any(re.search(p, form, re.IGNORECASE) for p in FIGURES.values()), form)

    def test_the_test_sees_a_heading_that_differs(self):
        import tempfile
        with tempfile.TemporaryDirectory() as t:
            fr, en = Path(t) / "fr", Path(t) / "en"
            fr.mkdir(), en.mkdir()
            (fr / "a.md").write_text("# A · 31 octobre\n## §1 bis · x\n### F10\n```\n# not a heading\n```\n",
                                     encoding="utf-8")
            (en / "a.md").write_text("# A · 31 October\n## §1a · x\n### F12\n", encoding="utf-8")
            self.assertEqual(heading_gaps(fr, en, {"a.md": "a.md"}), [])
            (en / "a.md").write_text("# A · 30 October\n### §1a · x\n", encoding="utf-8")
            self.assertEqual(len(heading_gaps(fr, en, {"a.md": "a.md"})), 3)



NEUTRALIZER = ROOT.parent / "outils" / "neutraliser.py"


@unittest.skipUnless(PUBLIC_MAP is None and NEUTRALIZER.is_file(), "the neutralizer is not published in the copy")
class PublicMapCase(unittest.TestCase):
    """The neutralizer re-reads the map it writes into the copy's parity tests, and fails if it drifts."""

    @classmethod
    def setUpClass(cls):
        import importlib.util
        spec = importlib.util.spec_from_file_location("neutralizer_under_test", NEUTRALIZER)
        cls.n = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.n)

    def rendered(self) -> dict:
        """A minimal copy: each path of the public map, and both parity tests with their written map."""
        n = self.n
        rendered = {p: b"" for pair in n.carte_publique().items() for p in pair}
        rendered["fr/modeles/tests/test_parite.py"] = n.avec_carte(
            "modeles/tests/test_parite.py",
            (ROOT.parent / "modeles/tests/test_parite.py").read_text(encoding="utf-8")).encode()
        rendered["templates/tests/test_parity.py"] = n.avec_carte(
            "templates/tests/test_parity.py", (ROOT / "templates/tests/test_parity.py").read_text(encoding="utf-8")).encode()
        return rendered

    def test_the_written_map_is_the_translated_map(self):
        self.assertEqual(self.n.ecarts_cartes_publiques(self.rendered()), [])

    def test_a_map_that_drifts_is_refused(self):
        rendered = self.rendered()
        text = rendered["templates/tests/test_parity.py"].decode()
        rendered["templates/tests/test_parity.py"] = text.replace("'templates/METHOD.md'", "'templates/METHODE.md'", 1).encode()
        self.assertEqual(self.n.ecarts_cartes_publiques(rendered),
                         ["  templates/tests/test_parity.py : PUBLIC_MAP n'est pas la CARTE traduite en chemins publics"])

    def test_a_map_left_empty_or_a_missing_path_is_refused(self):
        rendered = self.rendered()
        rendered["fr/modeles/tests/test_parite.py"] = (ROOT.parent / "modeles/tests/test_parite.py").read_bytes()
        del rendered["fr/GLOSSAIRE.md"]
        self.assertEqual(self.n.ecarts_cartes_publiques(rendered),
                         ["  fr/modeles/tests/test_parite.py : CARTE_PUBLIQUE n'est pas une carte (NoneType)",
                          "  fr/GLOSSAIRE.md : chemin de la carte publique absent de la copie"])

if __name__ == "__main__":
    unittest.main()
