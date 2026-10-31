"""Tests de generer_tableau.py : une page HTML tirée de chantiers.yaml, déterministe, échappée, une colonne par statut.

Chaque test bâtit sa source dans un dossier temporaire (voir outils_tests.py) et appelle le script en
ligne de commande.
"""
import re
import unittest
from datetime import date

from .outils_tests import GENERER, CasTemporaire, bloc, yaml

STATUTS = [("a-venir", "À venir"), ("a-cadrer", "À cadrer"), ("en-vol", "En vol"),
           ("dette", "Dette"), ("recette", "Recetté")]
RE_DATE = re.compile(r"\d{2}/\d{2}/\d{4}")


def colonnes(html: str) -> dict:
    """{statut: (libellé, total affiché, [titres des cartes])} d'après les sections de la page."""
    trouvees = {}
    for m in re.finditer(r'<section class="colonne st-(\S+?)" data-statut="\S+?"><h2>(.*?)<b>(\d+)</b></h2>(.*?)</section>',
                         html, flags=re.S):
        trouvees[m.group(1)] = (m.group(2), int(m.group(3)), re.findall(r"<h3>(.*?)</h3>", m.group(4)))
    return trouvees


class CasGenerer(CasTemporaire):
    def setUp(self):
        super().setUp()
        self.html = self.dossier / "chantiers.html"

    def generer(self, *blocs: str, entete: str = "# Chantiers — Essai", nom_source: str = "chantiers.yaml"):
        self.source = self.ecrire(nom_source, yaml(*blocs, entete=entete))
        sortie = self.lancer(GENERER, self.source, self.html)
        self.assertEqual(sortie.code, 0, sortie.stdout + sortie.stderr)
        return sortie

    def page(self) -> str:
        return self.html.read_text(encoding="utf-8")


