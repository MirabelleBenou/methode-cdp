#!/usr/bin/env python3
"""Vérificateur des vivants partagés — contrôle en lecture seule.

Quand plusieurs chefs de projet écrivent en même temps dans un dépôt de
« vivants », ce script vérifie que les documents partagés restent cohérents :
le registre des arbitrages, la source des chantiers (chantiers.yaml), la page
qui s'en régénère (chantiers.html) et le journal des lots du plan.

    python3 -B verifier_vivants.py --chantiers <chantiers.yaml> --registre <registre.md> \\
        [--tableau <chantiers.html> --generateur <generer_tableau.py>] [--journal <plan.md>] \\
        [--archives <dossier>] [--domaines <fichier> [--racine <dossier>] [--plafond-checkpoint <octets>]]

« --tableau » et « --generateur » vont ensemble ; « --journal » est facultatif.
« --archives » donne le dossier des archives de chantiers (les fichiers CHANTIERS_*.yaml,
même forme que chantiers.yaml, que fait archiver_chantiers.py) ; il doit exister. Sans cette
option, rien ne change. Avec elle, deux contrôles s'étendent aux archives : le 3 et le 7.
« --domaines » donne la table des domaines (voir le contrôle 9) et déclenche ce contrôle ;
« --racine » est le dossier d'où se lisent les chemins de cette table (le dossier courant
par défaut) ; il ne s'emploie qu'avec « --domaines ». « --plafond-checkpoint » donne le
plafond de taille d'un checkpoint, en octets (un entier positif, 10240 par défaut) : un
checkpoint se relit en entier à chaque reprise, il doit rester court (voir le contrôle 10) ;
il ne s'emploie, lui aussi, qu'avec « --domaines ». Un contrôle dont les fichiers ne sont
pas donnés s'affiche « non demandé ».

Les dix contrôles, dans cet ordre :
  1. numéros du registre : les lignes « | **R<n>** | » n'ont aucun numéro en
     double et aucun trou entre le plus petit et le plus grand ;
  2. réservations : une ligne « | **R<n>** | *réservé … » encore présente est un
     avertissement, pas un écart (une réservation vit le temps d'écrire l'entrée) ;
  3. identifiants de chantier : aucune « id: » en double dans chantiers.yaml ; avec
     « --archives », aussi : aucun id de chantiers.yaml qui figure dans une archive, aucun id
     présent deux fois dans les archives, et le compte devient « <n> chantiers, <a> archivés » ;
  4. versions des lots : aucune valeur de « version: » portée par deux entrées ;
  5. chantiers en vol : chaque entrée « statut: en-vol » porte un « cdp: » non vide ;
  6. tableau : la régénération de chantiers.yaml par le générateur, dans un
     dossier temporaire, est égale à l'octet à chantiers.html, après avoir
     remplacé dans les deux textes chaque date « jj/mm/aaaa » par un même jeton
     (le générateur date la page du jour où il tourne) ;
  7. journal : la dernière version du journal (dernière ligne du plan qui
     commence par « | `v…` | ») a une entrée de chantiers.yaml en
     « statut: recette » dont l'id ou la version la contient ; avec « --archives », cette
     entrée se cherche aussi dans les archives (une entrée archivée était en recette) ;
  8. livrables et ressources : un livrable (« livrable: », le dépôt de code d'où
     sort la release) et une ressource partagée (« ressource: », une machine ou
     un logiciel que deux lots ne peuvent pas occuper en même temps) n'ont
     chacun qu'un seul lot en vol à la fois, et un lot qui attend
     (« attend: <id> ») est suspendu. Trois règles : (a) pour chaque valeur de
     « livrable: » et pour chaque valeur de « ressource: », au plus une entrée en
     « statut: en-vol » (les deux espaces de noms sont séparés : un livrable et
     une ressource de même nom ne se mélangent pas ; une entrée peut porter les
     deux et compte alors pour chacun) ; (b) chaque « attend: » désigne l'id
     d'une entrée qui existe ; (c) une entrée qui porte « attend: » n'est pas en
     « statut: en-vol ». Le compte est « <n> livrables, <r> ressources, <m> en
     vol, <k> en attente » : valeurs distinctes de chaque champ, entrées en vol
     qui portent un livrable ou une ressource (une entrée qui porte les deux
     compte une fois), entrées qui portent « attend: ». Ce contrôle ne dépend que
     de « --chantiers » : il tourne toujours ;
  9. checkpoints : chaque domaine (un chef de projet, un périmètre) a un checkpoint, un
     document libre dont une section porte sa file (ce qui vient ensuite). Le contrôle
     recoupe cette file et le document avec chantiers.yaml. Il demande « --domaines » ; il
     lit la table des domaines dans la même forme pauvre que chantiers.yaml : une entrée
     commence par « - domaine: », une clé par ligne, les lignes vides et « # » ignorées.
     Les clés : « domaine » (nom court), « cdp » (le chef de projet du domaine),
     « checkpoint » (chemin du checkpoint, relatif à « --racine »), « file » (le début exact
     du titre de la section de file, une ligne qui commence par cette valeur ; vide : aucune
     section de file déclarée, ce qui est un écart du domaine), « modules » (les modules de
     chantiers.yaml du domaine, séparés par des espaces, peut être vide) et « prefixes »
     (facultatif : des débuts d'id du domaine).
     Une entrée de chantiers.yaml est au premier domaine qui convient, selon cet ordre de
     règles : son « cdp: » égale celui du domaine, sinon son id commence par l'un des
     préfixes, sinon son « module: » est l'un des modules ; sinon elle n'est à aucun
     domaine. Un id est cité par un checkpoint s'il y apparaît entre accents graves
     (`id`). La section de file va de sa ligne de titre à la ligne suivante qui commence
     par « ## », ou à la fin du fichier. Deux règles : (b) la file ne cite aucun chantier
     clos, c'est-à-dire en « statut: recette » ou seulement archivé (les archives viennent
     de « --archives ») ; (c) chaque entrée du domaine en « statut » a-venir, a-cadrer,
     dette ou en-vol, sans clé « pour: » (un message, pas un sujet), est citée par le
     checkpoint. Un « file: » vide fait une ligne d'écart du domaine (« aucune section de file
     déclarée »), placée avant ses lignes (c) ; (b) ne s'y applique pas, (c) oui. Une table en
     défaut (checkpoint introuvable, section de file introuvable, entrée sans « domaine » ou
     sans « checkpoint ») est un écart, et le domaine n'est pas contrôlé plus avant. Le compte
     est « <n> domaines, <b> cités clos, <c> non cités, <v> sans section de file » ;
 10. taille des checkpoints : un checkpoint se relit en entier à chaque reprise de session ;
     au-delà du plafond, il coûte à chaque reprise et son historique doit partir à une
     archive. Le contrôle demande « --domaines ». Pour chaque domaine (dans l'ordre de la
     table) qui a un « domaine » et un « checkpoint », il mesure la taille en octets du
     fichier du checkpoint sur le disque ; strictement au-dessus de « --plafond-checkpoint »
     (10240 par défaut), c'est une ligne d'écart « <domaine> : <chemin> pèse <n> octets,
     plafond <p> » (le chemin tel qu'écrit dans la table). Un checkpoint introuvable ou une
     entrée sans « domaine » ou sans « checkpoint » est ignoré ici : le contrôle 9 le
     signale déjà. Le compte est « <n> domaines, <k> au-delà de <p> octets », <n> étant les
     entrées qui ont un domaine et un checkpoint.

Sortie : une ligne par contrôle (OK, ÉCART ou avertissement, avec un compte),
le détail des écarts indenté dessous, puis une dernière ligne « VIVANTS · … ».
Code de retour : 0 sans écart, 1 avec au moins un écart, 2 pour un appel
invalide (argument manquant, fichier ou dossier introuvable, « --racine » ou
« --plafond-checkpoint » sans « --domaines », plafond qui n'est pas un entier positif).

Python 3, bibliothèque standard seulement. Le lecteur YAML est volontairement
pauvre, comme celui du générateur : « - id: » puis des « clé: valeur » sur une
seule ligne.
"""
import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

