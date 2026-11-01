"""Test de parité : une seule source par chiffre de la méthode, et les mêmes titres en français et en anglais.

(a) Chaque chiffre de la table « Les chiffres de la méthode » (`modeles/METHODE.md` §6) n'apparaît, dans les `.md` du
    package, qu'à sa source — une ligne de cette table, de son en-tête à sa dernière ligne (pas une autre table de la
    méthode). Partout ailleurs, un renvoi (« le plafond de la méthode §6 »). Les motifs se cherchent la casse
    indifférente, avec l'espace, l'espace insécable ou l'espace fine insécable, et sous leurs formes abrégées
    (« 250 k », « 10 ko ») ; les motifs, leur source et les exceptions sont écrits ci-dessous ; chaque exception porte
    sa raison.
(b) Chaque paire français / anglais de la `CARTE` du neutraliseur (`outils/neutraliser.py`) a les mêmes titres (`#` à
    `####`), au même rang, au même niveau, avec les mêmes nombres (un nombre collé à une lettre, comme « F10 » ou
    « v2 », ne compte pas ; « §1 bis » et « §1a » donnent tous deux 1).

Il tourne dans le dépôt privé (la racine est celle du dépôt, l'anglais est sous `en/`, la carte se lit dans
`outils/neutraliser.py`) et dans la copie publique (la racine est `fr/`, l'anglais est au-dessus ; le neutraliseur, qui
ne part pas, y a écrit sa carte dans CARTE_PUBLIQUE). Bibliothèque standard seule.

Lancement, depuis la racine du dépôt :
    python3 -B -m unittest discover -s modeles/tests -t .
"""
import ast
import re
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
# Dans la copie publique, le neutraliseur remplace cette ligne par sa CARTE (un dictionnaire) : voir `carte()`.
CARTE_PUBLIQUE = {'.gitignore': '.gitignore', 'README.md': 'README.md', 'NOYAU.md': 'CORE.md', 'GLOSSAIRE.md': 'GLOSSARY.md', 'DEPENDANCES_CLAUDE.md': 'CLAUDE_DEPENDENCIES.md', 'LISEZ_MOI.md': 'GUIDE.md', '1_INSTRUCTIONS_PROJET.md': '1_PROJECT_INSTRUCTIONS.md', '2_PROMPT_AMORCAGE_CDP.md': '2_PL_BOOTSTRAP_PROMPT.md', '3_GITHUB.md': '3_GITHUB.md', 'modeles/METHODE.md': 'templates/METHOD.md', 'modeles/PROMPT_DEV.md': 'templates/DEV_PROMPT.md', 'modeles/CADRAGE.md': 'templates/BRIEF.md', 'modeles/LOT_FICHIERS.md': 'templates/BATCH_FILES.md', 'modeles/COMMANDE_DEV.md': 'templates/DEV_COMMAND.md', 'modeles/CHECKPOINT.md': 'templates/CHECKPOINT.md', 'modeles/REGISTRE_ARBITRAGES.md': 'templates/DECISION_LOG.md', 'modeles/PLAN.md': 'templates/PLAN.md', 'modeles/chantiers.yaml': 'templates/workstreams.yaml', 'modeles/contexte.py': 'templates/context.py', 'modeles/generer_tableau.py': 'templates/make_board.py', 'modeles/verifier_vivants.py': 'templates/check_living_docs.py', 'modeles/archiver_chantiers.py': 'templates/archive_workstreams.py', 'modeles/ARBITRE.md': 'templates/ARBITER.md', 'modeles/CONTROLEUR.md': 'templates/CONTROLLER.md', 'modeles/arbitre.py': 'templates/arbiter.py', 'modeles/domaines.yaml': 'templates/domains.yaml', 'modeles/tests/__init__.py': 'templates/tests/__init__.py', 'modeles/tests/outils_tests.py': 'templates/tests/test_tools.py', 'modeles/tests/test_arbitre.py': 'templates/tests/test_arbiter.py', 'modeles/tests/test_contexte.py': 'templates/tests/test_context.py', 'modeles/tests/test_liens.py': 'templates/tests/test_links.py', 'modeles/tests/test_parite.py': 'templates/tests/test_parity.py', 'modeles/tests/test_verifier_vivants.py': 'templates/tests/test_check_living_docs.py', 'modeles/tests/test_archiver_chantiers.py': 'templates/tests/test_archive_workstreams.py', 'modeles/tests/test_generer_tableau.py': 'templates/tests/test_make_board.py', 'modeles/EXECUTANT_LOCAL.md': 'templates/LOCAL_RUNNER.md', 'modeles/EXECUTANT_SERVEUR.md': 'templates/SERVER_RUNNER.md', 'modeles/depot-vivants/README.md': 'templates/living-docs-repo/README.md', 'modeles/depot-vivants/arbitre.yml': 'templates/living-docs-repo/arbiter.yml', 'modeles/depot-app/.gitattributes': 'templates/code-repo/.gitattributes', 'modeles/depot-app/.gitignore': 'templates/code-repo/.gitignore', 'modeles/depot-app/CHANGELOG.md': 'templates/code-repo/CHANGELOG.md', 'skill/SKILL.md': 'skill/SKILL.md'}
ANGLAIS = RACINE / "en" if CARTE_PUBLIQUE is None else RACINE.parent

