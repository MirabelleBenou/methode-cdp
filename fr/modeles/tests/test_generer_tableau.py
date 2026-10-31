"""Tests de generer_tableau.py : une page fixe et un fichier de données tirés de chantiers.yaml, déterministes.

La page ne porte aucune donnée de chantier ; les chantiers sont dans le fichier .json écrit à côté. Chaque
test bâtit sa source dans un dossier temporaire (voir outils_tests.py) et appelle le script en ligne de
commande. Le JavaScript de la page ne s'exécute pas ici (bibliothèque standard seule) : les tests lisent
les données dans le JSON et vérifient la page comme un texte.
"""
import json
import re
import unittest
from datetime import date

from .outils_tests import GENERER, CasTemporaire, bloc, yaml

STATUTS = [("a-venir", "À venir"), ("a-cadrer", "À cadrer"), ("en-vol", "En vol"),
           ("dette", "Dette"), ("recette", "Recetté")]
RE_DATE = re.compile(r"\d{2}/\d{2}/\d{4}")
LIBELLES_DEFAUT = {"ecran": "Écran", "donnees": "Données", "doc": "Documentation", "outillage": "Outillage",
                   "moteur": "Moteur", "exploitation": "Exploitation", "socle": "Socle"}


def constante(page: str, nom: str):
    """La valeur JSON d'une constante « const NOM = …; » du script de la page."""
    m = re.search(rf"^const {nom} = (.*);$", page, flags=re.M)
    assert m, f"constante {nom} absente de la page"
    return json.loads(m.group(1))


class CasGenerer(CasTemporaire):
    def setUp(self):
        super().setUp()
        self.html = self.dossier / "chantiers.html"
        self.json = self.dossier / "chantiers.json"

    def generer(self, *blocs: str, entete: str = "# Chantiers — Essai", nom_source: str = "chantiers.yaml"):
        self.source = self.ecrire(nom_source, yaml(*blocs, entete=entete))
        sortie = self.lancer(GENERER, self.source, self.html)
        self.assertEqual(sortie.code, 0, sortie.stdout + sortie.stderr)
        return sortie

    def page(self) -> str:
        return self.html.read_text(encoding="utf-8")

    def texte_donnees(self) -> str:
        return self.json.read_text(encoding="utf-8")

    def donnees(self) -> dict:
        return json.loads(self.texte_donnees())

    def chantiers(self) -> list:
        return self.donnees()["chantiers"]


