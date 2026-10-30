"""Une doublure de ``docker`` pour les tests : joue des scénarios et REFUSE (en le signalant) tout appel hors de la
liste blanche du cadrage. Placée en tête du PATH sous le nom ``docker``.

Environnement : FAUX_DOCKER_ETAT (JSON : le scénario et l'état), FAUX_DOCKER_JOURNAL (une ligne JSON par appel).
Un appel interdit est journalisé avec la clé ``interdit`` et sort avec le code 97.
"""

import io
import json
import os
import sys
import tarfile

ETAT = os.environ["FAUX_DOCKER_ETAT"]
JOURNAL = os.environ["FAUX_DOCKER_JOURNAL"]

SH_DUMP = 'pg_dump -Fc -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
SH_LIRE = 'psql -X -q -A -t -F "|" --set=ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
MOTS_ECRITURE = ("INSERT", "UPDATE", "DELETE", "DROP", "TRUNCATE", "ALTER", "CREATE", "GRANT", "COPY")


def charger():
    with open(ETAT, "r", encoding="utf-8") as f:
        return json.load(f)


def sauver(e):
    tmp = ETAT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(e, f)
    os.replace(tmp, ETAT)


def journaliser(argv, interdit=None):
    with open(JOURNAL, "a", encoding="utf-8") as f:
        f.write(json.dumps({"argv": argv, "interdit": interdit}) + "\n")


def interdit(argv, raison):
    journaliser(argv, raison)
    sys.stderr.write("faux docker : appel interdit : %s\n" % raison)
    sys.exit(97)


def sortie(octets):
    if isinstance(octets, str):
        octets = octets.encode("utf-8")
    sys.stdout.buffer.write(octets)
    sys.stdout.buffer.flush()


def echec(message, code=1):
    sys.stderr.write(message + "\n")
    sys.exit(code)


def compose(argv, e):
    if len(argv) < 8 or argv[1:2] != ["-p"] or argv[3] != "--project-directory" or argv[5] != "-f":
        interdit(argv, "forme de compose inattendue")
    projet, dossier, fichier = argv[2], argv[4], argv[6]
    sub = argv[7:]
    if fichier != os.path.join(dossier, e.get("fichier", "docker-compose.yml")):
        interdit(argv, "fichier compose inattendu")
    ici = projet == e["projet"] and dossier == e["dossier"]
    if sub == ["ps", "--format", "json"]:
        journaliser(argv)
        if ici:
            for svc, etat in e["services"].items():
                nom = "%s-%s-1" % (e["projet"], svc)
                sortie(json.dumps({"Service": svc, "Name": nom, "State": etat, "Health": "", "Status": "Up"}) + "\n")
        return
    if len(sub) == 2 and sub[0] == "build" and sub[1] == "app":
        journaliser(argv)
        if e.get("build_echec"):
            echec("build en échec : erreur de compilation simulée")
        sortie("build ok\n")
        return
    if sub == ["up", "-d", "--no-deps", "app"]:
        journaliser(argv)
        if e.get("up_echec"):
            echec("up en échec simulé")
        if e.pop("up_echec_une_fois", False):
            sauver(e)
            echec("up en échec simulé (une seule fois)")
        version = e.pop("up_version", None)
        if version is None:
            with open(os.path.join(dossier, "VERSION"), "r", encoding="utf-8") as f:
                version = f.read().strip()
        e["version"] = version
        e["up_fait"] = True
        apres = e.pop("apres", None)
        if apres:
            if "tables" in apres:
                e["tables"] = apres["tables"]
            if "revision" in apres:
                e["revision"] = apres["revision"]
        sauver(e)
        sortie("recreated\n")
        return
    if len(sub) == 5 and sub[:3] == ["logs", "--no-color", "--since"] and sub[4] == "app":
        journaliser(argv)
        lignes = list(e.get("logs", []))
        lignes += e.pop("logs_apres_up", [])
        sauver(e)
        sortie("\n".join(lignes) + "\n")
        return
    interdit(argv, "sous-commande compose hors liste blanche : %s" % " ".join(sub))


def inspect(argv, e):
    if len(argv) != 2:
        interdit(argv, "inspect : forme inattendue")
    journaliser(argv)
    if argv[1] != e["conteneur_db"]:
        echec("Error: No such object: %s" % argv[1])
    sortie(json.dumps([{"Name": "/" + argv[1], "Config": {"Image": e["image"], "Labels": e["etiquettes_db"]},
                        "Mounts": e["montages"], "State": {"Running": True}}]))