SOURCE = "modeles/METHODE.md"
# La table de la source : de sa ligne d'en-tête à sa dernière ligne (les lignes « | » qui la suivent sans interruption).
ENTETE_TABLE = "| chiffre | valeur |"
# Un séparateur facultatif entre un nombre et son unité : l'espace, l'espace insécable (U+00A0), l'espace fine
# insécable (U+202F).
E = "[ \u00a0\u202f]?"
# Les chiffres de la table de la méthode §6, par motif. Un motif se cherche, la casse indifférente, dans chaque ligne de
# chaque .md français ; il prend aussi les formes abrégées (« 250 k », « 350k », « 10 ko »).
CHIFFRES = {
    "seuils de passation": rf"\b(?:[2-5]50|[34]00)(?:{E}000|{E}k)\b|\b450/550\b|\b1{E}M de jetons\b",
    "plafond d'un checkpoint": rf"\b10{E}ko\b|\b10{E}240\b",
    "plafond d'une entrée de chantier": rf"\b1[,.]5{E}ko\b",
    "plafond d'une entrée du registre": rf"\b800{E}caractères\b",
    "coupe du registre": rf"\bcinquante numéros\b|\b50{E}numéros\b|\b150{E}ko\b",
    "délai d'archivage d'un chantier en recette": rf"\b(?:sept|7){E}jours\b",
    "modèle et effort par défaut du dev": rf"Sonnet{E}·{E}Medium|\b(?:Sonnet|Medium) par défaut\b",
}
# Les exceptions : (chemin, début de la zone exceptée — None pour tout le fichier) -> la raison.
EXCEPTIONS = {
    ("LISEZ_MOI.md", "**Historique**"):
        "l'historique du guide §7 dit ce que chaque version a fait, avec les valeurs de son temps (15 jours en v12) : "
        "c'est un récit daté, pas une règle en vigueur",
    ("modeles/executant-serveur/docs/ORDRES.md", None):
        "un autre chiffre (les ordres joués depuis 7 jours, que l'action etat rapporte), dans l'implémentation de "
        "référence, qui ne se traduit pas et ne suit pas la méthode du projet",
}
# Les dossiers de la racine que (a) ne lit pas : en/ a son propre test (test_parity.py), .git n'est pas du package.
EXCLUS = {"en", ".git"}


def carte() -> dict:
    """La CARTE du neutraliseur : lue dans outils/neutraliser.py (privé), ou écrite ici par lui (copie publique)."""
    if CARTE_PUBLIQUE is not None:
        return CARTE_PUBLIQUE
    arbre = ast.parse((RACINE / "outils" / "neutraliser.py").read_text(encoding="utf-8"))
    for noeud in arbre.body:
        if isinstance(noeud, ast.Assign) and any(getattr(c, "id", None) == "CARTE" for c in noeud.targets):
            return ast.literal_eval(noeud.value)
    raise AssertionError("CARTE introuvable dans outils/neutraliser.py")


def documents(racine: Path = RACINE) -> list[Path]:
    return sorted(p for p in racine.rglob("*.md") if p.relative_to(racine).parts[0] not in EXCLUS)


def lignes_comptees(chemin: Path, racine: Path = RACINE):
    """(numéro, ligne) de chaque ligne du document que le test (a) regarde : hors des zones exceptées."""
    nom = chemin.relative_to(racine).as_posix()
    debut_excepte = None
    for (fichier, zone) in EXCEPTIONS:
        if fichier == nom:
            if zone is None:
                return []
            debut_excepte = zone
    sortie = []
    for numero, ligne in enumerate(chemin.read_text(encoding="utf-8").split("\n"), 1):
        if debut_excepte and ligne.startswith(debut_excepte):
            break
        sortie.append((numero, ligne))
    return sortie


