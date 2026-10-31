"""Aides communes aux tests des scripts des vivants.

Les trois scripts (verifier_vivants.py, archiver_chantiers.py, generer_tableau.py) se lancent
toujours par un chemin calculé depuis ce fichier, jamais depuis le dossier courant ; chaque test
bâtit ses fixtures dans un dossier temporaire, à partir de textes courts et neutres.

Lancement, depuis la racine du dépôt :
    python3 -m unittest discover -s modeles/tests -t .
"""
import importlib.util
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

MODELES = Path(__file__).resolve().parent.parent
VERIFIER = MODELES / "verifier_vivants.py"
ARCHIVER = MODELES / "archiver_chantiers.py"
GENERER = MODELES / "generer_tableau.py"

ECART = "ÉCART"
AVERTISSEMENT = "avertissement"
NON_DEMANDE = "non demandé"


def charger(chemin: Path, nom: str):
    """Importe un script par son chemin, pour appeler ses fonctions (il ne s'exécute pas : garde __main__)."""
    spec = importlib.util.spec_from_file_location(nom, chemin)
    module = importlib.util.module_from_spec(spec)
    sys.modules[nom] = module
    spec.loader.exec_module(module)
    return module


def bloc(id: str, **cles) -> str:
    """Une entrée : « - id: … » puis une clé par ligne ; _ devient - dans le nom de clé ; None : clé omise."""
    lignes = [f"- id: {id}"]
    lignes += [f"  {cle.replace('_', '-')}: {valeur}" for cle, valeur in cles.items() if valeur is not None]
    return "\n".join(lignes)


def yaml(*blocs: str, entete: str = "# Chantiers — Essai") -> str:
    """Un chantiers.yaml : l'en-tête, puis les blocs séparés par une ligne vide."""
    return entete + "\n\n" + "\n\n".join(blocs) + "\n"


def registre(*numeros: int) -> str:
    """Un registre : un titre, puis une ligne « | **R<n>** | … | » par numéro donné (dans l'ordre donné)."""
    return "# Registre\n" + "".join(f"| **R{n}** | décision {n} |\n" for n in numeros)


def lire_sortie(texte: str):
    """La sortie du vérificateur : ({rang: (verdict, compte, [détails])}, dernière ligne)."""
    controles, dernier = {}, None
    for ligne in texte.split("\n"):
        if not ligne.strip():
            continue
        if ligne.startswith("      ") and dernier is not None:
            controles[dernier][2].append(ligne.strip())
            continue
        m = re.match(rf"^(\d+)\s+(.+?)\s+({ECART}|{AVERTISSEMENT}|OK)\s+(.*)$", ligne)
        if m:
            dernier = int(m.group(1))
            controles[dernier] = (m.group(3), m.group(4), [])
            continue
        m = re.match(rf"^(\d+)\s+(.+?)\s+—\s+{NON_DEMANDE}$", ligne)
        if m:
            dernier = int(m.group(1))
            controles[dernier] = (NON_DEMANDE, "", [])
            continue
        dernier = None
        controles.setdefault("bilan", ligne)
    return controles


class Sortie:
    """Le résultat d'un appel en ligne de commande."""

    def __init__(self, processus: subprocess.CompletedProcess):
        self.code = processus.returncode
        self.stdout = processus.stdout
        self.stderr = processus.stderr
        self.controles = lire_sortie(self.stdout)

    def verdict(self, rang: int) -> str:
        return self.controles[rang][0]

    def compte(self, rang: int) -> str:
        return self.controles[rang][1]

    def details(self, rang: int) -> list:
        return self.controles[rang][2]

    @property
    def bilan(self) -> str:
        return self.controles.get("bilan", "")


class CasTemporaire(unittest.TestCase):
    """Un dossier temporaire par test, des écritures de fichiers et l'appel des scripts."""

    def setUp(self):
        temporaire = tempfile.TemporaryDirectory(prefix="essai-vivants-")
        self.addCleanup(temporaire.cleanup)
        self.dossier = Path(temporaire.name)

    # Les messages d'échec restent courts quand le conteneur est une page entière.
    def assertIn(self, membre, conteneur, msg=None):
        if isinstance(conteneur, str) and len(conteneur) > 2000:
            if membre not in conteneur:
                self.fail(msg or f"absent du texte ({len(conteneur)} caractères) : {membre!r}")
        else:
            super().assertIn(membre, conteneur, msg)

    def assertNotIn(self, membre, conteneur, msg=None):
        if isinstance(conteneur, str) and len(conteneur) > 2000:
            if membre in conteneur:
                self.fail(msg or f"présent dans le texte ({len(conteneur)} caractères) : {membre!r}")
        else:
            super().assertNotIn(membre, conteneur, msg)

    def ecrire(self, nom: str, texte, binaire: bool = False) -> Path:
        chemin = self.dossier / nom
        chemin.parent.mkdir(parents=True, exist_ok=True)
        if binaire:
            chemin.write_bytes(texte)
        else:
            chemin.write_bytes(texte.encode("utf-8"))
        return chemin

    def sous_dossier(self, nom: str) -> Path:
        chemin = self.dossier / nom
        chemin.mkdir(parents=True, exist_ok=True)
        return chemin

    def lancer(self, script: Path, *arguments, cwd=None) -> Sortie:
        """Lance le script avec le même Python ; le dossier courant est le dossier temporaire par défaut."""
        environnement = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1"}
        processus = subprocess.run(
            [sys.executable, "-B", str(script), *map(str, arguments)],
            capture_output=True, text=True, encoding="utf-8",
            cwd=str(cwd or self.dossier), env=environnement)
        return Sortie(processus)
