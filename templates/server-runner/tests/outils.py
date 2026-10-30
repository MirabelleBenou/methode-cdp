"""Doublures et outils des tests : faux docker, faux serveur de santé, dépôts Git locaux, dossiers temporaires.

Aucun test n'écrit hors de son dossier temporaire ; aucun ne touche au réseau ni à un vrai Docker.
"""

import http.server
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from unittest import mock

RACINE_TESTS = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(RACINE_TESTS)
if RACINE not in sys.path:
    sys.path.insert(0, RACINE)

from deployeur import config, passage, reseau  # noqa: E402

SH_DUMP = 'pg_dump -Fc -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
SH_LIRE = 'psql -X -q -A -t -F "|" --set=ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'

FICHIERS_A = {
    "VERSION": "1.0055\n",
    "docker-compose.yml": "services: {}\n",
    "app/main.py": "print('a')\n",
    "app/ancien.py": "ancien\n",
    "scripts/start.sh": ("#!/bin/sh\necho a\n", True),
}

ENV_GIT = {
    "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_SYSTEM": "/dev/null",
    "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t",
}


def git(*args, cwd=None):
    env = dict(os.environ)
    env.update(ENV_GIT)
    r = subprocess.run(["git"] + list(args), cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if r.returncode != 0:
        raise RuntimeError("git %s : %s" % (" ".join(args), r.stderr.decode("utf-8", "replace")))
    return r.stdout.decode("utf-8", "replace")


def dossier_temporaire(tc, prefixe="dep-"):
    base = "/tmp" if os.path.isdir("/tmp") else None
    d = os.path.realpath(tempfile.mkdtemp(prefix=prefixe, dir=base))
    tc.addCleanup(shutil.rmtree, d, True)
    return d


def ecrire(chemin, contenu, executable=False):
    os.makedirs(os.path.dirname(chemin), exist_ok=True)
    mode = "wb" if isinstance(contenu, bytes) else "w"
    with open(chemin, mode) as f:
        f.write(contenu)
    os.chmod(chemin, 0o755 if executable else 0o644)


def lire(chemin):
    with open(chemin, "rb") as f:
        return f.read().decode("utf-8")


class Reponse:
    def __init__(self, code, entetes, donnees):
        self.code, self.headers, self._d, self._pos = code, entetes, donnees, 0

    def read(self, n=-1):
        if n is None or n < 0:
            n = len(self._d) - self._pos
        out = self._d[self._pos:self._pos + n]
        self._pos += len(out)
        return out

    def close(self):
        pass


class FauxReseau:
    """Remplace le transport HTTPS de ``reseau`` : url -> (code, en-têtes, octets). Journalise les adresses."""

    def __init__(self):
        self.contenus = {}
        self.demandes = []

    def ajouter(self, url, donnees, code=200, entetes=None):
        e = {"Content-Length": str(len(donnees))} if code == 200 else {}
        e.update(entetes or {})
        self.contenus[url] = (code, e, donnees)

    def redirection(self, url, vers):
        self.contenus[url] = (302, {"Location": vers}, b"")

    def requete(self, url, delai):
        self.demandes.append(url)
        if url not in self.contenus:
            raise reseau.ErreurReseau("réponse HTTP 404 pour %s" % url)
        code, entetes, donnees = self.contenus[url]
        return code, entetes, Reponse(code, entetes, donnees)


class Env:
    """Un environnement complet : dossier Compose, dépôts, faux docker, serveur de santé, zones, suites."""

    def __init__(self, tc, histoire=("membres", "evenements")):
        self.tc = tc
        self.racine = dossier_temporaire(tc)
        r = self.racine
        self.app = os.path.join(r, "app")
        self.src = os.path.join(r, "app_src")
        self.ordres_remote = os.path.join(r, "ordres.git")
        self.ordres_w = os.path.join(r, "ordres_w")
        self.etat_dir = os.path.join(r, "etat")
        self.bin = os.path.join(r, "bin")
        self.suites_dir = os.path.join(r, "suites")
        self.zone_donnees = os.path.join(r, "zones", "donnees")
        self.zone_fichiers = os.path.join(r, "zones", "donnees", "fichiers")
        self.etat_docker = os.path.join(r, "docker_etat.json")
        self.journal_docker = os.path.join(r, "docker_journal.jsonl")
        self.histoire = list(histoire)
        self.sortie = []
        self.faux_reseau = FauxReseau()
        for d in (self.app, self.suites_dir, self.zone_donnees, self.zone_fichiers, self.bin):
            os.makedirs(d, exist_ok=True)
        # faux docker
        script = os.path.join(self.bin, "docker")
        with open(os.path.join(RACINE_TESTS, "faux_docker.py"), "r", encoding="utf-8") as f:
            corps = f.read()
        with open(script, "w", encoding="utf-8") as f:
            f.write("#!%s\n%s" % (sys.executable, corps))
        os.chmod(script, 0o755)
        # dépôts
        os.makedirs(self.src)
        git("init", "-q", "-b", "main", cwd=self.src)
        git("init", "-q", "--bare", "-b", "main", self.ordres_remote)
        git("clone", "-q", self.ordres_remote, self.ordres_w)
        ecrire(os.path.join(self.ordres_w, "LISEZ_MOI.md"), "ordres\n")
        git("add", "-A", cwd=self.ordres_w)
        git("commit", "-q", "-m", "init", cwd=self.ordres_w)
        git("push", "-q", "origin", "HEAD:refs/heads/main", cwd=self.ordres_w)
        self.commit_a = self.commit_app(FICHIERS_A)
        self.poser_dossier(self.commit_a)
        # état du faux docker
        pre = "com.docker.compose.project"
        self.docker_ecrire({
            "projet": "monprojet", "dossier": self.app, "fichier": "docker-compose.yml",
            "conteneur_db": "monprojet-db-1", "image": "postgres:16",
            "etiquettes_db": {pre: "monprojet", pre + ".working_dir": self.app,
                              "com.docker.compose.service": "db"},
            "montages": [{"Type": "volume", "Name": "monprojet_pgdata", "Destination": "/var/lib/postgresql/data"}],
            "volumes": {v: {pre: "monprojet"} for v in ("monprojet_pgdata", "monprojet_images", "monprojet_bruts")},
            "services": {"app": "running", "db": "running"},
            "revision": "0039",
            "tables": {"membres": 10, "evenements": 20, "autre": 3, "alembic_version": 1},
            "version": "1.0055",
        })
        # environnement du processus
        patch = mock.patch.dict(os.environ, dict(
            ENV_GIT, PATH=self.bin + os.pathsep + os.environ.get("PATH", ""),
            FAUX_DOCKER_ETAT=self.etat_docker, FAUX_DOCKER_JOURNAL=self.journal_docker))
        patch.start()
        tc.addCleanup(patch.stop)
        p2 = mock.patch.object(reseau, "_requete", self.faux_reseau.requete)
        p2.start()
        tc.addCleanup(p2.stop)
        # serveur de santé
        env = self

        class Gestionnaire(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                e = env.docker_etat()
                if e.get("sante") == "arret":
                    self.send_response(503)
                    self.end_headers()
                    return
                corps = json.dumps({"version": e["version"]}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(corps)))
                self.end_headers()
                self.wfile.write(corps)

            def log_message(self, *a):
                pass

        self.serveur = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Gestionnaire)
        self.serveur.daemon_threads = True
        threading.Thread(target=self.serveur.serve_forever, daemon=True).start()
        tc.addCleanup(self.serveur.server_close)
        tc.addCleanup(self.serveur.shutdown)
        self.url_sante = "http://127.0.0.1:%d/api/version" % self.serveur.server_address[1]
        self.dict_config = self._config()

    # -- dépôt de l'application ------------------------------------------------------------------
    def commit_app(self, fichiers, retirer=()):
        for chemin, contenu in fichiers.items():
            exe = False
            if isinstance(contenu, tuple):
                contenu, exe = contenu
            ecrire(os.path.join(self.src, chemin), contenu, exe)
        for chemin in retirer:
            os.remove(os.path.join(self.src, chemin))
        git("add", "-A", cwd=self.src)
        git("commit", "-q", "--allow-empty", "-m", "commit %s" % time.time(), cwd=self.src)
        return git("rev-parse", "HEAD", cwd=self.src).strip()

    def poser_dossier(self, commit):
        """Le dossier Compose reçoit exactement l'archive du commit, plus des fichiers hors archive."""
        archive = os.path.join(self.racine, "a.tar")
        with open(archive, "wb") as f:
            r = subprocess.run(["git", "-C", self.src, "archive", "--format=tar", commit], stdout=f)
        assert r.returncode == 0
        subprocess.run(["tar", "-x", "-C", self.app, "-f", archive], check=True)
        ecrire(os.path.join(self.app, ".env"), "SECRET=abc\n")
        ecrire(os.path.join(self.app, ".env.SAVE"), "SECRET=old\n")
        ecrire(os.path.join(self.app, "inconnu.txt"), "inconnu\n")
        ecrire(os.path.join(self.app, "data", "inconnu2.txt"), "inconnu2\n")
        ecrire(os.path.join(self.app, "backups", "monprojet_rev-0039_20261001-010101.dump"), "x")
        ecrire(os.path.join(self.app, "backups", "monprojet_auto-20261002-010101.dump"), "x")

    # -- configuration ---------------------------------------------------------------------------
    def _config(self):
        return {
            "repertoire_etat": self.etat_dir,
            "git": {"cle_ordres": self.racine + "/cle_ordres", "cle_application": self.racine + "/cle_app",
                    "known_hosts": self.racine + "/known_hosts", "identite_nom": "Deployeur",
                    "identite_courriel": "deployeur@localhost"},
            "depot_ordres": {"url": "file://" + self.ordres_remote, "branche": "main"},
            "application": {
                "projet": "monprojet", "dossier": self.app, "fichier_compose": "docker-compose.yml",
                "service_app": "app", "service_db": "db", "conteneur_db": "monprojet-db-1",
                "volume_base": "monprojet_pgdata", "montage_base": "/var/lib/postgresql/data",
                "volume_ecussons": "monprojet_images", "volume_depots_bruts": "monprojet_bruts",
                "prefixe_sauvegarde": "monprojet", "url_sante": self.url_sante,
                "depot_url": "file://" + self.src, "tables_histoire": self.histoire,
                "place_min_deploiement_go": 0, "sauvegardes_garder": 10, "delai_sante_s": 1.5,
                "intervalle_sante_s": 0.02,
            },
            "suites": {"suite-a": {"depot": "exemple/suites", "chemin": "dist/suite_a.html",
                                   "dossier": self.suites_dir, "fichier": "suite_a.html"}},
            "hote_fichiers_bruts": "raw.exemple.test",
            "zones": {"donnees": {"chemin": self.zone_donnees, "place_min_go": 0},
                      "fichiers": {"chemin": self.zone_fichiers, "place_min_go": 0}},
            "zone_transfert": "fichiers",
            "depots_publics": ["exemple/suites", "exemple/outils"],
            "hotes_autorises": ["cdn.exemple.test"],
            "intervalle_en_cours_s": 300,
        }

    def cfg(self):
        return config.valider(json.loads(json.dumps(self.dict_config)))

    def ecrire_config(self):
        chemin = os.path.join(self.racine, "config.json")
        ecrire(chemin, json.dumps(self.dict_config))
        return chemin

    # -- faux docker -----------------------------------------------------------------------------
    def docker_etat(self):
        with open(self.etat_docker, "r", encoding="utf-8") as f:
            return json.load(f)

    def docker_ecrire(self, e):
        tmp = self.etat_docker + ".t"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(e, f)
        os.replace(tmp, self.etat_docker)

    def docker(self, **kw):
        e = self.docker_etat()
        e.update(kw)
        self.docker_ecrire(e)

    def appels(self):
        return [l["argv"] for l in self._journal() if not l["interdit"]]

    def interdits(self):
        return [l for l in self._journal() if l["interdit"]]

    def _journal(self):
        try:
            with open(self.journal_docker, "r", encoding="utf-8") as f:
                return [json.loads(l) for l in f if l.strip()]
        except FileNotFoundError:
            return []

    def vider_appels(self):
        try:
            os.remove(self.journal_docker)
        except FileNotFoundError:
            pass

    # -- ordres et passages ----------------------------------------------------------------------
    def ordre(self, ident, **champs):
        obj = {"id": ident, "demande_par": "test"}
        obj.update(champs)
        self.ordre_brut(ident, json.dumps(obj))

    def ordre_brut(self, stem, texte):
        ecrire(os.path.join(self.ordres_w, "ordres", stem + ".json"), texte)
        git("add", "-A", cwd=self.ordres_w)
        git("commit", "-q", "-m", "ordre " + stem, cwd=self.ordres_w)
        git("pull", "-q", "--rebase", "origin", "main", cwd=self.ordres_w)
        git("push", "-q", "origin", "HEAD:refs/heads/main", cwd=self.ordres_w)

    def lancer(self, file="deploiement", cfg=None):
        self.sortie = []
        return passage.executer(cfg or self.cfg(), file, sortie=self.sortie.append,
                                dormir=lambda s: time.sleep(min(s, 0.02)))

    def resultat(self, ident):
        git("pull", "-q", "--rebase", "origin", "main", cwd=self.ordres_w)
        chemin = os.path.join(self.ordres_w, "resultats", ident + ".md")
        return lire(chemin) if os.path.exists(chemin) else None

    def statut(self, ident):
        r = self.resultat(ident)
        assert r is not None, "pas de compte rendu pour %s ; sortie : %s" % (ident, "\n".join(self.sortie))
        return r.splitlines()[0].replace("Statut : ", "")

    def jouer(self, ident, **champs):
        """Écrit l'ordre, passe la file, retourne le statut."""
        self.ordre(ident, **champs)
        file = "fichiers" if champs.get("action") == "fichiers" else "deploiement"
        self.lancer(file)
        return self.statut(ident)

    def adopter(self, ident="2026-10-27-01"):
        return self.jouer(ident, action="adopter", commit=self.commit_a)

    def application(self):
        return json.loads(lire(os.path.join(self.etat_dir, "application.json")))

    def servi(self):
        return self.application()["servi"]

    def nouveau_commit_b(self, version="1.0056", **plus):
        fichiers = {"VERSION": version + "\n", "app/main.py": "print('b')\n", "app/nouveau.py": "nouveau\n"}
        fichiers.update(plus)
        return self.commit_app(fichiers, retirer=["app/ancien.py"])

    def sauvegardes(self):
        d = os.path.join(self.app, "backups")
        return sorted(os.listdir(d))