def lignes_de_la_table(chemin: Path, entete: str = ENTETE_TABLE) -> set[int]:
    """Les numéros des lignes de la table des chiffres : de son en-tête à sa dernière ligne ; vide sans en-tête."""
    numeros, dedans = set(), False
    for numero, ligne in enumerate(chemin.read_text(encoding="utf-8").split("\n"), 1):
        if ligne.startswith(entete):
            dedans = True
        elif dedans and not ligne.startswith("|"):
            break
        if dedans:
            numeros.add(numero)
    return numeros


def ecarts_chiffres(racine: Path = RACINE, chiffres: dict = CHIFFRES, source: str = SOURCE) -> list[str]:
    """Une ligne par chiffre écrit hors de sa source, ou absent de sa table ; vide si tout est juste."""
    erreurs, vus_a_la_source = [], set()
    table = lignes_de_la_table(racine / source) if (racine / source).is_file() else set()
    for chemin in documents(racine):
        nom = chemin.relative_to(racine).as_posix()
        for numero, ligne in lignes_comptees(chemin, racine):
            for cle, motif in chiffres.items():
                if not re.search(motif, ligne, re.IGNORECASE):
                    continue
                if nom == source and numero in table:
                    vus_a_la_source.add(cle)
                    continue
                erreurs.append(f"{nom}:{numero} : « {cle} » hors de sa source ({source} §6) : {ligne.strip()[:90]}")
    erreurs += [f"{source} : « {cle} » absent de la table des chiffres" for cle in chiffres if cle not in vus_a_la_source]
    return erreurs


RE_TITRE = re.compile(r"^(#{1,4}) (.*)$")
RE_NOMBRE = re.compile(r"(?<![A-Za-z0-9])\d+")


def titres(chemin: Path) -> list[tuple[int, list[str]]]:
    """(niveau, nombres) de chaque titre # à ####, hors blocs de code."""
    sortie, dans_bloc = [], False
    for ligne in chemin.read_text(encoding="utf-8").split("\n"):
        if ligne.lstrip().startswith("```"):
            dans_bloc = not dans_bloc
            continue
        m = None if dans_bloc else RE_TITRE.match(ligne)
        if m:
            sortie.append((len(m.group(1)), RE_NOMBRE.findall(m.group(2))))
    return sortie


def ecarts_titres(francais: Path = RACINE, anglais: Path = ANGLAIS, paires: dict | None = None) -> list[str]:
    erreurs = []
    for fr, en in (paires if paires is not None else carte()).items():
        if not fr.endswith(".md"):
            continue
        a, b = titres(francais / fr), titres(anglais / en)
        if len(a) != len(b):
            erreurs.append(f"{fr} → {en} : {len(a)} titres contre {len(b)}")
        for rang, (x, y) in enumerate(zip(a, b), 1):
            if x != y:
                erreurs.append(f"{fr} → {en} : titre {rang}, niveau et nombres {x} contre {y}")
    return erreurs