RE_NUMERO = re.compile(r"^\|\s*\*\*R(\d+)\*\*\s*\|")
RE_RESERVATION = re.compile(r"^\|\s*\*\*R(\d+)\*\*\s*\|\s*\*réservé")
RE_JOURNAL = re.compile(r"^\|\s*`(v[^`]*)`\s*\|")
RE_DATE = re.compile(rb"\d{2}/\d{2}/\d{4}")

NON_DEMANDE = "—  non demandé"
STATUTS_OUVERTS = ("a-venir", "a-cadrer", "dette", "en-vol")
PLAFOND_DEFAUT = 10240  # octets : un checkpoint se relit en entier à chaque reprise


def lire_texte(chemin: Path) -> str:
    return chemin.read_text(encoding="utf-8")


def lire_chantiers(chemin: Path) -> list[dict]:
    """Même lecteur que le générateur ; chaque entrée garde sa ligne source (et son fichier)."""
    chantiers: list[dict] = []
    for numero, ligne in enumerate(lire_texte(chemin).split("\n"), start=1):
        nue = ligne.strip()
        if not nue or nue.startswith("#"):
            continue
        if nue.startswith("- "):
            chantiers.append({"_ligne": numero, "_fichier": chemin.name})
            nue = nue[2:]
        if ":" not in nue or not chantiers:
            continue
        cle, _, valeur = nue.partition(":")
        chantiers[-1][cle.strip()] = valeur.strip()
    return chantiers


