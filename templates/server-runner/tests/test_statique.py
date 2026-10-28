"""T0 : recherche statique dans deployeur/ et installer.sh, noms propres, un seul module qui lance des processus."""

import glob
import os
import re
import unittest

from outils import RACINE

REPERTOIRES_NEUTRES = ("deployeur", "systemd", "docs")
FICHIERS_NEUTRES = ("config.exemple.json",)
# Valeurs d'exemple du bloc de l'installateur, qui ne doivent apparaître nulle part ailleurs
NOMS_PROPRES = ("/srv/monprojet", "/srv/outils", "suite-b", "journal_activite")

# Mots interdits du cadrage §3 (« down » et « rmi » comme mots isolés)
MOTS_INTERDITS = [
    (r"\bprune\b", "prune"), (r"--volumes\b", "--volumes"), (r"\brmi\b", "rmi"), (r"\bdropdb\b", "dropdb"),
    (r"DROP ", "DROP "), (r"TRUNCATE", "TRUNCATE"), (r"DELETE FROM", "DELETE FROM"), (r"UPDATE ", "UPDATE "),
    (r"INSERT INTO", "INSERT INTO"), (r"\bdown\b", "down"), (r'"-v"', '"-v"'), (r"--volume\b", "--volume"),
]
INTERDITS_PROCESSUS = [
    (r"shell\s*=\s*True", "shell=True"), (r"\bos\.system\b", "os.system"), (r"\bos\.popen\b", "os.popen"),
    (r"\bos\.exec[lv]p?e?\b", "os.exec*"), (r"\bos\.spawn", "os.spawn*"), (r"\bpopen\b", "popen"),
    (r"\bpty\b", "pty"), (r"\bcommands\.getoutput\b", "commands.getoutput"),
]


def sources_python():
    return sorted(glob.glob(os.path.join(RACINE, "deployeur", "*.py")))


def lire(chemin):
    with open(chemin, "r", encoding="utf-8") as f:
        return f.read()


def fichiers_neutres():
    res = []
    for rep in REPERTOIRES_NEUTRES:
        for racine, _, fichiers in os.walk(os.path.join(RACINE, rep)):
            if "__pycache__" in racine:
                continue
            res += [os.path.join(racine, f) for f in fichiers]
    res += [os.path.join(RACINE, f) for f in FICHIERS_NEUTRES]
    return sorted(res)


