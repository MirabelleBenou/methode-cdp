"""Test des renvois dans l'anglais : aucun renvoi français ne reste dans la traduction.

Le français écrit « §1 bis », « §2 ter » ; l'anglais écrit « §1a », « §2b » (`outils/GLOSSARY_EN.md`). Le test de parité
compare « §1 bis » et « §1a » comme équivalents : il ne voit donc pas un renvoi resté en français dans un texte anglais.
Ce test-ci échoue si un fichier anglais contient :
  - un renvoi « §<n> bis », « §<n> ter » ou « §<n> quater » (avec un numéro de sous-section, « §1.4 ter », aussi) ;
  - la clé « `file:` » d'une table des domaines (l'anglais l'appelle `queue:`), dans le texte entre accents graves ou
    comme clé de `templates/domains.yaml`.
Il lit les fichiers texte de la traduction : `en/` dans le dépôt privé, la racine de la copie publique (hors `fr/`, `.git/`
et `templates/server-runner/`, du code en français qui ne se traduit pas). Les deux tests de renvois et de parité portent ces
chaînes comme données : ils ne sont pas lus. Bibliothèque standard seule.

Lancement, depuis la racine du dépôt :
    python3 -B -m unittest discover -s modeles/tests -t .
"""
import re
import tempfile
import unittest
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
# Dépôt privé : la traduction est sous en/. Copie publique : la racine est fr/, la traduction est au-dessus.
ANGLAIS = RACINE / "en" if (RACINE / "en").is_dir() else RACINE.parent
SUFFIXES = {".md", ".py", ".yml", ".yaml"}
# Ce que le test ne lit pas : (chemin relatif à la racine anglaise, préfixe de dossier terminé par « / » ou nom de fichier).
ECARTES = (
    "fr/", ".git/", "templates/server-runner/",
    "templates/tests/test_parity.py", "templates/tests/test_cross_refs.py",
)
RE_RENVOI = re.compile(r"§\s*\d+(?:\.\d+)*\s+(?:bis|ter|quater)\b", re.IGNORECASE)
RE_CLE_FILE_YAML = re.compile(r"^\s*(?:-\s*)?file\s*:", re.IGNORECASE)
CLE_FILE_EN_TEXTE = "`file:`"


def fichiers(racine: Path = ANGLAIS) -> list[Path]:
    sortie = []
    for p in sorted(racine.rglob("*")):
        nom = p.relative_to(racine).as_posix()
        if p.is_file() and p.suffix in SUFFIXES and not any(
                nom == e or (e.endswith("/") and nom.startswith(e)) for e in ECARTES):
            sortie.append(p)
    return sortie


def ecarts(racine: Path = ANGLAIS) -> list[str]:
    """Une ligne par renvoi français ou par clé `file:` dans la traduction ; vide si tout est juste."""
    erreurs = []
    for p in fichiers(racine):
        nom = p.relative_to(racine).as_posix()
        for numero, ligne in enumerate(p.read_text(encoding="utf-8").split("\n"), 1):
            for m in RE_RENVOI.finditer(ligne):
                erreurs.append(f"{nom}:{numero} : renvoi français « {m.group()} » (l'anglais écrit §1a, §2b…)")
            if CLE_FILE_EN_TEXTE in ligne or (p.name == "domains.yaml" and RE_CLE_FILE_YAML.match(ligne)):
                erreurs.append(f"{nom}:{numero} : la clé « file: » d'une table des domaines (l'anglais : queue:)")
    return erreurs


class CasRenvoisEn(unittest.TestCase):
    def test_la_traduction_porte_des_fichiers(self):
        self.assertGreater(len(fichiers()), 20, "peu de fichiers trouvés : la racine anglaise est fausse ?")

    def test_aucun_renvoi_francais_ne_reste_dans_l_anglais(self):
        erreurs = ecarts()
        self.assertEqual(erreurs, [], "\n" + "\n".join(erreurs))

    def test_le_test_voit_un_renvoi_francais_et_la_cle_file(self):
        with tempfile.TemporaryDirectory() as t:
            dossier = Path(t)
            (dossier / "templates").mkdir()
            (dossier / "A.md").write_text("method §4a, §1.4b, a missing file: code 2\n", encoding="utf-8")
            self.assertEqual(ecarts(dossier), [])
            (dossier / "A.md").write_text("ok\nmethod §1 bis\nsee §1.4 ter and §2 quater\nwhich `file:` names\n",
                                          encoding="utf-8")
            (dossier / "templates" / "domains.yaml").write_text("- domain: a\n  file: \"## §1 · x\"\n", encoding="utf-8")
            self.assertEqual([e.split(" :")[0] for e in ecarts(dossier)],
                             ["A.md:2", "A.md:3", "A.md:3", "A.md:4", "templates/domains.yaml:2"])

    def test_les_fichiers_qui_portent_ces_chaines_comme_donnees_ne_sont_pas_lus(self):
        with tempfile.TemporaryDirectory() as t:
            dossier = Path(t)
            for chemin in ("templates/tests/test_parity.py", "templates/tests/test_cross_refs.py",
                           "templates/server-runner/docs/A.md", "fr/A.md"):
                (dossier / chemin).parent.mkdir(parents=True, exist_ok=True)
                (dossier / chemin).write_text("§1 bis `file:`\n", encoding="utf-8")
            self.assertEqual(ecarts(dossier), [])


if __name__ == "__main__":
    unittest.main()
