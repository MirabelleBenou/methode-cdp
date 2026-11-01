#!/usr/bin/env python3
"""Vérificateur des vivants partagés — contrôle en lecture seule.

Quand plusieurs chefs de projet écrivent en même temps dans un dépôt de
« vivants », ce script vérifie que les documents partagés restent cohérents :
le registre des arbitrages, la source des chantiers (chantiers.yaml), la page
fixe et le fichier de données qui s'en régénèrent (chantiers.html et chantiers.json, à côté)
et le journal des lots du plan.

    python3 -B verifier_vivants.py --chantiers <chantiers.yaml> --registre <registre.md> \\
        [--tableau <chantiers.html> --generateur <generer_tableau.py>] [--journal <plan.md>] \\
        [--archives <dossier>] [--domaines <fichier> [--racine <dossier>] [--plafond-checkpoint <octets>]
                                 [--plafond-chantier <octets>] [--plafond-registre <caractères>] [--registre-depuis <n>]]

« --tableau » et « --generateur » vont ensemble ; « --tableau » désigne la page, son fichier
de données est celui qui est à côté, même nom en « .json » ; « --journal » est facultatif.
« --archives » donne le dossier des archives de chantiers (les fichiers CHANTIERS_*.yaml,
même forme que chantiers.yaml, que fait archiver_chantiers.py) ; il doit exister. Sans cette
option, rien ne change. Avec elle, quatre contrôles s'étendent aux archives : le 3, le 4 (sa
règle des lots en vol), le 7 et le 11.
« --domaines » donne la table des domaines (voir le contrôle 9) et déclenche ce contrôle, puis
étend le 11 à la table ;
« --racine » est le dossier d'où se lisent les chemins de cette table (le dossier courant
par défaut) ; il ne s'emploie qu'avec « --domaines ». « --plafond-checkpoint » donne le
plafond de taille d'un checkpoint, en octets (un entier positif, 10240 par défaut) : un
checkpoint se relit en entier à chaque reprise, il doit rester court (voir le contrôle 10) ;
il ne s'emploie, lui aussi, qu'avec « --domaines ». De même, « --plafond-chantier » (octets,
1536 par défaut), « --plafond-registre » (caractères, 800 par défaut) et « --registre-depuis »
(le numéro de la première entrée du registre mesurée ; sans elle, le registre n'est pas mesuré) :
des entiers positifs, qui ne s'emploient qu'avec « --domaines » (voir le contrôle 12). Un contrôle
dont les fichiers ne sont pas donnés s'affiche « non demandé ».

Les douze contrôles, dans cet ordre :
  1. numéros du registre : les lignes « | **R<n>** | » n'ont aucun numéro en
     double et aucun trou entre le plus petit et le plus grand ;
  2. réservations : une ligne « | **R<n>** | *réservé … » encore présente est un
     avertissement, pas un écart (une réservation vit le temps d'écrire l'entrée) ;
  3. identifiants de chantier : aucune « id: » en double dans chantiers.yaml ; avec
     « --archives », aussi : aucun id de chantiers.yaml qui figure dans une archive, aucun id
     présent deux fois dans les archives, et le compte devient « <n> chantiers, <a> archivés » ;
  4. versions des lots : (a) aucune valeur de « version: » portée par deux entrées de
     chantiers.yaml ; (b) une entrée « statut: en-vol » qui porte « version: » et « livrable: »
     porte une version strictement plus haute que toute autre « version: » du même
     « livrable: », dans chantiers.yaml et, avec « --archives », dans les archives : c'est la
     règle du numéro d'un lot (méthode §2, étape 6). Une version se compare par la suite des
     nombres de son jeton de version : la première occurrence, bornée par un caractère non
     alphanumérique ou le bord, de « [vV]?<n>.<n>[.<n>…] » ou de « [vV]<n> » (« v1.0065 » →
     (1, 65) ; « agent-v0.1.1 » → (0, 1, 1) ; « AC-V1.5.1 » → (1, 5, 1) ; « v1.10 (R205) » →
     (1, 10) ; « v19 » → (19,)) ; une valeur sans jeton ne se compare pas (« 18a2957, sans
     release (R188) » : ni le hash ni le numéro de décision ne sont des versions). Une ligne d'écart par entrée en
     vol en défaut, qui nomme la plus haute des autres versions : « <id> : <version> n'est pas
     au-dessus de <autre version> (<autre id>) ». Le compte reste « <n> versions » (valeurs
     distinctes de chantiers.yaml) ;
  5. chantiers en vol : chaque entrée « statut: en-vol » porte un « cdp: » non vide ;
  6. tableau : la page fixe et son fichier de données (celui qui est à côté de
     « --tableau », même nom en « .json ») sont égaux à la régénération de
     chantiers.yaml par le générateur, faite dans un dossier temporaire sous le
     même nom de page, à l'octet, après avoir remplacé dans les textes de chaque
     paire chaque date « jj/mm/aaaa » par un même jeton (le générateur date le
     fichier de données du jour où il tourne). Un écart par fichier qui diffère
     (premier octet et ligne) ; un écart si le fichier de données publié manque
     (« fichier de données absent : <chemin> ») ; le compte donne les octets de la
     page et des données ;
  7. journal : la dernière version du journal (dernière ligne du plan qui
     commence par « | `v…` | ») a une entrée de chantiers.yaml en
     « statut: recette » dont l'id ou la version la contient ; avec « --archives », cette
     entrée se cherche aussi dans les archives (une entrée archivée était en recette). Il
     vérifie l'accord du journal et des chantiers, pas le numéro d'un correctif : c'est la
     règle (b) du contrôle 4 ;
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
     lit la table des domaines dans la même forme que chantiers.yaml : une entrée
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
     dette ou en-vol, sans clé « pour: » (un message, pas un sujet), est citée DANS LA
     SECTION DE LA FILE du checkpoint (la même que lit la règle (b)) : une entrée citée
     seulement ailleurs dans le checkpoint est un écart. Un « file: » vide fait une ligne
     d'écart du domaine (« aucune section de file déclarée ») ; sans section de file, la
     règle (c) cherche la citation dans tout le checkpoint. Cette ligne d'écart est placée
     avant les lignes (c) ; (b) ne s'y applique pas, (c) oui. Une table en
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
     entrées qui ont un domaine et un checkpoint ;
 11. format YAML : chaque valeur de chantiers.yaml (« --chantiers »), des archives (si
     « --archives » est donné) et de la table des domaines (si « --domaines » est donné) est
     un scalaire YAML sûr, de sorte qu'un parseur YAML standard lit les mêmes valeurs que ce
     script. Une valeur est conforme si elle est vide ; ou nue et sûre (sans « : » suivi d'une
     espace ou de la fin de ligne, sans « # » précédé d'une espace, sans tabulation ni caractère de
     contrôle, et ne commençant par aucun de - ? : , [ ] { } # & * ! | > ' " % @ ` ) ; ou entre
     guillemets doubles, où seuls \\" et \\\\ sont des échappements. Le contrôle tourne toujours.
     OK : « <n> fichiers, <m> lignes lues » ; ÉCART : « <k> valeur(s) non conforme(s), <n> fichiers,
     <m> lignes lues », les cinq premières valeurs non conformes (« fichier:ligne : clé <clé> »),
     puis la commande qui normalise (« archiver_chantiers.py normaliser », qui ne réécrit que
     ces valeurs) ;
 12. taille des entrées : une entrée de chantier ou du registre se relit à chaque reprise ; au-delà
     de son plafond, son détail part au dossier du lot ou à une note, l'entrée n'en garde que le
     résumé et le chemin. Le contrôle demande « --domaines ». Entrées de chantier mesurées : celles de
     chantiers.yaml (pas des archives) en « statut » a-venir, a-cadrer, dette ou en-vol, sauf celles
     dont l'id commence par « arbitre- » (les constats de l'arbitre se ferment en corrigeant leur
     cause) ; une entrée avec « pour: » se mesure. Sa taille est le nombre d'octets UTF-8 des lignes du
     fichier depuis sa ligne « - id: » jusqu'à la ligne qui précède la suivante, sans les lignes vides
     ni celles dont le premier caractère non blanc est « # » (les bandeaux de section), chacune
     suivie d'un saut de ligne ; écart si elle est strictement au-dessus de « --plafond-chantier »
     (1536 par défaut). Entrées du registre mesurées : les lignes « | **R<n>** | » dont le numéro est
     au moins « --registre-depuis », sauf les réservations ; leur taille est le nombre de caractères
     de la ligne, saut de ligne exclu ; écart au-dessus de « --plafond-registre » (800 par défaut).
     Sans « --registre-depuis », le registre n'est pas mesuré. Le domaine d'une entrée de chantier est
     celui du contrôle 9 (cdp, puis préfixe, puis module), sinon « hors domaine » ; une entrée du
     registre n'a pas de domaine. Une ligne d'écart par entrée, dans l'ordre des fichiers
     (chantiers.yaml, puis le registre) : « <domaine> : chantier <id> pèse <o> octets, plafond <p> »
     (« hors domaine : chantier … »), « registre : R<n> compte <c> caractères, plafond <p> ». Le compte
     est « <n> chantiers ouverts, <r> entrées du registre, <k> au-delà » (<n> les entrées mesurées,
     <r> celles du registre, <k> les lignes d'écart) ; sans « --registre-depuis » :
     « <n> chantiers ouverts, registre non mesuré, <k> au-delà ».

Sortie : une ligne par contrôle (OK, ÉCART ou avertissement, avec un compte),
le détail des écarts indenté dessous, puis une dernière ligne « VIVANTS · … ».
Code de retour : 0 sans écart, 1 avec au moins un écart, 2 pour un appel
invalide (argument manquant, fichier ou dossier introuvable, « --racine »,
« --plafond-checkpoint », « --plafond-chantier », « --plafond-registre » ou « --registre-depuis »
sans « --domaines », plafond ou numéro qui n'est pas un entier positif).

Python 3.11 et plus, bibliothèque standard seulement. Le lecteur YAML est volontairement
pauvre, comme celui du générateur : « - id: » puis des « clé: valeur » sur une seule ligne ;
une valeur entre guillemets doubles se lit sans les guillemets ni les échappements
(\\" et \\\\), une valeur nue se lit telle quelle, conforme ou non.
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
# le jeton de version (contrôle 4) : la première occurrence, bornée par un caractère non alphanumérique ou le bord,
# de « [vV]?<n>.<n>[.<n>…] » ou de « [vV]<n> » ; « (?!\.?[^\W_]) » empêche de lire « 1.2 » dans « 1.2.3a »
RE_JETON_VERSION = re.compile(r"(?<![^\W_])(?:[vV]?[0-9]+(?:\.[0-9]+)+|[vV][0-9]+)(?!\.?[^\W_])")
RE_DATE = re.compile(rb"\d{2}/\d{2}/\d{4}")
# Le format YAML strict des valeurs (contrôle 11) : voir la docstring.
RE_ENTRE_GUILLEMETS = re.compile(r'"((?:[^"\\]|\\["\\])*)"')
RE_ECHAPPEMENT = re.compile(r'\\(["\\])')
RE_DEUX_POINTS = re.compile(r":(?:\s|$)")
RE_COMMENTAIRE = re.compile(r"\s#")
RE_NON_IMPRIMABLE = re.compile(r"[\x00-\x08\x0b-\x1f\x7f-\x9f\u2028\u2029]")
DEBUTS_INTERDITS = "-?:,[]{}#&*!|>'\"%@`"

NON_DEMANDE = "—  non demandé"
STATUTS_OUVERTS = ("a-venir", "a-cadrer", "dette", "en-vol")
PLAFOND_DEFAUT = 10240  # octets : un checkpoint se relit en entier à chaque reprise
PLAFOND_CHANTIER_DEFAUT = 1536  # octets : une entrée de chantier (contrôle 12)
PLAFOND_REGISTRE_DEFAUT = 800  # caractères : une entrée du registre (contrôle 12)
HORS_DOMAINE = "hors domaine"
OPTIONS_PLAFONDS = (("plafond_checkpoint", "plafond-checkpoint"), ("plafond_chantier", "plafond-chantier"),
                    ("plafond_registre", "plafond-registre"), ("registre_depuis", "registre-depuis"))


def lire_texte(chemin: Path) -> str:
    return chemin.read_text(encoding="utf-8")


def analyser(texte: str):
    """Les lignes utiles du texte : (numéro, début d'entrée, clé, valeur brute) ; sans « : », clé et valeur sont None."""
    commencee = False
    for numero, ligne in enumerate(texte.split("\n"), start=1):
        nue = ligne.strip()
        if not nue or nue.startswith("#"):
            continue
        debut = nue.startswith("- ")
        if debut:
            commencee, nue = True, nue[2:]
        if ":" not in nue or not commencee:
            yield numero, debut, None, None
            continue
        cle, _, brut = nue.partition(":")
        yield numero, debut, cle.strip(), brut


def lire_valeur(brut: str) -> str:
    """La valeur d'une ligne : sans les guillemets doubles ni les échappements (\\" et \\\\) si elle est entre guillemets, sinon telle quelle."""
    valeur = brut.strip()
    entre = RE_ENTRE_GUILLEMETS.fullmatch(valeur)
    return RE_ECHAPPEMENT.sub(r"\1", entre.group(1)) if entre else valeur


def lire_chantiers(chemin: Path) -> list[dict]:
    """Même lecteur que le générateur ; chaque entrée garde sa ligne source (et son fichier)."""
    chantiers: list[dict] = []
    for numero, debut, cle, brut in analyser(lire_texte(chemin)):
        if debut:
            chantiers.append({"_ligne": numero, "_fichier": chemin.name})
        if cle is not None:
            chantiers[-1][cle] = lire_valeur(brut)
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


def nombres(version: str) -> tuple[int, ...]:
    """La suite des nombres du jeton de version d'une valeur : « v1.0065 » → (1, 65) ; « AC-V1.5.1 » → (1, 5, 1) ;
    « v1.10 (R205) » → (1, 10) ; vide si la valeur n'en porte aucun (« … 18a2957, sans release (R188) »)."""
    m = RE_JETON_VERSION.search(version)
    return tuple(int(n) for n in re.findall(r"[0-9]+", m.group(0))) if m else ()


def controle_versions(chantiers: list[dict], archives: list[dict] | None = None):
    portees: dict[str, list[str]] = {}
    for c in chantiers:
        if c.get("version"):
            portees.setdefault(c["version"], []).append(nom(c))
    details = [f"version {v} portée par {' et '.join(ids)}"
               for v, ids in portees.items() if len(ids) > 1]
    # (b) une entrée en vol porte une version plus haute que toute autre du même livrable
    toutes = chantiers + (archives or [])
    for c in chantiers:
        if c.get("statut") != "en-vol" or not c.get("version") or not c.get("livrable") or not nombres(c["version"]):
            continue
        autres = [a for a in toutes if a is not c and a.get("livrable") == c["livrable"]
                  and a.get("version") and nombres(a["version"])]
        if not autres:
            continue
        haute = max(autres, key=lambda a: nombres(a["version"]))
        if nombres(haute["version"]) >= nombres(c["version"]):
            details.append(f"{nom(c)} : {c['version']} n'est pas au-dessus de {haute['version']} ({nom(haute)})")
    return ("ÉCART" if details else "OK"), f"{len(portees)} versions", details


def controle_en_vol(chantiers: list[dict]):
    en_vol = [c for c in chantiers if c.get("statut") == "en-vol"]
    details = [f"{nom(c)} (ligne {c['_ligne']}) : cdp absent ou vide"
               for c in en_vol if not c.get("cdp")]
    return ("ÉCART" if details else "OK"), f"{len(en_vol)} en vol", details


def ecart_texte(voulu: bytes, obtenu: bytes):
    """None si les deux textes sont égaux ; sinon (octet du premier écart, ligne)."""
    if voulu == obtenu:
        return None
    rang = next((i for i, (a, b) in enumerate(zip(voulu, obtenu)) if a != b), min(len(voulu), len(obtenu)))
    return rang, voulu.count(b"\n", 0, rang) + 1


def controle_tableau(chantiers: list[dict], chantiers_yaml: Path, tableau: Path, generateur: Path):
    """La page et son fichier de données (à côté, même nom en .json) contre leur régénération."""
    compte = f"{len(chantiers)} chantiers"
    donnees = tableau.with_suffix(".json")
    with tempfile.TemporaryDirectory(prefix="vivants-") as dossier:
        # même nom que la page publiée : la page porte le nom de son fichier de données
        sortie = Path(dossier) / tableau.name
        sortie_donnees = sortie.with_suffix(".json")
        essai = subprocess.run([sys.executable, "-B", str(generateur.resolve()), str(chantiers_yaml.resolve()), str(sortie)],
                               capture_output=True, text=True, cwd=dossier)
        if essai.returncode != 0 or not sortie.is_file():
            message = (essai.stderr.strip() or essai.stdout.strip() or "sans message").splitlines()[-1]
            return "ÉCART", compte, [f"le générateur a échoué (code {essai.returncode}) : {message}"]
        if not sortie_donnees.is_file():
            return "ÉCART", compte, [f"le générateur n'a pas écrit le fichier de données {sortie_donnees.name}"]
        page_publiee, page_regeneree = tableau.read_bytes(), sortie.read_bytes()
        donnees_regenerees = sortie_donnees.read_bytes()
        donnees_publiees = donnees.read_bytes() if donnees.is_file() else None
    details = []
    comparaisons = [("la page du tableau", page_publiee, page_regeneree)]
    if donnees_publiees is None:
        details.append(f"fichier de données absent : {donnees}")
    else:
        comparaisons.append(("le fichier de données", donnees_publiees, donnees_regenerees))
    for nom_fichier, brut, regenere in comparaisons:
        voulu, obtenu = RE_DATE.sub(b"<date>", brut), RE_DATE.sub(b"<date>", regenere)
        ecart = ecart_texte(voulu, obtenu)
        if ecart:
            rang, ligne = ecart
            details.append(f"{nom_fichier} diffère de sa régénération (dates masquées) : premier écart à l'octet "
                           f"{rang} (ligne {ligne}) ; {len(voulu)} octets contre {len(obtenu)} régénérés")
    if details:
        return "ÉCART", compte, details
    return "OK", (f"{compte}, page {len(page_publiee)} octets et données {len(donnees_publiees)} octets "
                  f"identiques hors date"), []


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
    """Les défauts de la table, ou : file non déclarée, file qui cite du clos (9b), ouverts non cités dans la file (9c)."""
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
    zone = section if section is not None else texte  # la citation se cherche dans la file ; sans file, dans tout le checkpoint
    positions = sorted((section.find(citation(i)), i) for i in clos if citation(i) in section) if section else []
    cites = [f"{nom_d} : la file cite {i}, clos ({clos[i]})" for _, i in positions]
    non_cites = [f"{nom_d} : {c['id']} ({c['statut']}) n'est pas cité au checkpoint"
                 for c in chantiers
                 if c.get("id") and c.get("statut") in STATUTS_OUVERTS and "pour" not in c
                 and domaine_de(c, domaines) == nom_d and citation(c["id"]) not in zone]
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


def taille_entree(lignes: list[str]) -> int:
    """Les octets UTF-8 des lignes d'une entrée, chacune suivie d'un saut de ligne, sans les lignes vides ni les « # »."""
    return sum(len(ligne.encode("utf-8")) + 1 for ligne in lignes if ligne.strip() and not ligne.strip().startswith("#"))


def controle_entrees(chantiers: list[dict], chantiers_texte: str, registre_texte: str, table: list[dict],
                     plafond_chantier: int, plafond_registre: int, registre_depuis: int | None):
    """Une entrée de chantier ouverte (hors « arbitre- ») ou du registre au-delà de son plafond est un écart."""
    valides = [d for d in table if d.get("domaine") and d.get("checkpoint")]
    lignes = chantiers_texte.split("\n")
    details, mesurees = [], 0
    for rang, c in enumerate(chantiers):
        if c.get("statut") not in STATUTS_OUVERTS or c.get("id", "").startswith("arbitre-"):
            continue
        mesurees += 1
        fin = chantiers[rang + 1]["_ligne"] - 1 if rang + 1 < len(chantiers) else len(lignes)
        taille = taille_entree(lignes[c["_ligne"] - 1:fin])
        if taille > plafond_chantier:
            domaine = domaine_de(c, valides) if c.get("id") else None
            details.append(f"{domaine or HORS_DOMAINE} : chantier {nom(c)} pèse {taille} octets, plafond {plafond_chantier}")
    mesurees_registre = 0
    if registre_depuis is not None:
        for ligne in registre_texte.split("\n"):
            m = RE_NUMERO.match(ligne)
            if not m or int(m.group(1)) < registre_depuis or RE_RESERVATION.match(ligne):
                continue
            mesurees_registre += 1
            if len(ligne) > plafond_registre:
                details.append(f"registre : R{m.group(1)} compte {len(ligne)} caractères, plafond {plafond_registre}")
    suite = f"{mesurees_registre} entrées du registre" if registre_depuis is not None else "registre non mesuré"
    compte = f"{mesurees} chantiers ouverts, {suite}, {len(details)} au-delà"
    return ("ÉCART" if details else "OK"), compte, details


def valeur_conforme(brut: str) -> bool:
    """Un scalaire YAML sûr : vide, entre guillemets doubles, ou nu et sans rien que YAML lirait autrement."""
    valeur = brut.strip()
    if RE_NON_IMPRIMABLE.search(valeur):
        return False
    if not valeur or RE_ENTRE_GUILLEMETS.fullmatch(valeur):
        return True
    return not (valeur[0] in DEBUTS_INTERDITS or "\t" in valeur
                or RE_DEUX_POINTS.search(valeur) or RE_COMMENTAIRE.search(valeur))


def nombre_de_lignes(texte: str) -> int:
    return texte.count("\n") + (0 if not texte or texte.endswith("\n") else 1)


def commande_normaliser(fichiers: dict) -> str:
    """La commande qui normalise les fichiers contrôlés, avec les chemins tels que donnés."""
    options = [f"--chantiers {fichiers['chantiers']}"]
    options += [f"--{option} {fichiers[option]}" for option in ("archives", "domaines") if option in fichiers]
    return "python3 -B archiver_chantiers.py normaliser " + " ".join(options)


def controle_format(fichiers: list[Path], commande: str):
    """Chaque valeur de chaque fichier est un scalaire YAML sûr (voir la docstring) ; le nombre de fichiers et de lignes lus."""
    lignes, non_conformes = 0, []
    for chemin in fichiers:
        texte = lire_texte(chemin)
        lignes += nombre_de_lignes(texte)
        non_conformes += [f"{chemin}:{numero} : clé {cle}" for numero, _, cle, brut in analyser(texte)
                          if cle is not None and not valeur_conforme(brut)]
    compte = f"{len(fichiers)} fichiers, {lignes} lignes lues"
    if not non_conformes:
        return "OK", compte, []
    compte = f"{len(non_conformes)} valeur(s) non conforme(s), {compte}"
    return "ÉCART", compte, non_conformes[:5] + [f"pour normaliser : {commande}"]


class Analyseur(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError(message.replace("expected one argument", "valeur manquante"))


def fichiers_archives(dossier: Path) -> list[Path]:
    """Les archives du dossier, par ordre de nom de fichier."""
    return sorted(p for p in dossier.glob("CHANTIERS_*.yaml") if p.is_file())


def lire_archives(dossier: Path) -> list[dict]:
    """Les entrées de toutes les archives du dossier, par ordre de nom de fichier."""
    archives: list[dict] = []
    for fichier in fichiers_archives(dossier):
        archives += lire_chantiers(fichier)
    return archives


def lire_arguments(argv: list[str]):
    p = Analyseur(prog="verifier_vivants.py", allow_abbrev=False, add_help=False)
    for option in ("chantiers", "registre", "tableau", "generateur", "journal", "archives", "domaines", "racine"):
        p.add_argument(f"--{option}")
    for _, option in OPTIONS_PLAFONDS:
        p.add_argument(f"--{option}")
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
    plafonds = {"plafond_checkpoint": PLAFOND_DEFAUT, "plafond_chantier": PLAFOND_CHANTIER_DEFAUT,
                "plafond_registre": PLAFOND_REGISTRE_DEFAUT, "registre_depuis": None}
    for attribut, option in OPTIONS_PLAFONDS:
        valeur = getattr(a, attribut)
        if valeur is None:
            continue
        if not a.domaines:
            raise ValueError(f"--{option} ne va qu'avec --domaines")
        if not re.fullmatch(r"[0-9]+", valeur) or int(valeur) < 1:
            raise ValueError(f"--{option} : un entier positif est attendu ({valeur})")
        plafonds[attribut] = int(valeur)
    chemins = {option: Path(getattr(a, option)) for option in
               ("chantiers", "registre", "tableau", "generateur", "journal", "archives", "domaines", "racine")
               if getattr(a, option)}
    for option, chemin in chemins.items():
        if not (chemin.is_dir() if option in ("archives", "racine") else chemin.is_file()):
            raise ValueError(f"fichier introuvable : --{option} {chemin}")
    return chemins, plafonds


def main(argv: list[str]) -> int:
    try:
        f, plafonds = lire_arguments(argv)
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
        ("versions des lots", lambda: controle_versions(chantiers, archives)),
        ("chantiers en vol", lambda: controle_en_vol(chantiers)),
        ("tableau", (lambda: controle_tableau(chantiers, f["chantiers"], f["tableau"], f["generateur"]))
         if "tableau" in f else None),
        ("journal", (lambda: controle_journal(chantiers + (archives or []), f["journal"])) if "journal" in f else None),
        ("livrables et ressources", lambda: controle_livrables(chantiers)),
        ("checkpoints", (lambda: controle_checkpoints(chantiers, archives, table, f.get("racine", Path("."))))
         if table is not None else None),
        ("taille des checkpoints", (lambda: controle_taille(table, f.get("racine", Path(".")), plafonds["plafond_checkpoint"]))
         if table is not None else None),
        ("format YAML", lambda: controle_format(
            [f["chantiers"]] + (fichiers_archives(f["archives"]) if "archives" in f else [])
            + ([f["domaines"]] if "domaines" in f else []), commande_normaliser(f))),
        ("taille des entrées", (lambda: controle_entrees(
            chantiers, lire_texte(f["chantiers"]), lire_texte(f["registre"]), table, plafonds["plafond_chantier"],
            plafonds["plafond_registre"], plafonds["registre_depuis"])) if table is not None else None),
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
