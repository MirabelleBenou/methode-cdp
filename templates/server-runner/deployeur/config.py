"""La configuration : lue, validée au démarrage, jamais devinée.

Tout ce qui est propre à une installation (projet, dossiers, volumes, dépôts, zones, suites…) vient d'ici.
Le programme refuse de tourner sur une configuration invalide.
"""

import json
import os
import re
from collections import namedtuple

from . import zones as _zones

CHEMIN_DEFAUT = "/etc/deployeur/config.json"
ETAT_DEFAUT = "/var/lib/deployeur"

CHEMINS_PROTEGES_DEFAUT = (".env", "backups/")

RE_NOM = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
RE_NOM_ZONE = re.compile(r"^[a-z][a-z0-9_-]{0,31}$")
RE_DEPOT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*/[A-Za-z0-9][A-Za-z0-9_.-]*$")
RE_HOTE = re.compile(r"^[a-z0-9]([a-z0-9.-]*[a-z0-9])?$")
RE_TABLE = re.compile(r"^[a-z_][a-z0-9_]{0,62}$")
RE_BRANCHE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_./-]*$")

Git = namedtuple("Git", "cle_ordres cle_application known_hosts identite_nom identite_courriel")
DepotOrdres = namedtuple("DepotOrdres", "url branche")
Suite = namedtuple("Suite", "nom depot chemin dossier fichier")
Application = namedtuple(
    "Application",
    "projet dossier fichier_compose service_app service_db conteneur_db volume_base montage_base "
    "volume_ecussons volume_depots_bruts prefixe_sauvegarde url_sante depot_url tables_histoire "
    "chemins_proteges place_min_deploiement_go sauvegardes_garder delai_sante_s intervalle_sante_s",
)
Config = namedtuple(
    "Config",
    "repertoire_etat git depot_ordres application suites hote_fichiers_bruts zones zone_transfert "
    "depots_publics hotes_autorises intervalle_en_cours_s",
)


class ErreurConfig(Exception):
    def __init__(self, problemes):
        self.problemes = list(problemes)
        super().__init__("configuration invalide : " + " ; ".join(self.problemes))


def garder_effectif(app):
    """Nombre de sauvegardes du déployeur gardées : jamais moins de trois."""
    return max(3, int(app.sauvegardes_garder))


def _abs(v):
    return isinstance(v, str) and os.path.isabs(v) and "\0" not in v and ".." not in v.split("/") \
        and not re.search(r"\s", v)


def _txt(d, cle, problemes, regex=None, defaut=None, prefixe=""):
    v = d.get(cle, defaut)
    if not isinstance(v, str) or not v or (regex is not None and not regex.match(v)):
        problemes.append("%s%s : texte attendu%s" % (prefixe, cle, " (forme invalide)" if isinstance(v, str) else ""))
        return ""
    return v


def _nombre(d, cle, problemes, defaut=None, minimum=0, entier=False, prefixe=""):
    v = d.get(cle, defaut)
    if isinstance(v, bool) or not isinstance(v, (int, float)) or (entier and not isinstance(v, int)) or v < minimum:
        problemes.append("%s%s : nombre %s≥ %s attendu" % (prefixe, cle, "entier " if entier else "", minimum))
        return minimum
    return v


def _liste_txt(d, cle, problemes, regex=None, vide_ok=False, defaut=None, prefixe=""):
    v = d.get(cle, defaut)
    if not isinstance(v, list) or (not v and not vide_ok) or not all(
            isinstance(x, str) and x and (regex is None or regex.match(x)) for x in v):
        problemes.append("%s%s : liste de textes %s attendue" % (prefixe, cle, "" if vide_ok else "non vide "))
        return []
    return list(v)


def _objet(d, cle, problemes):
    v = d.get(cle)
    if not isinstance(v, dict):
        problemes.append("%s : objet attendu" % cle)
        return {}
    return v


def _url_depot(v):
    return isinstance(v, str) and bool(re.match(r"^(git@[A-Za-z0-9.-]+:[^\s]+|ssh://[^\s]+|https://[^\s]+|file://[^\s]+|/[^\s]+)$", v)) \
        and not v.startswith("-")