def nom(c: dict) -> str:
    return c.get("id") or f"(sans id, ligne {c['_ligne']})"


def plages(numeros: list[int]) -> list[str]:
    """['R20', 'R25 à R27 (3 numéros)'] à partir d'une liste triée."""
    sortie, i = [], 0
    while i < len(numeros):
        j = i
        while j + 1 < len(numeros) and numeros[j + 1] == numeros[j] + 1:
            j += 1
        if i == j:
            sortie.append(f"R{numeros[i]}")
        else:
            sortie.append(f"R{numeros[i]} à R{numeros[j]} ({j - i + 1} numéros)")
        i = j + 1
    return sortie


# Chaque contrôle rend (verdict, compte, détails) ; verdict : OK, ÉCART ou avertissement.

def controle_numeros(registre: Path):
    lignes: dict[int, list[int]] = {}
    for position, ligne in enumerate(lire_texte(registre).split("\n"), start=1):
        m = RE_NUMERO.match(ligne)
        if m:
            lignes.setdefault(int(m.group(1)), []).append(position)
    total = sum(len(v) for v in lignes.values())
    if not lignes:
        return "ÉCART", "aucun numéro trouvé", ["aucune ligne « | **R<n>** | » dans le registre"]
    details = [f"R{n} en double (lignes {', '.join(map(str, v))})"
               for n, v in sorted(lignes.items()) if len(v) > 1]
    manquants = [n for n in range(min(lignes), max(lignes) + 1) if n not in lignes]
    details += [f"{p} manquant" if " " not in p else f"{p} manquants" for p in plages(manquants)]
    compte = f"{total} numéros, R{min(lignes)} à R{max(lignes)}"
    return ("ÉCART" if details else "OK"), compte, details


def controle_reservations(registre: Path):
    trouvees = []
    for position, ligne in enumerate(lire_texte(registre).split("\n"), start=1):
        m = RE_RESERVATION.match(ligne)
        if m:
            trouvees.append(f"R{m.group(1)} réservé (ligne {position})")
    if trouvees:
        return "avertissement", f"{len(trouvees)} réservation(s) en cours", trouvees
    return "OK", "aucune réservation en cours", []


