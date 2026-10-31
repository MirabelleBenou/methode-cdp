"""Test des liens : chaque lien relatif de chaque document Markdown du package mène à un fichier qui existe.

Le test lit tous les `.md` sous la racine du package (deux niveaux au-dessus de ce fichier : la racine du dépôt privé,
ou le dossier `fr/` de la copie publique), hors blocs de code et hors extraits de code en ligne. Un lien vers une
adresse (`https:`, `mailto:`) ou une ancre seule (`#…`) n'est pas relatif : il n'est pas contrôlé. Un lien qui commence
par « / » n'est pas relatif non plus : c'est une erreur. Sans dépendance.

Lancement, depuis la racine du dépôt :
    python3 -B -m unittest discover -s modeles/tests -t .
"""
import re
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
# Dans le dépôt privé, la traduction anglaise (en/) a son propre test et l'outillage (outils/) ne part pas en copie.
EXCLUS = {"en", "outils"}
RE_LIEN = re.compile(r"\[[^\]\n]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
RE_CODE_EN_LIGNE = re.compile(r"`[^`\n]*`")
RE_ADRESSE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")


def documents(racine: Path = RACINE) -> list[Path]:
    """Tous les .md sous la racine, triés ; .git, en/ et outils/ (à la racine seulement) sont écartés."""
    return sorted(p for p in racine.rglob("*.md")
                  if ".git" not in p.relative_to(racine).parts and p.relative_to(racine).parts[0] not in EXCLUS)


def liens(chemin: Path) -> list[tuple[int, str]]:
    """Les liens (numéro de ligne, cible) d'un document, hors blocs de code et hors code en ligne."""
    trouves, dans_bloc = [], False
    for numero, ligne in enumerate(chemin.read_text(encoding="utf-8").split("\n"), 1):
        if ligne.lstrip().startswith("```"):
            dans_bloc = not dans_bloc
            continue
        if dans_bloc:
            continue
        codes = [(m.start(), m.end()) for m in RE_CODE_EN_LIGNE.finditer(ligne)]
        for m in RE_LIEN.finditer(ligne):
            if any(debut < m.start() < fin for debut, fin in codes):
                continue
            trouves.append((numero, m.group(1)))
    return trouves


def ecarts(racine: Path = RACINE) -> list[str]:
    """Une ligne par lien relatif qui ne mène nulle part ; vide si tout est juste."""
    erreurs = []
    for chemin in documents(racine):
        for numero, cible in liens(chemin):
            if cible.startswith("#") or RE_ADRESSE.match(cible):
                continue
            nom = chemin.relative_to(racine)
            if cible.startswith("/"):
                erreurs.append(f"{nom}:{numero} : lien non relatif « {cible} »")
                continue
            fichier = (chemin.parent / cible.split("#", 1)[0]).resolve()
            if not fichier.exists():
                erreurs.append(f"{nom}:{numero} : « {cible} » n'existe pas")
    return erreurs


class CasLiens(unittest.TestCase):
    def test_le_package_porte_des_documents_et_des_liens(self):
        docs = documents()
        self.assertGreater(len(docs), 5, "aucun document trouvé : la racine est fausse ?")
        self.assertTrue(any(liens(d) for d in docs), "aucun lien trouvé : le test serait vide")

    def test_chaque_lien_relatif_mene_a_un_fichier_qui_existe(self):
        erreurs = ecarts()
        self.assertEqual(erreurs, [], "\n" + "\n".join(erreurs))

    def test_le_test_voit_un_lien_mort(self):
        import tempfile
        with tempfile.TemporaryDirectory() as t:
            dossier = Path(t)
            (dossier / "a.md").write_text(
                "[ok](b.md) [mort](c.md#x) [web](https://exemple.org) `[code](d.md)`\n```\n[bloc](e.md)\n```\n",
                encoding="utf-8")
            (dossier / "b.md").write_text("fin\n", encoding="utf-8")
            self.assertEqual(ecarts(dossier), ["a.md:1 : « c.md#x » n'existe pas"])


if __name__ == "__main__":
    unittest.main()
