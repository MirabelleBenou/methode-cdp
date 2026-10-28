"""Les ordres : un objet JSON par fichier ``ordres/<id>.json``. Champ inconnu, champ manquant, valeur hors forme,
action inconnue : refus, rien ne bouge. La validation a lieu en entier avant toute action.
"""

import datetime
import json
import re
from collections import namedtuple

from . import reseau, zones

Ordre = namedtuple("Ordre", "id action demande_par champs brut")

FILE_DEPLOIEMENT = "deploiement"
FILE_FICHIERS = "fichiers"

ACTIONS_DEPLOIEMENT = ("etat", "adopter", "deployer-application", "deployer-suite", "revenir", "reprendre-file")
ACTION_FICHIERS = "fichiers"
ACTIONS = ACTIONS_DEPLOIEMENT + (ACTION_FICHIERS,)

OPERATIONS = ("lister", "empreinte", "creer-dossier", "telecharger", "copier", "deplacer", "decompresser",
              "basculer", "mettre-a-la-corbeille", "vider-la-corbeille")
MAX_OPERATIONS = 50
MAX_EMPREINTES = 50

RE_ID = re.compile(r"^(\d{4})-(\d{2})-(\d{2})-(\d{2})$")
RE_COMMIT = re.compile(r"^[0-9a-f]{40}$")
RE_SHA256 = re.compile(r"^[0-9a-f]{64}$")
RE_VERSION = re.compile(r"^[0-9A-Za-z][0-9A-Za-z._+-]{0,31}$")
RE_STEM = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
EXTENSIONS_ARCHIVES = (".tar", ".tar.gz", ".tgz", ".zip")


class OrdreInvalide(ValueError):
    pass


def id_valide(texte):
    m = RE_ID.match(texte or "")
    if not m:
        return False
    try:
        datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return False
    return True


def file_de(texte):
    """Dans quelle file un ordre (texte JSON brut) doit-il être joué ? Tout ce qui n'est pas ``fichiers`` va
    à la file ``deploiement``, qui le refusera s'il est invalide."""
    try:
        obj = json.loads(texte)
    except ValueError:
        return FILE_DEPLOIEMENT
    if isinstance(obj, dict) and obj.get("action") == ACTION_FICHIERS:
        return FILE_FICHIERS
    return FILE_DEPLOIEMENT


def _texte(o, cle, maxi=500):
    v = o.get(cle)
    if not isinstance(v, str) or not v.strip():
        raise OrdreInvalide("champ '%s' : texte non vide attendu" % cle)
    if len(v) > maxi or "\0" in v:
        raise OrdreInvalide("champ '%s' : texte trop long ou invalide" % cle)
    return v


def _forme(o, cle, regex, quoi):
    v = o.get(cle)
    if not isinstance(v, str) or not regex.match(v):
        raise OrdreInvalide("champ '%s' : %s attendu" % (cle, quoi))
    return v


def _verifier_champs(o, obligatoires, facultatifs, quoi):
    inconnus = sorted(set(o) - set(obligatoires) - set(facultatifs))
    if inconnus:
        raise OrdreInvalide("%s : champ inconnu : %s" % (quoi, ", ".join(inconnus)))
    manquants = [c for c in obligatoires if c not in o]
    if manquants:
        raise OrdreInvalide("%s : champ manquant : %s" % (quoi, ", ".join(manquants)))


def _zone(o, cle, cfg):
    v = o.get(cle)
    if not isinstance(v, str) or v not in cfg.zones:
        raise OrdreInvalide("champ '%s' : zone inconnue (%r)" % (cle, v))
    return v


def _chemin(o, cle, vide_ok=False):
    try:
        return zones.valider_relatif(o.get(cle), vide_ok=vide_ok)
    except zones.ErreurChemin as e:
        raise OrdreInvalide("champ '%s' : %s" % (cle, e))