class CasParite(unittest.TestCase):
    def test_chaque_chiffre_n_est_ecrit_qu_a_sa_source(self):
        erreurs = ecarts_chiffres()
        self.assertEqual(erreurs, [], "\n" + "\n".join(erreurs))

    def test_chaque_paire_a_les_memes_titres(self):
        self.assertGreater(len([f for f in carte() if f.endswith(".md")]), 10, "carte vide : la racine est fausse ?")
        erreurs = ecarts_titres()
        self.assertEqual(erreurs, [], "\n" + "\n".join(erreurs))

    def test_le_test_voit_un_chiffre_hors_de_sa_source_et_une_table_vide(self):
        import tempfile
        with tempfile.TemporaryDirectory() as t:
            dossier = Path(t)
            (dossier / "modeles").mkdir()
            (dossier / "modeles" / "METHODE.md").write_text(
                "| chiffre | valeur |\n|---|---|\n| plafond | **10 Ko** |\n\nun checkpoint de 10 Ko\n"
                "| une autre table | 10 Ko |\n", encoding="utf-8")
            (dossier / "a.md").write_text("ok\nsept jours plus tard\n", encoding="utf-8")
            erreurs = ecarts_chiffres(dossier, {"ckpt": r"\b10 Ko\b", "délai": r"\bsept jours\b",
                                                "seuil": r"\b250 000\b"})
            self.assertEqual([e.split(" :")[0] for e in erreurs],
                             ["a.md:2", "modeles/METHODE.md:5", "modeles/METHODE.md:6", "modeles/METHODE.md",
                              "modeles/METHODE.md"])

    def test_les_motifs_prennent_les_espaces_insecables_la_casse_et_les_formes_abregees(self):
        vus = {
            "seuils de passation": ["250\u00a0000 jetons", "350\u202f000", "250 k", "350k", "450 K", "300\u00a0000 jetons", "400 k"],
            "plafond d'un checkpoint": ["10 ko", "10\u00a0Ko", "10\u202fKO", "10Ko", "10\u00a0240 octets"],
            "plafond d'une entrée de chantier": ["~1,5\u00a0ko"],
            "plafond d'une entrée du registre": ["800\u00a0caractères"],
            "coupe du registre": ["150\u202fko", "Cinquante numéros"],
            "délai d'archivage d'un chantier en recette": ["Sept\u00a0jours", "7\u202fjours"],
            "modèle et effort par défaut du dev": ["sonnet\u00a0·\u00a0medium", "Sonnet par défaut"],
        }
        for cle, formes in vus.items():
            for forme in formes:
                self.assertTrue(re.search(CHIFFRES[cle], forme, re.IGNORECASE), f"{cle} : {forme!r}")
        for forme in ("1 250 jetons", "10 kilomètres", "v1.10", "R250", "2500 k"):
            self.assertFalse(any(re.search(m, forme, re.IGNORECASE) for m in CHIFFRES.values()), forme)

    def test_le_test_voit_un_titre_qui_differe(self):
        import tempfile
        with tempfile.TemporaryDirectory() as t:
            fr, en = Path(t) / "fr", Path(t) / "en"
            fr.mkdir(), en.mkdir()
            (fr / "a.md").write_text("# A · 31 octobre\n## §1 bis · x\n### F10\n```\n# pas un titre\n```\n",
                                     encoding="utf-8")
            (en / "a.md").write_text("# A · 31 October\n## §1a · x\n### F12\n", encoding="utf-8")
            self.assertEqual(ecarts_titres(fr, en, {"a.md": "a.md"}), [])
            (en / "a.md").write_text("# A · 30 octobre\n### §1a · x\n", encoding="utf-8")
            self.assertEqual(len(ecarts_titres(fr, en, {"a.md": "a.md"})), 3)



NEUTRALISEUR = RACINE / "outils" / "neutraliser.py"


@unittest.skipUnless(CARTE_PUBLIQUE is None and NEUTRALISEUR.is_file(), "le neutraliseur ne part pas dans la copie")
class CasCartePublique(unittest.TestCase):
    """Le neutraliseur relit la carte qu'il écrit dans les tests de parité de la copie, et échoue si elle dérive."""

    @classmethod
    def setUpClass(cls):
        import importlib.util
        spec = importlib.util.spec_from_file_location("neutraliser_sous_test", NEUTRALISEUR)
        cls.n = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.n)

    def rendus(self) -> dict:
        """Une copie minimale : chaque chemin de la carte publique, et les deux tests de parité avec leur carte écrite."""
        n = self.n
        rendus = {c: b"" for paire in n.carte_publique().items() for c in paire}
        rendus["fr/modeles/tests/test_parite.py"] = n.avec_carte(
            "modeles/tests/test_parite.py", (RACINE / "modeles/tests/test_parite.py").read_text(encoding="utf-8")).encode()
        rendus["templates/tests/test_parity.py"] = n.avec_carte(
            "templates/tests/test_parity.py",
            (RACINE / "en/templates/tests/test_parity.py").read_text(encoding="utf-8")).encode()
        return rendus

    def test_la_carte_ecrite_est_la_carte_traduite(self):
        self.assertEqual(self.n.ecarts_cartes_publiques(self.rendus()), [])

    def test_une_carte_qui_derive_est_refusee(self):
        rendus = self.rendus()
        texte = rendus["templates/tests/test_parity.py"].decode()
        rendus["templates/tests/test_parity.py"] = texte.replace("'templates/METHOD.md'", "'templates/METHODE.md'", 1).encode()
        self.assertEqual(self.n.ecarts_cartes_publiques(rendus),
                         ["  templates/tests/test_parity.py : PUBLIC_MAP n'est pas la CARTE traduite en chemins publics"])

    def test_une_carte_restee_vide_ou_un_chemin_absent_est_refuse(self):
        rendus = self.rendus()
        rendus["fr/modeles/tests/test_parite.py"] = (RACINE / "modeles/tests/test_parite.py").read_bytes()
        del rendus["fr/GLOSSAIRE.md"]
        self.assertEqual(self.n.ecarts_cartes_publiques(rendus),
                         ["  fr/modeles/tests/test_parite.py : CARTE_PUBLIQUE n'est pas une carte (NoneType)",
                          "  fr/GLOSSAIRE.md : chemin de la carte publique absent de la copie"])

if __name__ == "__main__":
    unittest.main()
