"""L'installateur, joué à blanc dans un dossier d'essai (INSTALLATEUR_PREFIXE) avec des doublures des commandes système.

Pas exigé par le cadrage (C3) mais utile : il prouve l'idempotence, les droits, l'empreinte de GitHub, la clé de transfert
restreinte, la désinstallation, sans toucher à la machine.
"""

import json
import os
import shutil
import subprocess
import unittest

from outils import RACINE, dossier_temporaire, ecrire, lire

from deployeur import config

# la version installée est celle du fichier VERSION de l'archive
VERSION = lire(os.path.join(RACINE, "VERSION")).strip()

CLE_GITHUB = "github.com ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOMqqnkVzrm0SdG6UOoqKLsabgH5C9okWi0dh2l9GKJl"


def stub(chemin, corps):
    ecrire(chemin, "#!/bin/sh\n" + corps, executable=True)


@unittest.skipUnless(os.geteuid() == 0 and shutil.which("ssh-keygen"), "root et ssh-keygen requis")
class TestInstallateur(unittest.TestCase):
    def setUp(self):
        self.t = dossier_temporaire(self, "inst-")
        self.p = os.path.join(self.t, "racine")
        self.bin = os.path.join(self.t, "bin")
        self.appels = os.path.join(self.t, "appels.log")
        self.archive = os.path.join(self.t, "archive")
        for d in ("etc/systemd/system", "usr/bin", "srv/outils", "srv", "var/lib", "home", "etc"):
            os.makedirs(os.path.join(self.p, d), exist_ok=True)
        ecrire(os.path.join(self.p, "etc/os-release"), "ID=debian\n")
        ecrire(os.path.join(self.p, "usr/bin/rrsync"), "#!/bin/sh\n", executable=True)
        # l'archive : comme `git archive` (sans tests/)
        os.makedirs(self.archive)
        for nom in ("installer.sh", "VERSION", "README.md", "CHANGELOG.md", "config.exemple.json"):
            shutil.copy(os.path.join(RACINE, nom), self.archive)
        for nom in ("deployeur", "systemd", "docs"):
            shutil.copytree(os.path.join(RACINE, nom), os.path.join(self.archive, nom),
                            ignore=shutil.ignore_patterns("__pycache__"))
        # doublures
        os.makedirs(self.bin)
        journal = self.appels
        for nom in ("systemctl", "useradd", "passwd", "chown", "apt-get", "ufw", "iptables", "nft", "sshd"):
            stub(os.path.join(self.bin, nom), 'echo "%s $*" >> "%s"\n' % (nom, journal))
        stub(os.path.join(self.bin, "docker"), 'echo "docker $*" >> "%s"\n[ "$1 $2" = "compose version" ] || exit 99\n' % journal)
        stub(os.path.join(self.bin, "useradd"),
             'echo "useradd $*" >> "%s"\n: > "%s/compte-cree"\n' % (journal, self.t))
        # `id` : le compte de transfert n'existe qu'une fois « créé » ; le propriétaire des zones existe sauf fichier témoin
        stub(os.path.join(self.bin, "id"),
             'for dernier in "$@"; do :; done\n'
             'if [ "$dernier" = transfert ]; then [ -e "%s/compte-cree" ]; exit $?; fi\n'
             'if [ "$dernier" = exploitant ]; then\n'
             '    [ ! -e "%s/proprietaire-absent" ] || exit 1\n'
             '    case "$*" in *-gn*) echo exploitant ;; *) echo 1000 ;; esac\n'
             '    exit 0\nfi\n'
             'exec /usr/bin/id "$@"\n' % (self.t, self.t))
        self.cle_github = os.path.join(self.t, "cle_github")
        ecrire(self.cle_github, CLE_GITHUB + "\n")
        stub(os.path.join(self.bin, "ssh-keyscan"), 'cat "%s"\n' % self.cle_github)
        self.env = dict(os.environ, PATH=self.bin + os.pathsep + os.environ["PATH"], INSTALLATEUR_PREFIXE=self.p,
                        LC_ALL="C.UTF-8")
        self.rsync = os.path.join(self.bin, "rsync")
        stub(self.rsync, "exit 0\n")

    def lancer(self, *args, archive=None, env=None):
        e = dict(self.env)
        e.update(env or {})
        return subprocess.run(["sh", os.path.join(archive or self.archive, "installer.sh")] + list(args), env=e,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

    def installer(self, *args, **kw):
        r = self.lancer(*args, **kw)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return r

    def chemin(self, *morceaux):
        return os.path.join(self.p, *morceaux)

    def mode(self, *morceaux):
        return os.stat(self.chemin(*morceaux)).st_mode & 0o7777

    def appels_systeme(self):
        return lire(self.appels).splitlines() if os.path.exists(self.appels) else []

    # --------------------------------------------------------------------------------------------
    def test_installation_complete(self):
        r = self.installer()
        self.assertEqual(os.readlink(self.chemin("opt/deployeur/courant")), VERSION)
        self.assertTrue(os.path.isfile(self.chemin("opt/deployeur/" + VERSION + "/deployeur/__main__.py")))
        self.assertFalse(os.path.exists(self.chemin("opt/deployeur/" + VERSION + "/tests")))
        # configuration : 600, valide, valeurs du projet
        self.assertEqual(self.mode("etc/deployeur"), 0o700)
        self.assertEqual(self.mode("etc/deployeur/config.json"), 0o600)
        cfg = config.charger(self.chemin("etc/deployeur/config.json"))
        app = cfg.application
        self.assertEqual((app.projet, app.dossier, app.fichier_compose), ("monprojet", "/srv/monprojet",
                                                                         "docker-compose.yml"))
        self.assertEqual((app.service_app, app.service_db, app.conteneur_db), ("app", "db", "monprojet-db-1"))
        self.assertEqual((app.volume_base, app.montage_base, app.volume_ecussons, app.volume_depots_bruts),
                         ("monprojet_pgdata", "/var/lib/postgresql/data", "monprojet_images", "monprojet_bruts"))
        self.assertEqual(app.url_sante, "http://127.0.0.1:8000/api/version")
        self.assertEqual(app.depot_url, "git@github.com:exemple/application.git")
        self.assertEqual(cfg.depot_ordres.url, "git@github.com:exemple/ordres.git")
        self.assertEqual(cfg.git.identite_nom, "Deployeur VM")
        self.assertEqual(cfg.git.identite_courriel, "deployeur@localhost")
        self.assertEqual(len(app.tables_histoire), 7)
        self.assertEqual(app.tables_histoire[0], "membres")
        self.assertIn("journal_activite", app.tables_histoire)
        self.assertEqual((app.place_min_deploiement_go, app.sauvegardes_garder, app.delai_sante_s), (3, 10, 180))
        self.assertEqual(sorted(cfg.suites), ["suite-a", "suite-b"])
        self.assertEqual(cfg.suites["suite-a"].depot, "exemple/suite-a")
        self.assertEqual(cfg.suites["suite-a"].chemin, "dist/suite_a.html")
        self.assertEqual(cfg.suites["suite-b"].dossier, "/srv/suites")
        self.assertEqual(cfg.suites["suite-b"].fichier, "suite_b.html")
        self.assertEqual({n: (z.chemin, z.place_min_go) for n, z in cfg.zones.items()},
                         {"donnees": ("/srv/donnees", 20), "echange": ("/srv/donnees/echange", 20)})
        self.assertEqual(cfg.zone_transfert, "echange")
        self.assertEqual(cfg.depots_publics, ["exemple/suite-a", "exemple/suite-b",
                                              "exemple/outils"])
        self.assertEqual(cfg.hotes_autorises, ["exemple.org"])
        # clés et known_hosts
        for cle in ("cle_ordres", "cle_app"):
            self.assertEqual(self.mode("etc/deployeur", cle), 0o600)
            self.assertTrue(lire(self.chemin("etc/deployeur", cle + ".pub")).startswith("ssh-ed25519 "))
        self.assertEqual(lire(self.chemin("etc/deployeur/known_hosts")).strip(), CLE_GITHUB)
        # état et zones
        self.assertEqual(self.mode("var/lib/deployeur"), 0o700)
        self.assertTrue(os.path.isdir(self.chemin("srv/donnees/_corbeille")))
        self.assertTrue(os.path.isdir(self.chemin("srv/donnees/echange/_corbeille")))
        self.assertEqual(self.mode("srv/donnees/echange/entree"), 0o2775)
        # compte de transfert
        appels = self.appels_systeme()
        useradd = [a for a in appels if a.startswith("useradd ")]
        self.assertEqual(len(useradd), 1)
        for morceau in ("--system", "--shell /bin/sh", "transfert"):
            self.assertIn(morceau, useradd[0])
        self.assertIn("passwd -l transfert", appels)
        self.assertEqual(self.mode("var/lib/transfert/.ssh"), 0o700)
        self.assertEqual(self.mode("var/lib/transfert/.ssh/authorized_keys"), 0o600)
        # unités et minuteurs
        for u in ("deployeur-deploiement.service", "deployeur-deploiement.timer", "deployeur-fichiers.service",
                  "deployeur-fichiers.timer"):
            self.assertEqual(lire(self.chemin("etc/systemd/system", u)), lire(os.path.join(RACINE, "systemd", u)))
        self.assertIn("systemctl daemon-reload", appels)
        self.assertIn("systemctl enable --now deployeur-deploiement.timer deployeur-fichiers.timer", appels)
        # lien pour le gestionnaire de fichiers
        self.assertEqual(os.readlink(self.chemin("srv/outils/echange")), "/srv/donnees/echange")
        # rsync présent : pas d'apt
        self.assertFalse([a for a in appels if a.startswith("apt-get")])
        # le résumé nomme les dépôts exacts et les droits des clés
        for morceau in ("exemple/ordres", "exemple/application", "Deploy keys",
                        "Allow write access", "NE PAS cocher", "ssh-ed25519"):
            self.assertIn(morceau, r.stdout)
        self.assertIn(lire(self.chemin("etc/deployeur/cle_ordres.pub")).strip(), r.stdout)
        self.assertIn(lire(self.chemin("etc/deployeur/cle_app.pub")).strip(), r.stdout)

    def test_aucun_geste_interdit(self):
        self.installer()
        self.installer("--desinstaller")
        interdits = [a for a in self.appels_systeme() if a.split()[0] in ("ufw", "iptables", "nft", "sshd")]
        self.assertEqual(interdits, [])
        for a in self.appels_systeme():
            if a.startswith("docker"):
                self.assertEqual(a, "docker compose version")
            if a.startswith("systemctl"):
                self.assertRegex(a, r"^systemctl (daemon-reload|enable --now deployeur-deploiement\.timer deployeur-fichiers\.timer"
                                    r"|disable --now deployeur-(deploiement|fichiers)\.timer)$")
        self.assertFalse(os.path.exists(self.chemin("etc/ssh")))

    def test_idempotence(self):
        self.installer()
        cles = {c: lire(self.chemin("etc/deployeur", c)) for c in ("cle_ordres", "cle_app")}
        with open(self.chemin("etc/deployeur/config.json"), "a", encoding="utf-8") as f:
            f.write("\n")
        # une modification locale de la configuration est gardée
        cfg = json.loads(lire(self.chemin("etc/deployeur/config.json")))
        cfg["application"]["sauvegardes_garder"] = 7
        ecrire(self.chemin("etc/deployeur/config.json"), json.dumps(cfg))
        os.chmod(self.chemin("etc/deployeur/config.json"), 0o600)
        r = self.installer()
        self.assertIn("gardée telle quelle", r.stdout)
        self.assertEqual(json.loads(lire(self.chemin("etc/deployeur/config.json")))["application"]["sauvegardes_garder"], 7)
        for c, contenu in cles.items():
            self.assertEqual(lire(self.chemin("etc/deployeur", c)), contenu)
            self.assertIn("existe déjà, gardée", r.stdout)
        self.assertEqual(len([a for a in self.appels_systeme() if a.startswith("useradd ")]), 1)    # compte créé une fois
        self.assertIn("le compte transfert existe déjà", r.stdout)
        # addendum 2 : la réinstallation copie dans un dossier neuf voisin et y bascule « courant »
        self.assertEqual(os.readlink(self.chemin("opt/deployeur/courant")), VERSION + ".nouveau")
        self.assertFalse(os.path.exists(self.chemin("opt/deployeur/" + VERSION)))
        self.assertIn("quelque chose existe déjà à /srv/outils/echange", r.stdout)

    def test_mise_a_jour_bascule_le_lien(self):
        self.installer()
        ecrire(os.path.join(self.archive, "VERSION"), "0.2.0\n")
        self.installer()
        self.assertEqual(os.readlink(self.chemin("opt/deployeur/courant")), "0.2.0")
        self.assertTrue(os.path.isdir(self.chemin("opt/deployeur/" + VERSION)))

    def test_lien_existant_n_est_pas_touche(self):
        os.makedirs(self.chemin("srv/outils/echange"))
        ecrire(self.chemin("srv/outils/echange/important"), "x")
        r = self.installer()
        self.assertFalse(os.path.islink(self.chemin("srv/outils/echange")))
        self.assertTrue(os.path.exists(self.chemin("srv/outils/echange/important")))
        self.assertIn("je n'y touche pas", r.stdout)

    def test_empreinte_de_github_inattendue_arrete_l_installateur(self):
        autre = os.path.join(self.t, "cle_autre")
        subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", autre], check=True)
        ecrire(self.cle_github, "github.com " + lire(autre + ".pub").strip() + "\n")
        r = self.lancer()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("empreinte de github.com inattendue", r.stderr)
        self.assertFalse(os.path.exists(self.chemin("etc/deployeur/known_hosts")))
        self.assertFalse([a for a in self.appels_systeme() if a.startswith("systemctl")])

    def test_reseau_muet_arrete_l_installateur(self):
        ecrire(self.cle_github, "")
        r = self.lancer()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("ssh-keyscan", r.stderr)

    def test_zone_interdite_refusee_avant_tout_geste_sur_les_zones(self):
        texte = lire(os.path.join(self.archive, "installer.sh"))
        modifie = texte.replace("echange|/srv/donnees/echange|20", "echange|/etc/mazone|20")
        self.assertNotEqual(texte, modifie)
        ecrire(os.path.join(self.archive, "installer.sh"), modifie)
        r = self.lancer()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("configuration", r.stderr)
        self.assertFalse(os.path.exists(self.chemin("etc/mazone")))
        self.assertFalse(os.path.exists(self.chemin("srv/donnees")))
        self.assertFalse([a for a in self.appels_systeme() if a.startswith(("useradd", "systemctl"))])

    def test_rsync_manquant_est_installe_par_apt(self):
        os.remove(self.rsync)
        if shutil.which("rsync", path=self.env["PATH"]):
            self.skipTest("un vrai rsync est installé sur la machine d'essai")
        self.installer()
        self.assertIn("apt-get install -y rsync", self.appels_systeme())

    def test_rrsync_absent_arrete_l_installateur(self):
        os.remove(self.chemin("usr/bin/rrsync"))
        if os.path.exists("/usr/bin/rrsync"):
            self.skipTest("un vrai rrsync est installé sur la machine d'essai")
        r = self.lancer()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("rrsync", r.stderr)

    def test_systeme_non_debian_refuse(self):
        ecrire(self.chemin("etc/os-release"), "ID=fedora\n")
        r = self.lancer()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("Debian", r.stderr)

    def test_depuis_un_mauvais_dossier(self):
        isole = os.path.join(self.t, "seul")
        os.makedirs(isole)
        shutil.copy(os.path.join(RACINE, "installer.sh"), isole)
        r = self.lancer(archive=isole)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("dossier de l'archive", r.stderr)

    # -- clé de transfert -----------------------------------------------------------------------
    def cle_pc(self, nom="pc"):
        chemin = os.path.join(self.t, nom)
        subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", "pc@maison", "-f", chemin], check=True)
        return lire(chemin + ".pub").strip()

    def test_cle_de_transfert_restreinte_et_non_doublee(self):
        cle = self.cle_pc()
        self.installer("--cle-transfert", cle)
        ak = lire(self.chemin("var/lib/transfert/.ssh/authorized_keys"))
        self.assertEqual(ak, 'restrict,command="/usr/bin/rrsync -wo -no-del /srv/donnees/echange/entree" %s\n' % cle)
        r = self.installer("--cle-transfert", cle)
        self.assertIn("déjà autorisée", r.stdout)
        self.assertEqual(lire(self.chemin("var/lib/transfert/.ssh/authorized_keys")), ak)
        autre = self.cle_pc("autre")
        self.installer("--cle-transfert", autre)
        lignes = lire(self.chemin("var/lib/transfert/.ssh/authorized_keys")).splitlines()
        self.assertEqual(len(lignes), 2)
        self.assertEqual(self.mode("var/lib/transfert/.ssh/authorized_keys"), 0o600)

    def test_cle_de_transfert_invalide_refusee(self):
        cle = self.cle_pc()
        corps = cle.split()[1]
        mauvaises = [
            "n'importe quoi", 'command="/bin/sh" ' + cle, "no-pty " + cle, cle + '"; touch /tmp/x; "',
            cle + "\nssh-ed25519 AAAA ligne2", "", "ssh-ed25519", "ssh-dss " + corps, cle.replace(corps, corps + "$(id)"),
            cle + " \\",
        ]
        for m in mauvaises:
            r = self.lancer("--cle-transfert", m)
            self.assertNotEqual(r.returncode, 0, repr(m))
            ak = self.chemin("var/lib/transfert/.ssh/authorized_keys")
            self.assertEqual(lire(ak) if os.path.exists(ak) else "", "", repr(m))

    def test_option_inconnue_et_aide(self):
        r = self.lancer("--n-importe-quoi")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("option inconnue", r.stderr)
        r = self.lancer("--aide")
        self.assertEqual(r.returncode, 0)
        self.assertIn("--cle-transfert", r.stdout)
        r = self.lancer("--cle-transfert")
        self.assertNotEqual(r.returncode, 0)

    # -- désinstallation ------------------------------------------------------------------------
    def test_desinstallation_garde_l_essentiel(self):
        self.installer("--cle-transfert", self.cle_pc())
        r = self.installer("--desinstaller")
        self.assertFalse(os.path.exists(self.chemin("opt/deployeur")))
        for u in ("deployeur-deploiement.service", "deployeur-deploiement.timer", "deployeur-fichiers.service",
                  "deployeur-fichiers.timer"):
            self.assertFalse(os.path.exists(self.chemin("etc/systemd/system", u)))
        appels = self.appels_systeme()
        self.assertIn("systemctl disable --now deployeur-deploiement.timer", appels)
        self.assertIn("systemctl disable --now deployeur-fichiers.timer", appels)
        self.assertTrue(os.path.isfile(self.chemin("etc/deployeur/config.json")))
        self.assertTrue(os.path.isfile(self.chemin("etc/deployeur/cle_ordres")))
        self.assertTrue(os.path.isdir(self.chemin("var/lib/deployeur")))
        self.assertTrue(os.path.isdir(self.chemin("srv/donnees/echange/entree")))
        self.assertTrue(os.path.isfile(self.chemin("var/lib/transfert/.ssh/authorized_keys")))
        self.assertIn("GARDÉ", r.stdout)
        # on peut réinstaller ensuite
        self.installer()
        self.assertEqual(os.readlink(self.chemin("opt/deployeur/courant")), VERSION)

    # -- addendum 2 : propriétaire des zones et de entree/ ---------------------------------------
    def chowns(self):
        return [a for a in self.appels_systeme() if a.startswith("chown ")]

    def test_addendum2_proprietaire_des_zones_creees_et_de_entree(self):
        self.installer()
        chowns = self.chowns()
        for zone in ("srv/donnees", "srv/donnees/echange"):
            self.assertIn("chown exploitant:exploitant " + self.chemin(zone), chowns)
        self.assertIn("chown exploitant:transfert " + self.chemin("srv/donnees/echange/entree"), chowns)
        self.assertEqual(self.mode("srv/donnees/echange/entree"), 0o2775)

    def test_addendum2_une_zone_qui_existe_deja_n_est_pas_touchee(self):
        os.makedirs(self.chemin("srv/donnees"))
        r = self.installer()
        self.assertIn("existe déjà", r.stdout)
        self.assertNotIn("chown exploitant:exploitant " + self.chemin("srv/donnees"), self.chowns())
        self.assertIn("chown exploitant:exploitant " + self.chemin("srv/donnees/echange"), self.chowns())
        self.assertIn("chown exploitant:transfert " + self.chemin("srv/donnees/echange/entree"), self.chowns())

    def test_addendum2_proprietaire_inexistant_arrete_l_installateur_avant_tout_geste(self):
        ecrire(os.path.join(self.t, "proprietaire-absent"), "")
        r = self.lancer()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("exploitant", r.stderr)
        self.assertIn("n'existe pas", r.stderr)
        self.assertFalse(os.path.exists(self.chemin("opt/deployeur/" + VERSION)))
        self.assertFalse(os.path.exists(self.chemin("srv/donnees")))
        self.assertFalse([a for a in self.appels_systeme() if a.startswith(("useradd", "systemctl"))])

    def test_addendum2_le_proprietaire_est_dans_le_bloc_des_valeurs_du_projet(self):
        texte = lire(os.path.join(RACINE, "installer.sh"))
        bloc = texte[texte.index("# Valeurs de ce projet"):texte.index("# Fin des valeurs de ce projet")]
        self.assertIn("PROPRIETAIRE_ZONES=exploitant\n", bloc)

    # -- addendum 2 : la réinstallation ne retire pas le programme sous un passage en cours ------
    def test_addendum2_reinstallation_alterne_les_dossiers_et_retire_l_ancien(self):
        self.installer()
        self.assertEqual(os.readlink(self.chemin("opt/deployeur/courant")), VERSION)
        r = self.installer()
        self.assertEqual(os.readlink(self.chemin("opt/deployeur/courant")), VERSION + ".nouveau")
        self.assertTrue(os.path.isfile(self.chemin("opt/deployeur/" + VERSION + ".nouveau/deployeur/__main__.py")))
        self.assertFalse(os.path.exists(self.chemin("opt/deployeur/" + VERSION)))
        self.assertIn("retiré (aucun passage en cours)", r.stdout)
        self.installer()
        self.assertEqual(os.readlink(self.chemin("opt/deployeur/courant")), VERSION)
        self.assertFalse(os.path.exists(self.chemin("opt/deployeur/" + VERSION + ".nouveau")))
        self.assertTrue(os.path.isfile(self.chemin("opt/deployeur/courant/deployeur/__main__.py")))

    def tenir_verrou(self, nom):
        import fcntl
        os.makedirs(self.chemin("var/lib/deployeur"), exist_ok=True)
        f = open(self.chemin("var/lib/deployeur", "verrou-" + nom), "a")
        fcntl.flock(f, fcntl.LOCK_EX)
        self.addCleanup(f.close)
        return f

    def test_addendum2_un_passage_en_cours_garde_l_ancien_dossier(self):
        self.installer()
        for nom in ("deploiement", "fichiers"):
            verrou = self.tenir_verrou(nom)
            r = self.installer(env={"INSTALLATEUR_ATTENTE_VERROU_S": "2"})
            # « courant » est déjà basculé sur le dossier neuf, l'ancien est laissé sous le passage en cours
            self.assertIn("LAISSÉ en place", r.stdout)
            self.assertTrue(os.path.isfile(self.chemin("opt/deployeur/" + VERSION + "/deployeur/__main__.py")))
            cible = os.readlink(self.chemin("opt/deployeur/courant"))
            self.assertEqual(cible, VERSION + ".nouveau")
            verrou.close()
            # le passage est fini : une réinstallation suivante repart sur des dossiers nets
            self.installer()
            self.assertEqual(os.readlink(self.chemin("opt/deployeur/courant")), VERSION)
            self.assertFalse(os.path.exists(self.chemin("opt/deployeur/" + VERSION + ".nouveau")))

    def test_addendum2_l_installateur_attend_la_fin_du_passage_puis_retire_l_ancien(self):
        import threading
        import time
        self.installer()
        verrou = self.tenir_verrou("deploiement")
        threading.Timer(1.5, verrou.close).start()
        debut = time.time()
        r = self.installer(env={"INSTALLATEUR_ATTENTE_VERROU_S": "30"})
        self.assertGreaterEqual(time.time() - debut, 1.0)
        self.assertIn("retiré (aucun passage en cours)", r.stdout)
        self.assertFalse(os.path.exists(self.chemin("opt/deployeur/" + VERSION)))
        self.assertEqual(os.readlink(self.chemin("opt/deployeur/courant")), VERSION + ".nouveau")

    def test_addendum2_mise_a_jour_de_version_ne_retire_pas_la_precedente(self):
        self.installer()
        ecrire(os.path.join(self.archive, "VERSION"), "0.2.0\n")
        r = self.installer()
        self.assertIn("aucun ancien dossier de cette version à retirer", r.stdout)
        self.assertTrue(os.path.isdir(self.chemin("opt/deployeur/" + VERSION)))
        self.assertEqual(os.readlink(self.chemin("opt/deployeur/courant")), "0.2.0")


if __name__ == "__main__":
    unittest.main()
