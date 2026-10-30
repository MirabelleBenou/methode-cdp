"""T1 et C5 : validation des ordres, exemples de docs/ORDRES.md."""

import json
import os
import re
import unittest

from outils import RACINE, Env, lire

from deployeur import config, ordres

COMMIT = "0123456789abcdef0123456789abcdef01234567"
SHA = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"


def cfg_exemple():
    return config.charger(os.path.join(RACINE, "config.exemple.json"))


def exemples_docs():
    with open(os.path.join(RACINE, "docs", "ORDRES.md"), "r", encoding="utf-8") as f:
        texte = f.read()
    return [json.loads(b) for b in re.findall(r"```json\n(.*?)\n```", texte, re.S)]


class TestExemplesDeLaDocumentation(unittest.TestCase):
    """C5 : un exemple JSON valide pour chaque action et chaque opération ; un test les charge et les valide."""

    def test_chaque_exemple_est_valide(self):
        cfg = cfg_exemple()
        exemples = exemples_docs()
        self.assertGreaterEqual(len(exemples), 12)
        for ex in exemples:
            o = ordres.charger(json.dumps(ex), ex["id"], cfg)
            self.assertEqual(o.action, ex["action"])

    def test_chaque_action_et_chaque_operation_ont_un_exemple(self):
        exemples = exemples_docs()
        actions = {e["action"] for e in exemples}
        self.assertEqual(actions, set(ordres.ACTIONS))
        operations = {op["operation"] for e in exemples if e["action"] == "fichiers" for op in e["operations"]}
        self.assertEqual(operations, set(ordres.OPERATIONS))
        cibles = {e["cible"] for e in exemples if e["action"] == "revenir"}
        self.assertEqual(cibles, {"application", "suite-a"})
        sources = {op["source"].split(":")[0] if op["source"].startswith("github:") else op["source"].split("/")[2]
                   for e in exemples if e["action"] == "fichiers" for op in e["operations"]
                   if op["operation"] == "telecharger"}
        self.assertEqual(sources, {"github", "github.com", "exemple.org"})

    def test_les_identifiants_des_exemples_sont_uniques(self):
        ids = [e["id"] for e in exemples_docs()]
        self.assertEqual(len(ids), len(set(ids)))

    def test_la_configuration_d_exemple_est_valide_et_neutre(self):
        cfg = cfg_exemple()
        self.assertEqual(cfg.application.projet, "monprojet")
        self.assertIn("suite-a", cfg.suites)


def base(**plus):
    o = {"id": "2026-10-27-01", "demande_par": "test"}
    o.update(plus)
    return o