class TestGeneration(CasGenerer):
    def test_la_sortie_resume_ce_qui_a_ete_lu(self):
        sortie = self.generer(bloc("alpha-1", statut="a-venir"), bloc("alpha-2", statut="dette"),
                              bloc("alpha-3", statut="dette"))
        self.assertTrue(sortie.stdout.startswith("3 chantiers lus · "), sortie.stdout)
        self.assertIn('"a-venir": 1', sortie.stdout)
        self.assertIn('"dette": 2', sortie.stdout)
        self.assertIn('"recette": 0', sortie.stdout)
        self.assertTrue(sortie.stdout.rstrip().endswith(f"écrit dans {self.html} et {self.json}"), sortie.stdout)

    def test_deux_fichiers_sont_ecrits_et_le_second_porte_le_meme_nom_en_json(self):
        self.generer(bloc("alpha-1", statut="a-venir"))
        self.assertTrue(self.html.is_file())
        self.assertTrue(self.json.is_file())
        self.assertEqual(sorted(p.name for p in self.dossier.iterdir()), ["chantiers.html", "chantiers.json", "chantiers.yaml"])

    def test_le_fichier_de_donnees_se_range_a_cote_de_la_page_sous_son_nom(self):
        source = self.ecrire("chantiers.yaml", yaml(bloc("alpha-1", statut="a-venir")))
        (self.dossier / "x").mkdir()
        sortie = self.lancer(GENERER, source, self.dossier / "x" / "tableau.html")
        self.assertEqual(sortie.code, 0, sortie.stdout + sortie.stderr)
        self.assertEqual(sorted(p.name for p in (self.dossier / "x").iterdir()), ["tableau.html", "tableau.json"])
        self.assertTrue(sortie.stdout.rstrip().endswith(
            f"écrit dans {self.dossier / 'x' / 'tableau.html'} et {self.dossier / 'x' / 'tableau.json'}"), sortie.stdout)
        self.assertIn('"tableau.json"', (self.dossier / "x" / "tableau.html").read_text(encoding="utf-8"))

    def test_deux_generations_de_la_meme_source_sont_identiques_hors_la_date(self):
        self.generer(bloc("alpha-1", titre="Premier", statut="a-venir", module="module-a", priorite="haut"),
                     bloc("alpha-2", titre="Deuxième", statut="recette", module="module-b", complexite="forte"))
        premiere, premieres_donnees = self.page(), self.texte_donnees()
        seconde_page = self.dossier / "seconde.html"
        self.assertEqual(self.lancer(GENERER, self.source, seconde_page).code, 0)
        seconde = seconde_page.read_text(encoding="utf-8")
        secondes_donnees = (self.dossier / "seconde.json").read_text(encoding="utf-8")
        self.assertEqual(RE_DATE.sub("<date>", premieres_donnees), RE_DATE.sub("<date>", secondes_donnees))
        self.assertEqual(len(RE_DATE.findall(premieres_donnees)), 1)
        # la page ne porte aucune date ; elle ne diffère que par le nom du fichier de données
        self.assertEqual(RE_DATE.findall(premiere), [])
        self.assertEqual(premiere.replace("chantiers.json", "seconde.json"), seconde)

    def test_les_donnees_sont_datees_du_jour(self):
        avant = date.today().strftime("%d/%m/%Y")
        self.generer(bloc("alpha-1", statut="a-venir"))
        apres = date.today().strftime("%d/%m/%Y")  # le jour a pu changer pendant l'appel
        self.assertIn(self.donnees()["engendre"], {avant, apres})

    def test_la_page_est_un_document_html_complet(self):
        self.generer(bloc("alpha-1", statut="a-venir"))
        page = self.page()
        self.assertTrue(page.startswith("<!doctype html>"))
        self.assertTrue(page.rstrip().endswith("</html>"))
        for repere in ("%PROJET%", "%DONNEES%", "%STATUTS%", "%PRIORITES%", "%COMPLEXITES%"):
            self.assertNotIn(repere, page)

    def test_la_page_est_la_meme_pour_deux_sources_au_meme_en_tete(self):
        self.generer(bloc("alpha-1", titre="Premier", statut="a-venir", module="module-a"))
        premiere = self.page()
        self.generer(bloc("beta-1", titre="Autre", statut="dette", module="module-z", priorite="haut"),
                     bloc("beta-2", titre="Encore", statut="recette"), bloc("beta-3", statut="en-vol", cdp="X"))
        self.assertEqual(self.page(), premiere)

    def test_la_page_ne_contient_aucune_donnee_de_chantier(self):
        self.generer(bloc("zeta-un", titre="Titre unique", statut="a-venir", module="module-q", mesure="Mesure rare",
                          cout="Coût rare", refs="REF-RARE", rang="3", categorie="doc"),
                     bloc("zeta-deux", titre="Autre titre", statut="dette"), bloc("zeta-trois", statut="recette"))
        page = self.page()
        for valeur in ("zeta-un", "Titre unique", "module-q", "Mesure rare", "Coût rare", "REF-RARE",
                       "zeta-deux", "Autre titre", "zeta-trois"):
            self.assertNotIn(valeur, page)

    def test_la_page_ne_depend_que_du_nom_du_projet(self):
        self.generer(bloc("alpha-1", statut="a-venir"), entete="# Chantiers — Projet Un · suite\n# libelle: x = Y")
        un = self.page()
        self.generer(bloc("beta-1", statut="dette"), entete="# Chantiers — Projet Un · tout autre texte")
        self.assertEqual(self.page(), un)
        self.generer(bloc("alpha-1", statut="a-venir"), entete="# Chantiers — Projet Deux")
        self.assertNotEqual(self.page(), un)

    def test_la_page_ne_contient_pas_innerhtml(self):
        self.generer(bloc("alpha-1", titre="Premier", statut="a-venir"))
        self.assertNotIn("innerHTML", self.page())
        self.assertNotIn("insertAdjacentHTML", self.page())
        self.assertNotIn("document.write", self.page())

    def test_la_page_construit_le_dom_par_createelement_et_textcontent(self):
        self.generer(bloc("alpha-1", statut="a-venir"))
        page = self.page()
        self.assertIn("document.createElement(", page)
        self.assertIn(".textContent", page)

    def test_la_page_contient_le_nom_du_fichier_de_donnees_et_le_lit_par_fetch(self):
        self.generer(bloc("alpha-1", statut="a-venir"))
        page = self.page()
        self.assertEqual(constante(page, "NOM_DONNEES"), "chantiers.json")
        self.assertIn("fetch(NOM_DONNEES", page)

    def test_la_page_affiche_un_echec_visible_si_les_donnees_manquent(self):
        self.generer(bloc("alpha-1", statut="a-venir"))
        page = self.page()
        self.assertIn('"Impossible de charger " + NOM_DONNEES + " ("', page)
        self.assertIn(".catch(", page)

    def test_la_page_porte_les_statuts_priorites_et_complexites_de_la_methode(self):
        self.generer(bloc("alpha-1", statut="a-venir"))
        page = self.page()
        self.assertEqual(constante(page, "STATUTS"), [list(x) for x in STATUTS])
        self.assertEqual([v for v, _ in constante(page, "PRIORITES")], ["haut", "moyen", "faible"])
        self.assertEqual([v for v, _ in constante(page, "COMPLEXITES")], ["forte", "moyenne", "faible"])

    def test_la_page_empeche_le_debordement_en_largeur_sur_telephone(self):
        self.generer(bloc("alpha-1", statut="a-venir"))
        css = re.search(r"<style>(.*?)</style>", self.page(), flags=re.S).group(1)
        self.assertRegex(css, r"(?m)^\.colonne\{[^}]*min-width:0[;}]")
        self.assertRegex(css, r"(?m)^\.carte\{[^}]*overflow-wrap:anywhere[;}]")

    def test_la_page_porte_les_themes_clair_et_sombre(self):
        self.generer(bloc("alpha-1", statut="a-venir"))
        page = self.page()
        self.assertIn("--fond:#EFE9DC;", page)
        self.assertIn("@media (prefers-color-scheme:dark)", page)
        self.assertIn(':root[data-theme="dark"]', page)

    def test_le_fichier_de_donnees_a_ses_quatre_cles_dans_l_ordre(self):
        self.generer(bloc("alpha-1", statut="a-venir"))
        donnees = self.donnees()
        self.assertEqual(list(donnees), ["projet", "engendre", "libelles", "chantiers"])
        self.assertEqual(donnees["projet"], "Essai")
        self.assertRegex(donnees["engendre"], r"^\d{2}/\d{2}/\d{4}$")

    def test_le_fichier_de_donnees_est_en_utf8_indente_avec_un_saut_de_ligne_final(self):
        self.generer(bloc("alpha-1", titre="Éléphant à l'île", statut="a-venir"))
        octets = self.json.read_bytes()
        self.assertTrue(octets.endswith(b"}\n"))
        texte = octets.decode("utf-8")
        self.assertIn("Éléphant à l'île", texte, "les accents sont écrits tels quels, pas en \\u00c9")
        self.assertIn('\n "projet": "Essai",\n', texte, "indent=1")
        self.assertEqual(texte, json.dumps(json.loads(texte), ensure_ascii=False, indent=1) + "\n")

    def test_les_entrees_sont_dans_l_ordre_du_fichier_sans_tri_ni_filtrage(self):
        ids = ["zeta", "alpha", "mu", "beta", "omega"]
        statuts = ["recette", "dette", "a-venir", "en-vol", "a-cadrer"]
        self.generer(*(bloc(i, statut=s, cdp="X" if s == "en-vol" else None, rang=str(n))
                       for n, (i, s) in enumerate(zip(ids, statuts), start=1)))
        self.assertEqual([c["id"] for c in self.chantiers()], ids)

    def test_chaque_entree_garde_toutes_ses_cles_telles_que_lues(self):
        self.generer(bloc("alpha-1", titre="Premier", statut="en-vol", cdp="Opus-CdP-Alpha", module="module-a",
                          categorie="doc", priorite="haut", complexite="forte", rang="2", mesure="Une mesure",
                          cout="2 jours", refs="R1 R2", version="v1.0.0", livrable="depot", attend="alpha-2"),
                     bloc("alpha-2", statut="a-venir", cle_inconnue="valeur"))
        premier, second = self.chantiers()
        self.assertEqual(premier, {"id": "alpha-1", "titre": "Premier", "statut": "en-vol", "cdp": "Opus-CdP-Alpha",
                                   "module": "module-a", "categorie": "doc", "priorite": "haut", "complexite": "forte",
                                   "rang": "2", "mesure": "Une mesure", "cout": "2 jours", "refs": "R1 R2",
                                   "version": "v1.0.0", "livrable": "depot", "attend": "alpha-2"})
        self.assertEqual(list(premier), ["id", "titre", "statut", "cdp", "module", "categorie", "priorite", "complexite",
                                         "rang", "mesure", "cout", "refs", "version", "livrable", "attend"])
        self.assertEqual(second, {"id": "alpha-2", "statut": "a-venir", "cle-inconnue": "valeur"})
        for entree in (premier, second):
            self.assertTrue(all(isinstance(v, str) for v in entree.values()), entree)

    def test_les_libelles_par_defaut_sont_dans_les_donnees(self):
        self.generer(bloc("alpha-1", statut="a-venir"))
        self.assertEqual(self.donnees()["libelles"], LIBELLES_DEFAUT)

    def test_les_libelles_de_l_en_tete_s_ajoutent_aux_defauts_et_les_remplacent(self):
        self.generer(bloc("alpha-1", statut="a-venir", module="module-a", categorie="doc"),
                     entete="# Chantiers — Essai\n# libelle: module-a = Module Alpha\n# libelle: doc = Notices")
        libelles = self.donnees()["libelles"]
        self.assertEqual(libelles["module-a"], "Module Alpha")
        self.assertEqual(libelles["doc"], "Notices")
        self.assertEqual(libelles["ecran"], "Écran")
        self.assertEqual(list(libelles), list(LIBELLES_DEFAUT) + ["module-a"])

    def test_une_entree_ajoutee_apparait_dans_les_donnees(self):
        self.generer(bloc("alpha-1", titre="Premier", statut="a-venir"))
        self.assertEqual([c["id"] for c in self.chantiers()], ["alpha-1"])
        sortie = self.generer(bloc("alpha-1", titre="Premier", statut="a-venir"),
                              bloc("alpha-2", titre="Ajoutée ensuite", statut="dette"))
        self.assertTrue(sortie.stdout.startswith("2 chantiers lus"))
        self.assertEqual([c["titre"] for c in self.chantiers() if c["statut"] == "dette"], ["Ajoutée ensuite"])
        self.assertNotIn("Ajoutée ensuite", self.page())

    def test_la_source_est_relue_a_chaque_generation(self):
        self.generer(bloc("alpha-1", titre="Ancien titre", statut="a-venir"))
        self.generer(bloc("alpha-1", titre="Nouveau titre", statut="a-venir"))
        self.assertNotIn("Ancien titre", self.texte_donnees())
        self.assertIn("Nouveau titre", self.texte_donnees())


