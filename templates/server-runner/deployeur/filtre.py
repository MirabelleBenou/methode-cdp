"""Le filtre : tout texte issu d'un journal ou d'une commande passe ici avant d'être écrit au dépôt.

Il masque (``***``) : la valeur de toute affectation dont la clé contient TOKEN, SECRET, PASSWORD, PASSWD,
PASS, KEY, AUTH, COOKIE, SESSION, DSN ou DATABASE_URL (sans égard à la casse) ; le mot de passe d'une URL ;
un en-tête Authorization ou Cookie ; un paramètre d'URL token=, code=, state= ; une URL de webhook Discord ;
une chaîne sk-ant-… ; tout bloc de 32 caractères base64 ou hexadécimaux et plus.
"""

import re

MASQUE = "***"

_CLES = r"(?:TOKEN|SECRET|PASSWORD|PASSWD|PASS|KEY|AUTH|COOKIE|SESSION|DSN|DATABASE_URL)"

_RE_URL_MDP = re.compile(r"(\b[A-Za-z][A-Za-z0-9+.\-]*://[^\s:/@]+:)([^\s@/]+)(@)")
_RE_ENTETE = re.compile(r"(?im)\b((?:proxy-)?authorization|set-cookie|cookie)(\s*:)[^\r\n]*")
_RE_PARAM = re.compile(r"(?i)([?&](?:token|code|state)=)[^&\s#\"']*")
_RE_DISCORD = re.compile(r"(?i)(discord(?:app)?\.com/api/webhooks/)\S+")
_RE_SK = re.compile(r"sk-ant-[A-Za-z0-9_\-]*")
_RE_AFFECT = re.compile(
    r"(?i)(\b[A-Za-z0-9_.\-]*" + _CLES + r"[A-Za-z0-9_.\-]*)([\"']?\s*[=:]\s*)(\"[^\"\r\n]*\"|'[^'\r\n]*'|[^\s,;\"']+)"
)
_RE_BLOC = re.compile(r"[A-Za-z0-9+/=_\-]{32,}")


def _affect(m):
    valeur = m.group(3)
    if valeur == MASQUE:
        return m.group(0)
    if valeur[:1] in "\"'" and len(valeur) >= 2:
        return m.group(1) + m.group(2) + valeur[0] + MASQUE + valeur[-1]
    return m.group(1) + m.group(2) + MASQUE


def filtrer(texte):
    """Retourne ``texte`` avec les secrets masqués."""
    if not texte:
        return texte or ""
    t = _RE_URL_MDP.sub(lambda m: m.group(1) + MASQUE + m.group(3), texte)
    t = _RE_ENTETE.sub(lambda m: m.group(1) + m.group(2) + " " + MASQUE, t)
    t = _RE_PARAM.sub(lambda m: m.group(1) + MASQUE, t)
    t = _RE_DISCORD.sub(lambda m: m.group(1) + MASQUE, t)
    t = _RE_SK.sub(MASQUE, t)
    t = _RE_AFFECT.sub(_affect, t)
    t = _RE_BLOC.sub(MASQUE, t)
    return t