def volume(argv, e):
    if len(argv) != 3 or argv[1] != "inspect":
        interdit(argv, "volume : sous-commande hors liste blanche : %s" % " ".join(argv[1:]))
    journaliser(argv)
    if argv[2] not in e["volumes"]:
        echec("Error: No such volume: %s" % argv[2])
    sortie(json.dumps([{"Name": argv[2], "Labels": e["volumes"][argv[2]]}]))


def execute(argv, e):
    reste = argv[1:]
    avec_entree = False
    if reste and reste[0] == "-i":
        avec_entree = True
        reste = reste[1:]
    if not reste or reste[0] != e["conteneur_db"]:
        interdit(argv, "exec : conteneur inattendu")
    cmd = reste[1:]
    if cmd == ["sh", "-c", SH_DUMP] and not avec_entree:
        journaliser(argv)
        if e.get("dump") == "vide":
            return
        sortie(b"PGDMP-FAUX" + b"x" * 4096)
        return
    if cmd == ["pg_restore", "--list"] and avec_entree:
        journaliser(argv)
        sys.stdin.buffer.read()
        if e.get("restore_list") == "echec":
            echec("pg_restore: erreur : fichier d'entrée illisible")
        n = len(e["tables"])
        if e.get("restore_list") == "peu":
            n = max(0, n - 3)
        lignes = ["; Archive created at 2026-10-27", ";     dbname: faux"]
        lignes += ["%d; 0 %d TABLE DATA public t%d postgres" % (i, i, i) for i in range(n)]
        lignes += ["999; 1259 1 TABLE public autre postgres"]
        sortie("\n".join(lignes) + "\n")
        return
    if cmd == ["sh", "-c", SH_LIRE] and avec_entree:
        sql = sys.stdin.read()
        if "BEGIN READ ONLY" not in sql or "ROLLBACK" not in sql:
            interdit(argv, "lecture de la base hors transaction en lecture seule")
        haut = sql.upper()
        for mot in MOTS_ECRITURE:
            if mot in haut.replace("QUERY_TO_XML", ""):
                interdit(argv, "SQL d'écriture : %s" % mot)
        journaliser(argv)
        if e.get("lecture_echec") or (e.get("lecture_echec_apres_up") and e.get("up_fait")):
            echec("psql: erreur de connexion simulée")
        sortie("R|%s\n" % e["revision"])
        for nom, n in sorted(e["tables"].items()):
            sortie("T|%s|%d\n" % (nom, n))
        return
    interdit(argv, "exec : commande hors liste blanche : %s" % " ".join(cmd))


def run(argv, e):
    attendu_debut = ["run", "--rm", "--network", "none", "--mount"]
    if argv[:5] != attendu_debut or len(argv) != 13:
        interdit(argv, "run : forme hors liste blanche")
    mount, image, suite = argv[5], argv[6], argv[7:]
    if suite != ["tar", "-czf", "-", "-C", "/source", "."]:
        interdit(argv, "run : commande hors liste blanche")
    if image != e["image"]:
        interdit(argv, "run : image inattendue")
    morceaux = dict(p.split("=", 1) if "=" in p else (p, True) for p in mount.split(","))
    if morceaux.get("type") != "volume" or morceaux.get("dst") != "/source" or not morceaux.get("readonly") \
            or morceaux.get("src") not in e["volumes"]:
        interdit(argv, "run : montage hors liste blanche")
    journaliser(argv)
    mode = e.get("tar", "ok")
    if mode == "vide":
        return
    if mode == "illisible":
        sortie(b"\x1f\x8b" + b"pas une archive" * 10)
        return
    tampon = io.BytesIO()
    with tarfile.open(fileobj=tampon, mode="w:gz") as tf:
        data = b"ecusson"
        info = tarfile.TarInfo("a.png")
        info.size = len(data)
        tf.addfile(info, io.BytesIO(data))
    sortie(tampon.getvalue())


def main():
    argv = sys.argv[1:]
    e = charger()
    if not argv:
        interdit(argv, "aucun argument")
    if argv[0] == "compose":
        compose(argv, e)
    elif argv[0] == "inspect":
        inspect(argv, e)
    elif argv[0] == "volume":
        volume(argv, e)
    elif argv[0] == "exec":
        execute(argv, e)
    elif argv[0] == "run":
        run(argv, e)
    else:
        interdit(argv, "sous-commande docker hors liste blanche : %s" % argv[0])


main()