def valider(brut):
    """Valide un dictionnaire de configuration et retourne une ``Config`` ; lève ErreurConfig sinon."""
    p = []
    if not isinstance(brut, dict):
        raise ErreurConfig(["la configuration doit être un objet JSON"])

    etat = brut.get("repertoire_etat", ETAT_DEFAUT)
    if not _abs(etat):
        p.append("repertoire_etat : chemin absolu attendu")

    g = _objet(brut, "git", p)
    git = Git(
        cle_ordres=g.get("cle_ordres", ""), cle_application=g.get("cle_application", ""),
        known_hosts=g.get("known_hosts", ""),
        identite_nom=_txt(g, "identite_nom", p, prefixe="git."),
        identite_courriel=_txt(g, "identite_courriel", p, prefixe="git."),
    )
    for k in ("cle_ordres", "cle_application", "known_hosts"):
        if not _abs(getattr(git, k)):
            p.append("git.%s : chemin absolu sans espace attendu" % k)

    d = _objet(brut, "depot_ordres", p)
    if not _url_depot(d.get("url")):
        p.append("depot_ordres.url : adresse de dépôt attendue")
    depot_ordres = DepotOrdres(d.get("url", ""), _txt(d, "branche", p, RE_BRANCHE, defaut="main", prefixe="depot_ordres."))

    a = _objet(brut, "application", p)
    pre = "application."
    dossier = a.get("dossier", "")
    if not _abs(dossier):
        p.append("application.dossier : chemin absolu attendu")
    if not _url_depot(a.get("depot_url")):
        p.append("application.depot_url : adresse de dépôt attendue")
    url_sante = a.get("url_sante", "")
    if not (isinstance(url_sante, str) and re.match(r"^https?://[^\s]+$", url_sante)):
        p.append("application.url_sante : adresse http(s) attendue")
    montage = a.get("montage_base", "")
    if not _abs(montage):
        p.append("application.montage_base : chemin absolu attendu")
    tables = _liste_txt(a, "tables_histoire", p, RE_TABLE, prefixe=pre)
    proteges = list(CHEMINS_PROTEGES_DEFAUT)
    supp = a.get("chemins_proteges", [])
    if not isinstance(supp, list) or not all(isinstance(x, str) and x and not x.startswith("/") and ".." not in x.split("/")
                                              for x in supp):
        p.append("application.chemins_proteges : liste de chemins relatifs attendue")
    else:
        proteges += [x for x in supp if x not in proteges]
    app = Application(
        projet=_txt(a, "projet", p, RE_NOM, prefixe=pre), dossier=dossier,
        fichier_compose=_txt(a, "fichier_compose", p, RE_NOM, defaut="docker-compose.yml", prefixe=pre),
        service_app=_txt(a, "service_app", p, RE_NOM, prefixe=pre),
        service_db=_txt(a, "service_db", p, RE_NOM, prefixe=pre),
        conteneur_db=_txt(a, "conteneur_db", p, RE_NOM, prefixe=pre),
        volume_base=_txt(a, "volume_base", p, RE_NOM, prefixe=pre), montage_base=montage,
        volume_ecussons=_txt(a, "volume_ecussons", p, RE_NOM, prefixe=pre),
        volume_depots_bruts=_txt(a, "volume_depots_bruts", p, RE_NOM, prefixe=pre),
        prefixe_sauvegarde=_txt(a, "prefixe_sauvegarde", p, RE_NOM, prefixe=pre),
        url_sante=url_sante, depot_url=a.get("depot_url", ""), tables_histoire=tables,
        chemins_proteges=proteges,
        place_min_deploiement_go=_nombre(a, "place_min_deploiement_go", p, defaut=3, prefixe=pre),
        sauvegardes_garder=_nombre(a, "sauvegardes_garder", p, defaut=10, entier=True, prefixe=pre),
        delai_sante_s=_nombre(a, "delai_sante_s", p, defaut=180, minimum=1, prefixe=pre),
        intervalle_sante_s=_nombre(a, "intervalle_sante_s", p, defaut=5, minimum=0, prefixe=pre),
    )

    suites = {}
    sb = brut.get("suites", {})
    if not isinstance(sb, dict):
        p.append("suites : objet attendu")
        sb = {}
    for nom, s in sb.items():
        if not RE_NOM_ZONE.match(nom) or not isinstance(s, dict):
            p.append("suites.%s : nom ou objet invalide" % nom)
            continue
        pr = "suites.%s." % nom
        depot = _txt(s, "depot", p, RE_DEPOT, prefixe=pr)
        chemin = s.get("chemin", "")
        try:
            _zones.valider_relatif(chemin)
        except _zones.ErreurChemin:
            p.append(pr + "chemin : chemin relatif au dépôt attendu")
        dos = s.get("dossier", "")
        if not _abs(dos):
            p.append(pr + "dossier : chemin absolu attendu")
        fichier = _txt(s, "fichier", p, RE_NOM, prefixe=pr)
        suites[nom] = Suite(nom, depot, chemin, dos, fichier)

    hote = _txt(brut, "hote_fichiers_bruts", p, RE_HOTE, defaut="raw.githubusercontent.com")

    zones = {}
    zb = brut.get("zones", {})
    if not isinstance(zb, dict) or not zb:
        p.append("zones : objet non vide attendu")
        zb = {}
    interdits = [dossier, etat] + [s.dossier for s in suites.values()]
    for nom, z in zb.items():
        if not RE_NOM_ZONE.match(nom) or not isinstance(z, dict):
            p.append("zones.%s : nom ou objet invalide" % nom)
            continue
        zone = _zones.Zone(nom, z.get("chemin", ""), _nombre(z, "place_min_go", p, defaut=20, prefixe="zones.%s." % nom))
        problemes_zone = _zones.verifier_zone(zone, [x for x in interdits if _abs(x)])
        p.extend(problemes_zone)
        zones[nom] = zone
    transfert = brut.get("zone_transfert", "")
    if transfert not in zones:
        p.append("zone_transfert : doit nommer une zone déclarée")

    depots_publics = _liste_txt(brut, "depots_publics", p, RE_DEPOT, vide_ok=True, defaut=[])
    hotes = _liste_txt(brut, "hotes_autorises", p, RE_HOTE, vide_ok=True, defaut=[])
    interv = _nombre(brut, "intervalle_en_cours_s", p, defaut=300, minimum=0)

    if p:
        raise ErreurConfig(p)
    return Config(etat, git, depot_ordres, app, suites, hote, zones, transfert,
                  [x.lower() for x in depots_publics], [x.lower() for x in hotes], interv)


def charger(chemin=None):
    chemin = chemin or CHEMIN_DEFAUT
    try:
        with open(chemin, "rb") as f:
            brut = json.loads(f.read().decode("utf-8"))
    except FileNotFoundError:
        raise ErreurConfig(["fichier de configuration introuvable : %s" % chemin])
    except (ValueError, OSError) as e:
        raise ErreurConfig(["fichier de configuration illisible (%s) : %s" % (chemin, e)])
    return valider(brut)