def controle_identifiants(chantiers: list[dict], archives: list[dict] | None = None):
    vus: dict[str, list[int]] = {}
    for c in chantiers:
        if c.get("id"):
            vus.setdefault(c["id"], []).append(c["_ligne"])
    details = [f"id {i} en double (lignes {', '.join(map(str, v))})"
               for i, v in vus.items() if len(v) > 1]
    compte = f"{len(chantiers)} chantiers"
    if archives is not None:
        details += ecarts_archives(vus, archives)
        compte += f", {len(archives)} archivés"
    return ("ÉCART" if details else "OK"), compte, details


def ecarts_archives(vivants: dict[str, list[int]], archives: list[dict]) -> list[str]:
    """Les id de chantiers.yaml aussi archivés, puis les id présents deux fois dans les archives."""
    archives_par_id: dict[str, list[str]] = {}
    for c in archives:
        if c.get("id"):
            archives_par_id.setdefault(c["id"], []).append(f"{c['_fichier']}:{c['_ligne']}")
    details = [f"id {i} aussi archivé ({emplacements[0]})"
               for i, emplacements in archives_par_id.items() if i in vivants]
    details += [f"id {i} en double dans les archives ({', '.join(emplacements)})"
                for i, emplacements in archives_par_id.items() if len(emplacements) > 1]
    return details


def controle_versions(chantiers: list[dict]):
    portees: dict[str, list[str]] = {}
    for c in chantiers:
        if c.get("version"):
            portees.setdefault(c["version"], []).append(nom(c))
    details = [f"version {v} portée par {' et '.join(ids)}"
               for v, ids in portees.items() if len(ids) > 1]
    return ("ÉCART" if details else "OK"), f"{len(portees)} versions", details


def controle_en_vol(chantiers: list[dict]):
    en_vol = [c for c in chantiers if c.get("statut") == "en-vol"]
    details = [f"{nom(c)} (ligne {c['_ligne']}) : cdp absent ou vide"
               for c in en_vol if not c.get("cdp")]
    return ("ÉCART" if details else "OK"), f"{len(en_vol)} en vol", details


def controle_tableau(chantiers: list[dict], chantiers_yaml: Path, tableau: Path, generateur: Path):
    compte = f"{len(chantiers)} chantiers"
    with tempfile.TemporaryDirectory(prefix="vivants-") as dossier:
        sortie = Path(dossier) / "regeneration.html"
        essai = subprocess.run([sys.executable, "-B", str(generateur.resolve()), str(chantiers_yaml.resolve()), str(sortie)],
                               capture_output=True, text=True, cwd=dossier)
        if essai.returncode != 0 or not sortie.is_file():
            message = (essai.stderr.strip() or essai.stdout.strip() or "sans message").splitlines()[-1]
            return "ÉCART", compte, [f"le générateur a échoué (code {essai.returncode}) : {message}"]
        brut, regenere = tableau.read_bytes(), sortie.read_bytes()
    voulu, obtenu = RE_DATE.sub(b"<date>", brut), RE_DATE.sub(b"<date>", regenere)
    if voulu == obtenu:
        return "OK", f"{compte}, {len(brut)} octets identiques hors date", []
    rang = next((i for i, (a, b) in enumerate(zip(voulu, obtenu)) if a != b), min(len(voulu), len(obtenu)))
    ligne = voulu.count(b"\n", 0, rang) + 1
    return "ÉCART", compte, [f"le tableau diffère de sa régénération (dates masquées) : premier écart à l'octet "
                             f"{rang} (ligne {ligne}) ; {len(voulu)} octets contre {len(obtenu)} régénérés"]