class TestGeneration(CasGenerer):
    def test_la_sortie_resume_ce_qui_a_ete_lu(self):
        sortie = self.generer(bloc("alpha-1", statut="a-venir"), bloc("alpha-2", statut="dette"),
                              bloc("alpha-3", statut="dette"))
        self.assertTrue(sortie.stdout.startswith("3 chantiers lus · "), sortie.stdout)
        self.assertIn('"a-venir": 1', sortie.stdout)
        self.assertIn('"dette": 2', sortie.stdout)
        self.assertIn('"recette": 0', sortie.stdout)
        self.assertTrue(sortie.stdout.rstrip().endswith(f"écrit dans {self.html}"), sortie.stdout)

    def test_deux_generations_de_la_meme_source_sont_identiques_hors_la_date(self):
        self.generer(bloc("alpha-1", titre="Premier", statut="a-venir", module="module-a", priorite="haut"),
                     bloc("alpha-2", titre="Deuxième", statut="recette", module="module-b", complexite="forte"))
        premiere = self.page()
        seconde_sortie = self.dossier / "seconde.html"
        self.assertEqual(self.lancer(GENERER, self.source, seconde_sortie).code, 0)
        seconde = seconde_sortie.read_text(encoding="utf-8")
        self.assertEqual(RE_DATE.sub("<date>", premiere), RE_DATE.sub("<date>", seconde))
        self.assertEqual(len(RE_DATE.findall(premiere)), 1)

    def test_la_page_est_datee_du_jour(self):
        self.generer(bloc("alpha-1", statut="a-venir"))
        self.assertIn(f"engendré le {date.today().strftime('%d/%m/%Y')}", self.page())

    def test_la_page_est_un_document_html_complet(self):
        self.generer(bloc("alpha-1", statut="a-venir"))
        page = self.page()
        self.assertTrue(page.startswith("<!doctype html>"))
        self.assertTrue(page.rstrip().endswith("</html>"))
        for repere in ("%PROJET%", "%COLONNES%", "%CHIPS%", "%DATE%", "%TOTAL%", "%DETTES%"):
            self.assertNotIn(repere, page)

    def test_chaque_statut_a_sa_colonne_dans_l_ordre_de_la_methode(self):
        self.generer(*(bloc(f"alpha-{n}", titre=f"Titre {statut}", statut=statut)
                       for n, (statut, _) in enumerate(STATUTS, start=1)))
        trouvees = colonnes(self.page())
        self.assertEqual(list(trouvees), [statut for statut, _ in STATUTS])
        for statut, libelle in STATUTS:
            self.assertEqual(trouvees[statut], (libelle, 1, [f"Titre {statut}"]), statut)

    def test_une_colonne_sans_entree_est_affichee_vide(self):
        self.generer(bloc("alpha-1", titre="Seul", statut="dette"))
        trouvees = colonnes(self.page())
        self.assertEqual(len(trouvees), 5)
        self.assertEqual(trouvees["dette"], ("Dette", 1, ["Seul"]))
        for statut in ("a-venir", "a-cadrer", "en-vol", "recette"):
            self.assertEqual(trouvees[statut][1:], (0, []), statut)

    def test_les_cartes_vont_dans_la_colonne_de_leur_statut(self):
        self.generer(bloc("alpha-1", titre="Un", statut="en-vol", cdp="Opus-CdP-Alpha"),
                     bloc("alpha-2", titre="Deux", statut="en-vol", cdp="Opus-CdP-Alpha"),
                     bloc("alpha-3", titre="Trois", statut="a-cadrer"))
        trouvees = colonnes(self.page())
        self.assertEqual(trouvees["en-vol"][1:], (2, ["Un", "Deux"]))
        self.assertEqual(trouvees["a-cadrer"][1:], (1, ["Trois"]))

    def test_une_carte_sans_titre_porte_son_id(self):
        self.generer(bloc("alpha-1", statut="a-venir"))
        self.assertEqual(colonnes(self.page())["a-venir"][2], ["alpha-1"])

    def test_tri_par_rang_puis_ordre_du_fichier(self):
        self.generer(bloc("a", titre="Sans rang", statut="a-venir"),
                     bloc("b", titre="Rang 2", statut="a-venir", rang="2"),
                     bloc("c", titre="Rang 1", statut="a-venir", rang="1"),
                     bloc("d", titre="Sans rang bis", statut="a-venir"))
        self.assertEqual(colonnes(self.page())["a-venir"][2], ["Rang 1", "Rang 2", "Sans rang", "Sans rang bis"])

    def test_une_entree_ajoutee_apparait(self):
        self.generer(bloc("alpha-1", titre="Premier", statut="a-venir"))
        avant = self.page()
        self.assertNotIn("Ajoutée ensuite", avant)
        self.assertIn('<b id="compte">1</b>', avant)
        sortie = self.generer(bloc("alpha-1", titre="Premier", statut="a-venir"),
                              bloc("alpha-2", titre="Ajoutée ensuite", statut="dette"))
        apres = self.page()
        self.assertTrue(sortie.stdout.startswith("2 chantiers lus"))
        self.assertEqual(colonnes(apres)["dette"][1:], (1, ["Ajoutée ensuite"]))
        self.assertIn('<b id="compte">2</b>', apres)
        self.assertIn("entrées affichées sur 2 · 1 en dette", apres)

    def test_le_compte_des_dettes_est_dans_l_en_tete(self):
        self.generer(bloc("alpha-1", statut="dette"), bloc("alpha-2", statut="dette"), bloc("alpha-3", statut="a-venir"))
        self.assertIn("entrées affichées sur 3 · 2 en dette", self.page())

    def test_la_source_est_relue_a_chaque_generation(self):
        self.generer(bloc("alpha-1", titre="Ancien titre", statut="a-venir"))
        self.generer(bloc("alpha-1", titre="Nouveau titre", statut="a-venir"))
        self.assertNotIn("Ancien titre", self.page())
        self.assertIn("Nouveau titre", self.page())


class TestEchappement(CasGenerer):
    def test_un_titre_avec_des_caracteres_html_sort_echappe(self):
        self.generer(bloc("alpha-1", titre="Titre <b>gras</b> & suite", statut="a-venir"))
        page = self.page()
        self.assertIn("<h3>Titre &lt;b&gt;gras&lt;/b&gt; &amp; suite</h3>", page)
        self.assertNotIn("<b>gras</b>", page)
        self.assertNotIn("& suite", page)

    def test_le_caractere_inferieur_seul_est_echappe(self):
        self.generer(bloc("alpha-1", titre="a<b", statut="a-venir"))
        page = self.page()
        self.assertIn("<h3>a&lt;b</h3>", page)
        self.assertNotIn("<h3>a<b", page)

    def test_les_autres_champs_de_la_carte_sont_echappes(self):
        self.generer(bloc("alpha-1", titre="T", statut="a-venir", mesure="<script>alert(1)</script>",
                          cout="coût < 5 & > 2", refs="R<1>", categorie="a&b", module="mod<x>"))
        page = self.page()
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", page)
        self.assertNotIn("<script>alert(1)", page)
        self.assertIn("coût &lt; 5 &amp; &gt; 2", page)
        self.assertIn('<span class="ref">R&lt;1&gt;</span>', page)
        self.assertIn('<span class="cat">A&amp;b</span>', page)
        self.assertIn('data-mod="mod&lt;x&gt;"', page)

    def test_une_guillemet_dans_un_attribut_est_echappe(self):
        self.generer(bloc("alpha-1", titre="T", statut="a-venir", module='x"y'))
        page = self.page()
        self.assertIn('data-mod="x&quot;y"', page)
        self.assertNotIn('data-mod="x"y"', page)

    def test_le_nom_du_projet_est_echappe(self):
        self.generer(bloc("alpha-1", statut="a-venir"), entete="# Chantiers — Essai & <Cie> · suite")
        page = self.page()
        self.assertIn("<title>Chantiers Essai &amp; &lt;Cie&gt;</title>", page)
        self.assertNotIn("<Cie>", page)

    def test_les_libelles_sont_echappes(self):
        self.generer(bloc("alpha-1", statut="a-venir", module="module-a"),
                     entete="# Chantiers — Essai\n# libelle: module-a = Module <A> & Cie")
        page = self.page()
        self.assertIn("Module &lt;A&gt; &amp; Cie", page)
        self.assertNotIn("Module <A>", page)