class TestValidation(unittest.TestCase):
    def setUp(self):
        self.cfg = cfg_exemple()

    def ok(self, obj, stem=None):
        return ordres.charger(json.dumps(obj), stem or obj["id"], self.cfg)

    def refuse(self, obj, stem=None, motif=None):
        with self.assertRaises(ordres.OrdreInvalide) as cm:
            ordres.charger(obj if isinstance(obj, str) else json.dumps(obj), stem or "2026-10-27-01", self.cfg)
        if motif:
            self.assertIn(motif, str(cm.exception))

    def test_t1_action_inconnue(self):
        self.refuse(base(action="rm-rf"), motif="action inconnue")
        self.refuse(base(action="deployer-application-ancien"), motif="action inconnue")
        self.refuse(base(), motif="action inconnue")

    def test_t1_id_different_du_nom_du_fichier(self):
        self.refuse(base(action="etat"), stem="2026-10-27-02", motif="doit égaler")

    def test_t1_id_mal_forme(self):
        for ident in ("2026-10-27", "2026-13-01-01", "2026-02-30-01", "26-10-27-01", "2026-10-27-1", "2026-10-27-001",
                      "../2026-10-27-01", "", 5, None):
            o = base(action="etat")
            o["id"] = ident
            self.refuse(o, stem=str(ident))

    def test_t1_champ_inconnu_ou_manquant(self):
        self.refuse(base(action="etat", en_plus=1), motif="champ inconnu")
        self.refuse(base(action="adopter"), motif="champ manquant")
        self.refuse(base(action="adopter", commit=COMMIT, version="1"), motif="champ inconnu")
        o = base(action="etat")
        del o["demande_par"]
        self.refuse(o, motif="demande_par")
        self.refuse(base(action="etat", demande_par=""), motif="demande_par")

    def test_t1_sha_court_ou_mal_forme(self):
        self.refuse(base(action="adopter", commit="abc1234"), motif="commit")
        self.refuse(base(action="adopter", commit=COMMIT.upper()), motif="commit")
        self.refuse(base(action="adopter", commit=COMMIT + "0"), motif="commit")
        self.refuse(base(action="deployer-suite", suite="suite-a", commit=COMMIT, sha256="abc"), motif="sha256")
        self.refuse(base(action="deployer-suite", suite="suite-a", commit=COMMIT, sha256=SHA[:-1]), motif="sha256")
        self.refuse(base(action="deployer-suite", suite="suite-a", commit="court", sha256=SHA), motif="commit")

    def test_t1_suite_inconnue(self):
        self.refuse(base(action="deployer-suite", suite="inconnue", commit=COMMIT, sha256=SHA), motif="suite inconnue")
        self.refuse(base(action="revenir", cible="inconnue"), motif="cible")

    def test_t1_go_manquant_ou_vide(self):
        self.refuse(base(action="deployer-application", commit=COMMIT, version="1.0"), motif="go")
        self.refuse(base(action="deployer-application", commit=COMMIT, version="1.0", go=""), motif="go")
        self.refuse(base(action="deployer-application", commit=COMMIT, version="1.0", go="   "), motif="go")
        self.refuse(base(action="deployer-application", commit=COMMIT, version="1.0", go=5), motif="go")
        self.refuse(base(action="revenir", cible="application"), motif="go")
        self.refuse(base(action="reprendre-file", file="deploiement"), motif="go")
        self.refuse(base(action="reprendre-file", file="deploiement", go=""), motif="go")
        self.refuse(base(action="fichiers", operations=[{"operation": "vider-la-corbeille", "zone": "donnees"}]),
                    motif="go")

    def test_t1_valeurs_valides(self):
        self.ok(base(action="etat"))
        self.ok(base(action="adopter", commit=COMMIT))
        self.ok(base(action="deployer-application", commit=COMMIT, version="1.0056", go="ok"))
        self.ok(base(action="revenir", cible="suite-a"))
        self.ok(base(action="revenir", cible="suite-a", go="ok"))
        self.ok(base(action="revenir", cible="application", go="ok"))
        self.ok(base(action="reprendre-file", file="fichiers", go="ok"))

    def test_t1_reprendre_file_inconnue(self):
        self.refuse(base(action="reprendre-file", file="autre", go="ok"), motif="file")

    def test_t1_json_illisible(self):
        self.refuse("{pas du json", motif="JSON illisible")
        self.refuse("[1, 2]", motif="objet JSON")
        self.refuse("null", motif="objet JSON")

    def test_t1_operations_de_fichiers_invalides(self):
        def op(**kw):
            return base(action="fichiers", operations=[kw])
        self.refuse(base(action="fichiers"), motif="champ manquant")
        self.refuse(base(action="fichiers", operations=[]), motif="operations")
        self.refuse(base(action="fichiers", operations=[{"operation": "lister", "zone": "donnees", "chemin": ""}] * 51),
                    motif="operations")
        self.refuse(op(operation="formater", zone="donnees"), motif="opération inconnue")
        self.refuse(op(operation="lister", zone="inconnue", chemin=""), motif="zone inconnue")
        self.refuse(op(operation="lister", zone="donnees", chemin="", profondeur=4), motif="profondeur")
        self.refuse(op(operation="lister", zone="donnees", chemin="", profondeur=0), motif="profondeur")
        self.refuse(op(operation="lister", zone="donnees", chemin="../x"), motif="..")
        self.refuse(op(operation="lister", zone="donnees", chemin="/etc"), motif="absolu")
        self.refuse(op(operation="lister", zone="donnees", chemin="", en_plus=1), motif="champ inconnu")
        self.refuse(op(operation="creer-dossier", zone="donnees"), motif="champ manquant")
        self.refuse(op(operation="empreinte", zone="donnees", chemins=["a"] * 51), motif="chemins")
        self.refuse(op(operation="empreinte", zone="donnees", chemins=[]), motif="chemins")
        self.refuse(op(operation="telecharger", zone="donnees", chemin="a", source="https://pirate.test/x"),
                    motif="source")
        self.refuse(op(operation="telecharger", zone="donnees", chemin="a", source="https://exemple.org/x", sha256="abc"),
                    motif="sha256")
        self.refuse(op(operation="copier", zone="donnees", de="a", vers="b", si_existe="ecraser"), motif="si_existe")
        self.refuse(op(operation="deplacer", zone="donnees", de="a", vers="b", zone_vers="inconnue"), motif="zone")
        self.refuse(op(operation="decompresser", zone="donnees", archive="a.rar", vers="b"), motif="archive")
        self.refuse(op(operation="basculer", zone="donnees", prepare="a", servi="a"), motif="différer")
        self.refuse(base(action="fichiers", operations=[{"operation": "vider-la-corbeille", "zone": "donnees",
                                                          "id_corbeille": "../x"}], go="ok"), motif="id_corbeille")
        self.refuse(base(action="fichiers", operations=["lister"]), motif="objet attendu")

    def test_le_nom_du_fichier_est_controle(self):
        self.assertIsNone(ordres.RE_STEM.match("../x"))
        self.assertIsNone(ordres.RE_STEM.match("a b"))
        self.assertTrue(ordres.id_valide("2026-02-28-01"))
        self.assertFalse(ordres.id_valide("2026-02-29-01"))
        self.assertEqual(ordres.file_de('{"action": "fichiers"}'), "fichiers")
        self.assertEqual(ordres.file_de('{"action": "etat"}'), "deploiement")
        self.assertEqual(ordres.file_de("n'importe quoi"), "deploiement")