def controle_journal(chantiers: list[dict], journal: Path):
    derniere = None
    for ligne in lire_texte(journal).split("\n"):
        m = RE_JOURNAL.match(ligne)
        if m:
            derniere = m.group(1)
    if derniere is None:
        return "ÉCART", "aucune version", ["aucune ligne « | `v…` | » dans le journal"]
    portent = [c for c in chantiers if derniere in c.get("id", "") or derniere in c.get("version", "")]
    recettes = [c for c in portent if c.get("statut") == "recette"]
    if recettes:
        return "OK", f"dernière version {derniere}", []
    details = [f"{derniere} : aucune entrée en statut recette ne porte cette version"]
    details += [f"{nom(c)} la porte mais est en statut {c.get('statut') or 'vide'}" for c in portent]
    return "ÉCART", f"dernière version {derniere}", details


def controle_livrables(chantiers: list[dict]):
    # champ -> valeur -> ids des entrées en vol ; un espace de noms par champ
    espaces: dict[str, dict[str, list[str]]] = {"livrable": {}, "ressource": {}}
    for c in chantiers:
        for champ, valeurs in espaces.items():
            if c.get(champ):
                valeurs.setdefault(c[champ], [])
                if c.get("statut") == "en-vol":
                    valeurs[c[champ]].append(nom(c))
    ids = {c["id"] for c in chantiers if c.get("id")}
    details = [f"{champ} {valeur} : {len(en_vol)} lots en vol ({', '.join(en_vol)})"
               for champ, valeurs in espaces.items()
               for valeur, en_vol in valeurs.items() if len(en_vol) > 1]
    attendent = [c for c in chantiers if c.get("attend")]
    details += [f"{nom(c)} attend {c['attend']}, qui n'existe pas"
                for c in attendent if c["attend"] not in ids]
    details += [f"{nom(c)} est en vol mais attend {c['attend']}"
                for c in attendent if c.get("statut") == "en-vol"]
    en_vol = sum(1 for c in chantiers
                 if c.get("statut") == "en-vol" and (c.get("livrable") or c.get("ressource")))
    compte = (f"{len(espaces['livrable'])} livrables, {len(espaces['ressource'])} ressources, "
              f"{en_vol} en vol, {len(attendent)} en attente")
    return ("ÉCART" if details else "OK"), compte, details


def valeurs(entree: dict, cle: str) -> list[str]:
    return entree.get(cle, "").split()


def domaine_de(c: dict, domaines: list[dict]) -> str | None:
    """Le premier domaine qui convient, règle après règle : cdp, puis préfixe, puis module."""
    regles = (
        lambda d: bool(c.get("cdp")) and c["cdp"] == d.get("cdp"),
        lambda d: any(c["id"].startswith(p) for p in valeurs(d, "prefixes")),
        lambda d: bool(c.get("module")) and c["module"] in valeurs(d, "modules"),
    )
    for regle in regles:
        for d in domaines:
            if regle(d):
                return d["domaine"]
    return None


def section_de_file(texte: str, titre: str) -> str | None:
    """De la ligne qui commence par le titre à la ligne « ## » suivante (exclue) ; None sans titre."""
    lignes = texte.split("\n")
    debut = next((i for i, ligne in enumerate(lignes) if ligne.startswith(titre)), None)
    if debut is None:
        return None
    fin = next((i for i in range(debut + 1, len(lignes)) if lignes[i].startswith("## ")), len(lignes))
    return "\n".join(lignes[debut:fin])


def ids_clos(chantiers: list[dict], archives: list[dict] | None) -> dict[str, str]:
    """Les id clos : en recette dans chantiers.yaml, ou seulement archivés."""
    vivants = {c["id"] for c in chantiers if c.get("id")}
    clos = {c["id"]: "recette" for c in chantiers if c.get("id") and c.get("statut") == "recette"}
    for c in archives or []:
        if c.get("id") and c["id"] not in vivants:
            clos.setdefault(c["id"], "archivé")
    return clos


def citation(i: str) -> str:
    return f"`{i}`"