class TestEchappement(CasGenerer):
    def test_le_nom_du_projet_est_echappe_dans_la_page(self):
        self.generer(bloc("alpha-1", statut="a-venir"), entete="# Chantiers — Essai & <Cie> · suite")
        page = self.page()
        self.assertIn("<title>Chantiers Essai &amp; &lt;Cie&gt;</title>", page)
        self.assertIn("<h1>Chantiers — Essai &amp; &lt;Cie&gt;</h1>", page)
        self.assertNotIn("<Cie>", page)
        self.assertEqual(self.donnees()["projet"], "Essai & <Cie>", "le JSON porte la valeur lue, sans échappement HTML")

    def test_un_nom_de_projet_qui_ressemble_a_un_repere_n_est_pas_substitue(self):
        self.generer(bloc("alpha-1", statut="a-venir"), entete="# Chantiers — %DONNEES% %STATUTS% · suite")
        page = self.page()
        self.assertIn("<title>Chantiers %DONNEES% %STATUTS%</title>", page)
        self.assertEqual(constante(page, "NOM_DONNEES"), "chantiers.json")

    def test_les_valeurs_a_caracteres_html_sont_dans_le_json_telles_quelles_et_absentes_de_la_page(self):
        self.generer(bloc("alpha-1", titre="Titre <b>gras</b> & suite", statut="a-venir",
                          mesure="<script>alert(1)</script>", cout="coût < 5 & > 2", refs="R<1>",
                          categorie="a&b", module='x"y'))
        entree = self.chantiers()[0]
        self.assertEqual(entree["titre"], "Titre <b>gras</b> & suite")
        self.assertEqual(entree["mesure"], "<script>alert(1)</script>")
        self.assertEqual(entree["module"], 'x"y')
        page = self.page()
        for valeur in ("<b>gras</b>", "alert(1)", "coût < 5", "R<1>", "a&b"):
            self.assertNotIn(valeur, page)

    def test_le_json_ne_peut_pas_fermer_un_script_de_la_page(self):
        self.generer(bloc("alpha-1", titre="</script><b>x</b>", statut="a-venir"))
        self.assertNotIn("</script><b>", self.page())
        self.assertEqual(self.chantiers()[0]["titre"], "</script><b>x</b>")