class TestEnTeteEtLibelles(CasGenerer):
    def test_le_titre_vient_de_la_premiere_ligne(self):
        self.generer(bloc("alpha-1", statut="a-venir"), entete="# Chantiers — Projet Témoin · autre chose")
        page = self.page()
        self.assertIn("<title>Chantiers Projet Témoin</title>", page)
        self.assertIn("<h1>Chantiers — Projet Témoin</h1>", page)

    def test_sans_titre_c_est_le_nom_du_dossier_de_la_source(self):
        self.generer(bloc("alpha-1", statut="a-venir"), entete="# Pas de titre ici", nom_source="projet-sans-titre/chantiers.yaml")
        self.assertIn("<title>Chantiers projet-sans-titre</title>", self.page())

    def test_libelle_donne_par_l_en_tete(self):
        self.generer(bloc("alpha-1", statut="a-venir", module="module-a", categorie="doc"),
                     entete="# Chantiers — Essai\n# libelle: module-a = Module Alpha\n# libelle: doc = Notices")
        page = self.page()
        self.assertIn('<span class="mod">Module Alpha</span>', page)
        self.assertIn('<span class="cat">Notices</span>', page)
        self.assertIn("Module Alpha<b>1</b>", page, "le filtre porte aussi le libellé")

    def test_libelle_par_defaut(self):
        self.generer(bloc("alpha-1", statut="a-venir", module="module-a", categorie="outillage"),
                     bloc("alpha-2", statut="a-venir", module="ecran"))
        page = self.page()
        self.assertIn('<span class="mod">Module a</span>', page, "tirets en espaces, première lettre en capitale")
        self.assertIn('<span class="cat">Outillage</span>', page)
        self.assertIn('<span class="mod">Écran</span>', page)

    def test_priorite_et_complexite_par_defaut_et_donnees(self):
        self.generer(bloc("alpha-1", statut="a-venir"),
                     bloc("alpha-2", statut="a-venir", priorite="haut", complexite="forte"),
                     bloc("alpha-3", statut="a-venir", priorite="faible", complexite="faible"))
        page = self.page()
        self.assertIn('class="carte pr-moyen" data-mod="" data-pr="moyen" data-cx="moyenne"', page)
        self.assertIn('class="carte pr-haut" data-mod="" data-pr="haut" data-cx="forte"', page)
        self.assertIn('class="carte pr-faible" data-mod="" data-pr="faible" data-cx="faible"', page)
        for points in ('">●●●</span>', '">●●</span>', '">●</span>'):
            self.assertIn(points, page)

    def test_les_filtres_ne_proposent_que_les_valeurs_presentes(self):
        self.generer(bloc("alpha-1", statut="a-venir", module="module-a", priorite="haut"),
                     bloc("alpha-2", statut="dette", module="module-b", priorite="haut"))
        page = self.page()
        self.assertIn('data-champ="mod" data-val="module-a"', page)
        self.assertIn('data-champ="mod" data-val="module-b"', page)
        self.assertIn('data-champ="pr" data-val="haut"', page)
        self.assertNotIn('data-champ="pr" data-val="faible"', page)
        self.assertIn('data-champ="st" data-val="dette"', page)
        self.assertNotIn('data-champ="st" data-val="recette"', page)


class TestRefus(CasGenerer):
    def refuse(self, texte: str, message: str):
        self.source = self.ecrire("chantiers.yaml", texte)
        sortie = self.lancer(GENERER, self.source, self.html)
        self.assertNotEqual(sortie.code, 0, sortie.stdout)
        self.assertIn(message, sortie.stderr)
        self.assertFalse(self.html.exists(), "aucune page n'est écrite")

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


if __name__ == "__main__":
    unittest.main()