def controle_domaine(d: dict, chantiers: list[dict], clos: dict[str, str],
                     domaines: list[dict], racine: Path):
    """Les défauts de la table, ou : file non déclarée, file qui cite du clos (9b), ouverts non cités (9c)."""
    nom_d, chemin = d["domaine"], racine / d["checkpoint"]
    if not chemin.is_file():
        return [f"{nom_d} : checkpoint introuvable {d['checkpoint']}"], [], [], []
    try:
        texte = lire_texte(chemin)
    except (OSError, UnicodeDecodeError):
        return [f"{nom_d} : checkpoint illisible {d['checkpoint']}"], [], [], []
    titre = d.get("file", "")
    section = section_de_file(texte, titre) if titre else None
    if titre and section is None:
        return [f"{nom_d} : section de file introuvable « {titre} »"], [], [], []
    sans_file = [] if titre else [f"{nom_d} : aucune section de file déclarée (file: vide)"]
    positions = sorted((section.find(citation(i)), i) for i in clos if citation(i) in section) if section else []
    cites = [f"{nom_d} : la file cite {i}, clos ({clos[i]})" for _, i in positions]
    non_cites = [f"{nom_d} : {c['id']} ({c['statut']}) n'est pas cité au checkpoint"
                 for c in chantiers
                 if c.get("id") and c.get("statut") in STATUTS_OUVERTS and "pour" not in c
                 and domaine_de(c, domaines) == nom_d and citation(c["id"]) not in texte]
    return [], sans_file, cites, non_cites


def controle_checkpoints(chantiers: list[dict], archives: list[dict] | None, table: list[dict], racine: Path):
    clos = ids_clos(chantiers, archives)
    valides = [d for d in table if d.get("domaine") and d.get("checkpoint")]
    details, total_cites, total_non_cites, total_sans_file = [], 0, 0, 0
    for d in table:
        if d not in valides:
            details.append(f"entrée de la ligne {d['_ligne']} : domaine ou checkpoint manquant")
            continue
        defauts, sans_file, cites, non_cites = controle_domaine(d, chantiers, clos, valides, racine)
        details += defauts + sans_file + cites + non_cites
        total_cites += len(cites)
        total_non_cites += len(non_cites)
        total_sans_file += len(sans_file)
    compte = (f"{len(table)} domaines, {total_cites} cités clos, {total_non_cites} non cités, "
              f"{total_sans_file} sans section de file")
    return ("ÉCART" if details else "OK"), compte, details


def taille_checkpoint(chemin: Path) -> int | None:
    """La taille en octets du fichier sur le disque ; None s'il est introuvable."""
    try:
        return chemin.stat().st_size if chemin.is_file() else None
    except OSError:
        return None


def controle_taille(table: list[dict], racine: Path, plafond: int):
    """Un checkpoint strictement plus lourd que le plafond est un écart ; les introuvables sont ignorés."""
    valides = [d for d in table if d.get("domaine") and d.get("checkpoint")]
    details = []
    for d in valides:
        taille = taille_checkpoint(racine / d["checkpoint"])
        if taille is not None and taille > plafond:
            details.append(f"{d['domaine']} : {d['checkpoint']} pèse {taille} octets, plafond {plafond}")
    compte = f"{len(valides)} domaines, {len(details)} au-delà de {plafond} octets"
    return ("ÉCART" if details else "OK"), compte, details


