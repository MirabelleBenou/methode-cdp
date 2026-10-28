"""Les zones : des dossiers déclarés dans la configuration, dans lesquels seules les opérations de fichiers
peuvent agir. Les chemins d'un ordre sont toujours relatifs à une zone et contrôlés ici.
"""

import os
from collections import namedtuple

Zone = namedtuple("Zone", "nom chemin place_min_go")

NOM_CORBEILLE = "_corbeille"

# Une zone ne peut pas contenir, ni être contenue dans, ces chemins (sauf la racine : voir verifier_zone).
INTERDITS_FIXES = (
    "/var/lib/docker", "/etc", "/var/lib/deployeur", "/etc/deployeur", "/home", "/root", "/usr", "/boot",
)


class ErreurChemin(ValueError):
    """Un chemin d'ordre n'est pas acceptable (absolu, '..', nul, hors de la zone…)."""


def _composants(chemin):
    return [c for c in os.path.normpath(chemin).split(os.sep) if c]


def _contient(parent, enfant):
    """``enfant`` est ``parent`` ou est dessous (comparaison par composants)."""
    p, e = _composants(parent), _composants(enfant)
    return e[:len(p)] == p


def verifier_zone(zone, dossiers_interdits):
    """Retourne la liste des problèmes de ``zone`` (vide : conforme). Contrôle le chemin tel qu'écrit et résolu."""
    problemes = []
    c = zone.chemin
    if not isinstance(c, str) or not os.path.isabs(c) or "\0" in c:
        return ["zone %s : le chemin doit être absolu" % zone.nom]
    if os.path.normpath(c) != c.rstrip("/") and c != "/":
        problemes.append("zone %s : chemin non normalisé (%s)" % (zone.nom, c))
    if ".." in c.split("/"):
        problemes.append("zone %s : composant '..' interdit" % zone.nom)
    for forme in {os.path.normpath(c), os.path.realpath(c)}:
        if forme == "/":
            problemes.append("zone %s : la racine ne peut pas être une zone" % zone.nom)
            continue
        for interdit in list(INTERDITS_FIXES) + list(dossiers_interdits):
            for f2 in {os.path.normpath(interdit), os.path.realpath(interdit)}:
                if f2 == "/":
                    continue
                if _contient(f2, forme) or _contient(forme, f2):
                    problemes.append("zone %s : %s est interdit (contient ou est contenu dans %s)"
                                     % (zone.nom, forme, f2))
    seen = []
    for p in problemes:
        if p not in seen:
            seen.append(p)
    return seen


def valider_relatif(chemin, vide_ok=False):
    """Contrôle syntaxique d'un chemin relatif à une zone ; retourne la forme normalisée ('' pour la racine)."""
    if not isinstance(chemin, str):
        raise ErreurChemin("le chemin doit être un texte")
    if "\0" in chemin:
        raise ErreurChemin("caractère nul dans le chemin")
    if chemin.startswith("/") or os.path.isabs(chemin):
        raise ErreurChemin("chemin absolu refusé : %r" % chemin)
    morceaux = chemin.split("/")
    if ".." in morceaux:
        raise ErreurChemin("composant '..' refusé : %r" % chemin)
    propres = [m for m in morceaux if m not in ("", ".")]
    if not propres:
        if vide_ok:
            return ""
        raise ErreurChemin("chemin vide")
    return "/".join(propres)


def _dans(base, chemin):
    return chemin == base or chemin.startswith(base.rstrip(os.sep) + os.sep)


def racine(zone):
    """Chemin réel (liens résolus) de la racine de la zone ; la zone doit exister."""
    reel = os.path.realpath(zone.chemin)
    if not os.path.isdir(reel):
        raise ErreurChemin("la zone %s n'existe pas sur la machine (%s)" % (zone.nom, zone.chemin))
    return reel


def resoudre(zone, relatif, vide_ok=False, corbeille_ok=True):
    """Retourne le chemin absolu (jonction lexicale sous la racine réelle) après contrôles.

    Refus : chemin absolu, '..', nul ; tout lien symbolique qui fait sortir de la zone ; (si ``corbeille_ok``
    est faux) tout chemin dans la corbeille de la zone.
    """
    rel = valider_relatif(relatif, vide_ok=vide_ok)
    base = racine(zone)
    cible = os.path.join(base, rel) if rel else base
    if rel:
        parent_reel = os.path.realpath(os.path.dirname(cible))
        if not _dans(base, parent_reel):
            raise ErreurChemin("le chemin sort de la zone %s : %r" % (zone.nom, relatif))
        if os.path.islink(cible):
            if not _dans(base, os.path.realpath(cible)):
                raise ErreurChemin("lien symbolique qui sort de la zone %s : %r" % (zone.nom, relatif))
        elif not _dans(base, os.path.realpath(cible)):
            raise ErreurChemin("le chemin sort de la zone %s : %r" % (zone.nom, relatif))
    if not corbeille_ok and rel and (rel == NOM_CORBEILLE or rel.startswith(NOM_CORBEILLE + "/")):
        raise ErreurChemin("la corbeille de la zone n'est pas une cible permise : %r" % relatif)
    return cible


def relatif_a(zone, chemin_abs):
    base = racine(zone)
    return os.path.relpath(chemin_abs, base)