def _operation(op, rang, cfg):
    quoi = "opération %d" % rang
    if not isinstance(op, dict):
        raise OrdreInvalide("%s : objet attendu" % quoi)
    nom = op.get("operation")
    if nom not in OPERATIONS:
        raise OrdreInvalide("%s : opération inconnue (%r)" % (quoi, nom))
    quoi = "opération %d (%s)" % (rang, nom)
    try:
        if nom == "lister":
            _verifier_champs(op, ("operation", "zone", "chemin"), ("profondeur",), quoi)
            _zone(op, "zone", cfg)
            _chemin(op, "chemin", vide_ok=True)
            p = op.get("profondeur", 1)
            if isinstance(p, bool) or not isinstance(p, int) or not 1 <= p <= 3:
                raise OrdreInvalide("champ 'profondeur' : entier de 1 à 3 attendu")
        elif nom == "empreinte":
            _verifier_champs(op, ("operation", "zone", "chemins"), (), quoi)
            _zone(op, "zone", cfg)
            ch = op.get("chemins")
            if not isinstance(ch, list) or not 1 <= len(ch) <= MAX_EMPREINTES:
                raise OrdreInvalide("champ 'chemins' : liste de 1 à %d chemins attendue" % MAX_EMPREINTES)
            for c in ch:
                _chemin({"c": c}, "c")
        elif nom == "creer-dossier":
            _verifier_champs(op, ("operation", "zone", "chemin"), (), quoi)
            _zone(op, "zone", cfg)
            _chemin(op, "chemin")
        elif nom == "telecharger":
            _verifier_champs(op, ("operation", "zone", "chemin", "source"), ("sha256",), quoi)
            _zone(op, "zone", cfg)
            _chemin(op, "chemin")
            try:
                reseau.analyser_source(op.get("source"), cfg)
            except reseau.ErreurSource as e:
                raise OrdreInvalide("champ 'source' : %s" % e)
            if "sha256" in op:
                _forme(op, "sha256", RE_SHA256, "sha256 de 64 caractères hexadécimaux (minuscules)")
        elif nom in ("copier", "deplacer"):
            _verifier_champs(op, ("operation", "zone", "de", "vers"), ("zone_vers", "si_existe"), quoi)
            _zone(op, "zone", cfg)
            if "zone_vers" in op:
                _zone(op, "zone_vers", cfg)
            _chemin(op, "de")
            _chemin(op, "vers")
            if op.get("si_existe", "refuser") not in ("refuser", "remplacer"):
                raise OrdreInvalide("champ 'si_existe' : 'refuser' ou 'remplacer' attendu")
        elif nom == "decompresser":
            _verifier_champs(op, ("operation", "zone", "archive", "vers"), (), quoi)
            _zone(op, "zone", cfg)
            a = _chemin(op, "archive")
            _chemin(op, "vers")
            if not a.lower().endswith(EXTENSIONS_ARCHIVES):
                raise OrdreInvalide("champ 'archive' : .tar, .tar.gz, .tgz ou .zip attendu")
        elif nom == "basculer":
            _verifier_champs(op, ("operation", "zone", "prepare", "servi"), (), quoi)
            _zone(op, "zone", cfg)
            if _chemin(op, "prepare") == _chemin(op, "servi"):
                raise OrdreInvalide("'prepare' et 'servi' doivent différer")
        elif nom == "mettre-a-la-corbeille":
            _verifier_champs(op, ("operation", "zone", "chemin"), (), quoi)
            _zone(op, "zone", cfg)
            _chemin(op, "chemin")
        elif nom == "vider-la-corbeille":
            _verifier_champs(op, ("operation", "zone"), ("id_corbeille",), quoi)
            _zone(op, "zone", cfg)
            if "id_corbeille" in op and not id_valide(op.get("id_corbeille")):
                raise OrdreInvalide("champ 'id_corbeille' : identifiant d'ordre AAAA-MM-JJ-NN attendu")
    except OrdreInvalide as e:
        if str(e).startswith(quoi):
            raise
        raise OrdreInvalide("%s : %s" % (quoi, e))


def charger(texte, stem, cfg):
    """Analyse et valide un ordre. ``stem`` est le nom du fichier sans ``.json``. Lève OrdreInvalide."""
    try:
        o = json.loads(texte)
    except ValueError as e:
        raise OrdreInvalide("JSON illisible : %s" % e)
    if not isinstance(o, dict):
        raise OrdreInvalide("un ordre est un objet JSON")
    if not id_valide(o.get("id") if isinstance(o.get("id"), str) else ""):
        raise OrdreInvalide("champ 'id' : AAAA-MM-JJ-NN (date valide) attendu")
    if o["id"] != stem:
        raise OrdreInvalide("l'id (%s) doit égaler le nom du fichier (%s)" % (o["id"], stem))
    action = o.get("action")
    if action not in ACTIONS:
        raise OrdreInvalide("action inconnue : %r" % (action,))
    demande_par = _texte(o, "demande_par", 200)

    communs = ("id", "action", "demande_par")
    if action == "etat":
        _verifier_champs(o, communs, (), "ordre")
    elif action == "adopter":
        _verifier_champs(o, communs + ("commit",), (), "ordre")
        _forme(o, "commit", RE_COMMIT, "commit de 40 caractères hexadécimaux (minuscules)")
    elif action == "deployer-application":
        _verifier_champs(o, communs + ("commit", "version", "go"), (), "ordre")
        _forme(o, "commit", RE_COMMIT, "commit de 40 caractères hexadécimaux (minuscules)")
        _forme(o, "version", RE_VERSION, "version")
        _texte(o, "go")
    elif action == "deployer-suite":
        _verifier_champs(o, communs + ("suite", "commit", "sha256"), (), "ordre")
        if o.get("suite") not in cfg.suites:
            raise OrdreInvalide("champ 'suite' : suite inconnue (%r)" % (o.get("suite"),))
        _forme(o, "commit", RE_COMMIT, "commit de 40 caractères hexadécimaux (minuscules)")
        _forme(o, "sha256", RE_SHA256, "sha256 de 64 caractères hexadécimaux (minuscules)")
    elif action == "revenir":
        _verifier_champs(o, communs + ("cible",), ("go",), "ordre")
        cible = o.get("cible")
        if cible == "application":
            _texte(o, "go")
        elif cible in cfg.suites:
            if "go" in o:
                _texte(o, "go")
        else:
            raise OrdreInvalide("champ 'cible' : 'application' ou une suite connue attendu (%r)" % (cible,))
    elif action == "reprendre-file":
        _verifier_champs(o, communs + ("file", "go"), (), "ordre")
        if o.get("file") not in (FILE_DEPLOIEMENT, FILE_FICHIERS):
            raise OrdreInvalide("champ 'file' : 'deploiement' ou 'fichiers' attendu")
        _texte(o, "go")
    elif action == ACTION_FICHIERS:
        _verifier_champs(o, communs + ("operations",), ("go",), "ordre")
        ops = o.get("operations")
        if not isinstance(ops, list) or not 1 <= len(ops) <= MAX_OPERATIONS:
            raise OrdreInvalide("champ 'operations' : liste de 1 à %d opérations attendue" % MAX_OPERATIONS)
        for i, op in enumerate(ops, 1):
            _operation(op, i, cfg)
        if "go" in o:
            _texte(o, "go")
        if any(op["operation"] == "vider-la-corbeille" for op in ops) and "go" not in o:
            raise OrdreInvalide("'vider-la-corbeille' exige un champ 'go' non vide dans l'ordre")
    champs = {k: v for k, v in o.items() if k not in communs}
    return Ordre(o["id"], action, demande_par, champs, o)