class Analyseur(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError(message.replace("expected one argument", "valeur manquante"))


def lire_archives(dossier: Path) -> list[dict]:
    """Les entrées de toutes les archives du dossier, par ordre de nom de fichier."""
    archives: list[dict] = []
    for fichier in sorted(p for p in dossier.glob("CHANTIERS_*.yaml") if p.is_file()):
        archives += lire_chantiers(fichier)
    return archives


def lire_arguments(argv: list[str]):
    p = Analyseur(prog="verifier_vivants.py", allow_abbrev=False, add_help=False)
    for option in ("chantiers", "registre", "tableau", "generateur", "journal", "archives", "domaines", "racine"):
        p.add_argument(f"--{option}")
    p.add_argument("--plafond-checkpoint")
    a, inconnus = p.parse_known_args(argv)
    if inconnus:
        raise ValueError(f"argument inconnu : {inconnus[0]}")
    for option in ("chantiers", "registre"):
        if not getattr(a, option):
            raise ValueError(f"argument manquant : --{option}")
    if bool(a.tableau) != bool(a.generateur):
        raise ValueError("--tableau et --generateur vont ensemble")
    if a.racine and not a.domaines:
        raise ValueError("--racine ne va qu'avec --domaines")
    if a.plafond_checkpoint is not None and not a.domaines:
        raise ValueError("--plafond-checkpoint ne va qu'avec --domaines")
    plafond = PLAFOND_DEFAUT
    if a.plafond_checkpoint is not None:
        if not re.fullmatch(r"[0-9]+", a.plafond_checkpoint) or int(a.plafond_checkpoint) < 1:
            raise ValueError(f"--plafond-checkpoint : un entier positif est attendu ({a.plafond_checkpoint})")
        plafond = int(a.plafond_checkpoint)
    chemins = {option: Path(getattr(a, option)) for option in
               ("chantiers", "registre", "tableau", "generateur", "journal", "archives", "domaines", "racine")
               if getattr(a, option)}
    for option, chemin in chemins.items():
        if not (chemin.is_dir() if option in ("archives", "racine") else chemin.is_file()):
            raise ValueError(f"fichier introuvable : --{option} {chemin}")
    return chemins, plafond


def main(argv: list[str]) -> int:
    try:
        f, plafond = lire_arguments(argv)
        chantiers = lire_chantiers(f["chantiers"])
        archives = lire_archives(f["archives"]) if "archives" in f else None
        table = lire_chantiers(f["domaines"]) if "domaines" in f else None
        for option in ("registre", "journal"):  # lecture d'essai : un fichier illisible est un appel invalide
            if option in f:
                lire_texte(f[option])
    except (ValueError, OSError, UnicodeDecodeError) as erreur:
        print(f"verifier_vivants : {' '.join(str(erreur).split())}", file=sys.stderr)
        return 2

    controles = [
        ("numéros du registre", lambda: controle_numeros(f["registre"])),
        ("réservations", lambda: controle_reservations(f["registre"])),
        ("identifiants de chantier", lambda: controle_identifiants(chantiers, archives)),
        ("versions des lots", lambda: controle_versions(chantiers)),
        ("chantiers en vol", lambda: controle_en_vol(chantiers)),
        ("tableau", (lambda: controle_tableau(chantiers, f["chantiers"], f["tableau"], f["generateur"]))
         if "tableau" in f else None),
        ("journal", (lambda: controle_journal(chantiers + (archives or []), f["journal"])) if "journal" in f else None),
        ("livrables et ressources", lambda: controle_livrables(chantiers)),
        ("checkpoints", (lambda: controle_checkpoints(chantiers, archives, table, f.get("racine", Path("."))))
         if table is not None else None),
        ("taille des checkpoints", (lambda: controle_taille(table, f.get("racine", Path(".")), plafond))
         if table is not None else None),
    ]
    ecarts = 0
    for rang, (libelle, controle) in enumerate(controles, start=1):
        if controle is None:
            print(f"{rang:<2} {libelle:<26} {NON_DEMANDE}")
            continue
        verdict, compte, details = controle()
        ecarts += verdict == "ÉCART"
        print(f"{rang:<2} {libelle:<26} {verdict:<13}  {compte}")
        for detail in details:
            print(f"      {detail}")
    print("VIVANTS · aucun écart" if not ecarts else f"VIVANTS · {ecarts} écart(s)")
    return 1 if ecarts else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