class TestEnTete(CasGenerer):
    def test_le_titre_vient_de_la_premiere_ligne(self):
        self.generer(bloc("alpha-1", statut="a-venir"), entete="# Chantiers — Projet Témoin · autre chose")
        page = self.page()
        self.assertIn("<title>Chantiers Projet Témoin</title>", page)
        self.assertIn("<h1>Chantiers — Projet Témoin</h1>", page)
        self.assertEqual(self.donnees()["projet"], "Projet Témoin")

    def test_sans_titre_c_est_le_nom_du_dossier_de_la_source(self):
        self.generer(bloc("alpha-1", statut="a-venir"), entete="# Pas de titre ici", nom_source="projet-sans-titre/chantiers.yaml")
        self.assertIn("<title>Chantiers projet-sans-titre</title>", self.page())
        self.assertEqual(self.donnees()["projet"], "projet-sans-titre")


class TestRefus(CasGenerer):
    def refuse(self, texte: str, message: str):
        self.source = self.ecrire("chantiers.yaml", texte)
        sortie = self.lancer(GENERER, self.source, self.html)
        self.assertNotEqual(sortie.code, 0, sortie.stdout)
        self.assertIn(message, sortie.stderr)
        self.assertFalse(self.html.exists(), "aucune page n'est écrite")
        self.assertFalse(self.json.exists(), "aucun fichier de données n'est écrit")

    def test_statut_inconnu(self):
        self.refuse(yaml(bloc("alpha-1", statut="termine")), "ARRÊT : statut inconnu ['termine'].")

    def test_priorite_inconnue(self):
        self.refuse(yaml(bloc("alpha-1", statut="dette", priorite="urgent")), "ARRÊT : priorite inconnu ['urgent'].")

    def test_complexite_inconnue(self):
        self.refuse(yaml(bloc("alpha-1", statut="dette", complexite="enorme")), "ARRÊT : complexite inconnu ['enorme'].")

    def test_entree_sans_statut(self):
        self.refuse(yaml(bloc("alpha-1")), "ARRÊT : 1 entrée(s) sans id ou sans statut.")

    def test_entree_sans_id(self):
        self.refuse("# Chantiers — Essai\n\n- titre: Sans id\n  statut: dette\n", "ARRÊT : 1 entrée(s) sans id ou sans statut.")

    def test_id_en_double(self):
        self.refuse(yaml(bloc("alpha-1", statut="dette"), bloc("alpha-1", statut="a-venir")),
                    "ARRÊT : id en double ['alpha-1'].")

    def test_mauvais_nombre_d_arguments(self):
        for arguments in ((), ("seul.yaml",), ("a.yaml", "b.html", "c")):
            with self.subTest(arguments=arguments):
                sortie = self.lancer(GENERER, *arguments)
                self.assertNotEqual(sortie.code, 0)
                self.assertIn("usage : generer_tableau.py <chantiers.yaml> <chantiers.html>", sortie.stderr)

    def test_source_absente(self):
        sortie = self.lancer(GENERER, self.dossier / "absent.yaml", self.html)
        self.assertNotEqual(sortie.code, 0)
        self.assertFalse(self.html.exists())
        self.assertFalse(self.json.exists())

    def test_une_page_qui_porterait_l_extension_des_donnees_est_refusee(self):
        self.source = self.ecrire("chantiers.yaml", yaml(bloc("alpha-1", statut="dette")))
        sortie = self.lancer(GENERER, self.source, self.dossier / "tableau.json")
        self.assertNotEqual(sortie.code, 0)
        self.assertIn("ARRÊT : la page ne peut pas porter l'extension .json", sortie.stderr)
        self.assertFalse((self.dossier / "tableau.json").exists())


if __name__ == "__main__":
    unittest.main()
