#!/usr/bin/env python3
"""Contexte de la session au dernier tour — la mesure de la passation.

    python3 -B contexte.py [<journal.jsonl>]

Outil jetable du CdP (copié dans <Dossier>/outils_cdp/). Lit le journal de la session et
additionne, pour le dernier tour, input_tokens + cache_read_input_tokens +
cache_creation_input_tokens. C'est la taille du contexte, pas le cumul consommé depuis le
début de la session.

Le journal est celui qu'on donne en argument ; sans argument, le plus récent de
~/.claude/projects/*/*.jsonl, en écartant tout fichier sous un dossier « subagents/ ». Seules
les lignes de la session principale comptent : une ligne marquée « "isSidechain": true » (un
sous-agent) est ignorée, une ligne illisible est sautée. Sans journal ou sans ligne « usage »,
le script le dit en une ligne (sur la sortie d'erreur) et sort en code 1. Si le journal porte
une marque de compactage (« "isCompactSummary": true » ou « "subtype": "compact_boundary" »),
une seconde ligne le dit : la mesure porte sur le contexte compacté.

Python 3.11 et plus, bibliothèque standard seulement.
"""
import glob
import json
import os
import sys

CLES = ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens")


def journal_recent():
    """Le journal le plus récent de ~/.claude/projects/*/*.jsonl hors dossier « subagents/ » ; None s'il n'y en a pas."""
    candidats = [c for c in glob.glob(os.path.expanduser("~/.claude/projects/*/*.jsonl"))
                 if "subagents" not in os.path.normpath(c).split(os.sep) and os.path.isfile(c)]
    return max(candidats, key=os.path.getmtime) if candidats else None


def mesurer(chemin):
    """(dernier « usage » de la session principale ou None, compactage vu ?)."""
    usage, compactage = None, False
    with open(chemin, encoding="utf-8", errors="replace") as journal:
        for ligne in journal:
            try:
                objet = json.loads(ligne)
            except ValueError:
                continue
            if not isinstance(objet, dict) or objet.get("isSidechain") is True:
                continue
            if objet.get("isCompactSummary") is True or objet.get("subtype") == "compact_boundary":
                compactage = True
            message = objet.get("message")
            if isinstance(message, dict) and isinstance(message.get("usage"), dict) and message["usage"]:
                usage = message["usage"]
    return usage, compactage


def main(argv):
    chemin = argv[0] if argv else journal_recent()
    if not chemin:
        print("contexte : aucun journal trouvé (~/.claude/projects/*/*.jsonl)", file=sys.stderr)
        return 1
    try:
        usage, compactage = mesurer(chemin)
    except OSError as erreur:
        print(f"contexte : journal illisible ({chemin}) : {erreur.strerror or erreur}", file=sys.stderr)
        return 1
    if usage is None:
        print(f"contexte : aucune ligne usage dans {chemin}", file=sys.stderr)
        return 1
    total = sum(v for v in (usage.get(k, 0) for k in CLES) if isinstance(v, (int, float)))
    print(f"contexte au dernier tour : {total:,} jetons".replace(",", " "))
    if compactage:
        print("compactage vu : la mesure porte sur le contexte compacté")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