class TestRechercheStatique(unittest.TestCase):
    def cibles(self):
        return sources_python() + [os.path.join(RACINE, "installer.sh")]

    def test_t0_aucun_mot_interdit(self):
        for chemin in self.cibles():
            texte = lire(chemin)
            for motif, nom in MOTS_INTERDITS:
                trouves = [m.start() for m in re.finditer(motif, texte)]
                self.assertEqual(trouves, [], "%s : mot interdit %r" % (os.path.relpath(chemin, RACINE), nom))
            for motif, nom in MOTS_INTERDITS:
                if nom in ("DROP ", "TRUNCATE", "DELETE FROM", "UPDATE ", "INSERT INTO"):
                    self.assertIsNone(re.search(re.escape(nom), texte, re.I),
                                      "%s : %r (sans égard à la casse)" % (os.path.relpath(chemin, RACINE), nom))

    def test_t0_pg_restore_seulement_avec_list(self):
        for chemin in self.cibles():
            for i, ligne in enumerate(lire(chemin).splitlines(), 1):
                if "pg_restore" in ligne:
                    self.assertIn('"--list"', ligne, "%s:%d" % (chemin, i))
        # et il est bien présent dans commandes.py, dans une liste d'arguments qui contient --list
        self.assertRegex(lire(os.path.join(RACINE, "deployeur", "commandes.py")),
                         r'\["docker", "exec", "-i", [^\]]*"pg_restore", "--list"\]')

    def test_t0_aucun_shell_true_system_popen(self):
        for chemin in self.cibles():
            texte = lire(chemin)
            for motif, nom in INTERDITS_PROCESSUS:
                if chemin.endswith(".sh") and nom in ("pty", "popen"):
                    continue
                self.assertIsNone(re.search(motif, texte), "%s : %s" % (os.path.relpath(chemin, RACINE), nom))

    def test_t0_subprocess_seulement_dans_commandes(self):
        for chemin in sources_python():
            nom = os.path.basename(chemin)
            texte = lire(chemin)
            importe = re.search(r"^\s*(import\s+subprocess|from\s+subprocess\s+import)", texte, re.M)
            if nom == "commandes.py":
                self.assertIsNotNone(importe)
            else:
                self.assertIsNone(importe, nom)
                self.assertNotIn("subprocess", texte.replace("``subprocess``", ""), nom)

    def test_t0_aucun_nom_propre_au_projet(self):
        for chemin in fichiers_neutres():
            texte = lire(chemin).lower()
            for nom in NOMS_PROPRES:
                self.assertNotIn(nom, texte, "%s contient %r" % (os.path.relpath(chemin, RACINE), nom))

    def test_t0_les_noms_propres_sont_dans_le_bloc_de_l_installateur(self):
        texte = lire(os.path.join(RACINE, "installer.sh"))
        debut = texte.index("# Valeurs de ce projet")
        fin = texte.index("# Fin des valeurs de ce projet")
        hors_bloc = (texte[:debut] + texte[fin:]).lower()
        for nom in NOMS_PROPRES:
            self.assertNotIn(nom, hors_bloc, nom)
        self.assertIn("/srv/monprojet", texte[debut:fin].lower())

    def test_arbre_livre_conforme_au_cadrage(self):
        attendu_racine = {"README.md", "VERSION", "CHANGELOG.md", ".gitattributes", "deployeur", "systemd", "installer.sh",
                          "config.exemple.json", "docs", "tests"}
        presents = {n for n in os.listdir(RACINE) if n not in (".git", "__pycache__")}
        self.assertEqual(presents, attendu_racine)
        self.assertEqual(sorted(os.listdir(os.path.join(RACINE, "systemd"))),
                         ["deployeur-deploiement.service", "deployeur-deploiement.timer", "deployeur-fichiers.service",
                          "deployeur-fichiers.timer"])
        self.assertEqual(sorted(os.listdir(os.path.join(RACINE, "docs"))), ["INSTALLATION.md", "ORDRES.md"])
        self.assertEqual(lire(os.path.join(RACINE, "VERSION")).strip(), "0.1.1")
        self.assertIn('__version__ = "0.1.1"', lire(os.path.join(RACINE, "deployeur", "__init__.py")))
        self.assertEqual(lire(os.path.join(RACINE, ".gitattributes")).strip(), "tests/ export-ignore")

    def test_les_unites_systemd(self):
        for nom, delai in (("deploiement", "TimeoutStartSec=30min"), ("fichiers", "TimeoutStartSec=infinity")):
            service = lire(os.path.join(RACINE, "systemd", "deployeur-%s.service" % nom))
            self.assertIn("Type=oneshot", service)
            self.assertIn("ExecStart=/usr/bin/python3 -m deployeur --file %s" % nom, service)
            self.assertIn("WorkingDirectory=/opt/deployeur/courant", service)
            self.assertIn(delai, service)
            timer = lire(os.path.join(RACINE, "systemd", "deployeur-%s.timer" % nom))
            self.assertIn("OnBootSec=2min", timer)
            self.assertIn("OnUnitActiveSec=1min", timer)

    def test_le_changelog_contient_l_entree_de_reference_mot_pour_mot(self):
        texte = lire(os.path.join(RACINE, "CHANGELOG.md"))
        attendu = """# Changelog — exécutant serveur (implémentation de référence)

## 0.1.1 — implémentation de référence

Première version publiée avec le package méthode, éprouvée en production sur un projet réel. Le déployeur lit chaque
minute les ordres du dépôt privé d'ordres et n'exécute qu'une liste blanche d'actions : état, adoption du commit servi,
"""
        self.assertTrue(texte.startswith(attendu), texte[:200])
        self.assertEqual(texte.count("\n## "), 1)
        self.assertIn("Les chemins protégés par défaut sont `.env` et `backups/`.", texte)


if __name__ == "__main__":
    unittest.main()