class TestOrdresInvalidesDeBoutEnBout(unittest.TestCase):
    """Les ordres invalides sont refusés sans que rien ne bouge (ni Docker, ni fichiers, ni état servi)."""

    def test_t1_refus_sans_aucun_geste(self):
        env = Env(self)
        env.adopter("2026-10-27-01")
        env.vider_appels()
        avant = sorted(os.listdir(env.app))
        mauvais = {
            "2026-10-27-02": base(id="2026-10-27-02", action="supprimer-tout"),
            "2026-10-27-03": base(id="2026-10-27-03", action="deployer-application", commit=env.commit_a, version="1.0055"),
            "2026-10-27-04": base(id="2026-10-27-04", action="deployer-suite", suite="inconnue", commit=COMMIT, sha256=SHA),
            "2026-10-27-05": base(id="2026-10-27-05", action="adopter", commit="abc"),
            "2026-10-27-06": base(id="2026-10-27-99", action="etat"),
            "2026-10-27-07": base(id="2026-10-27-07", action="etat", surprise=True),
        }
        for stem, obj in mauvais.items():
            env.ordre_brut(stem, json.dumps(obj))
        env.ordre_brut("2026-10-27-08", "pas du json")
        env.lancer()
        for stem in list(mauvais) + ["2026-10-27-08"]:
            self.assertEqual(env.statut(stem), "refusé", stem)
        self.assertEqual(env.appels(), [])
        self.assertEqual(sorted(os.listdir(env.app)), avant)
        self.assertEqual(env.servi()["commit"], env.commit_a)
        self.assertFalse(os.path.exists(os.path.join(env.etat_dir, "arret-deploiement.json")))

    def test_un_ordre_refuse_est_marque_et_non_rejoue(self):
        env = Env(self)
        env.ordre_brut("2026-10-27-01", json.dumps(base(action="nimporte")))
        env.lancer()
        env.lancer()
        journal = json.loads(lire(os.path.join(env.etat_dir, "journal-deploiement.json")))
        self.assertEqual(journal["ordres"]["2026-10-27-01"]["statut"], "refusé")
        log = [l for l in env.sortie if "début" in l]
        self.assertEqual(log, [])      # le second passage n'a rien rejoué


if __name__ == "__main__":
    unittest.main()
