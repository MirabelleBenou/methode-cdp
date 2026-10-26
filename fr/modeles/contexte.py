#!/usr/bin/env python3
"""Contexte de la session au dernier tour — la mesure de la passation.

    python3 -B contexte.py

Outil jetable du CdP (copié dans <Dossier>/outils_cdp/). Lit le journal de la
session (~/.claude/projects/*/*.jsonl, le plus récent) et additionne, pour le
dernier tour, input_tokens + cache_read_input_tokens + cache_creation_input_tokens.
C'est la taille du contexte, pas le cumul consommé depuis le début de la session.
"""
import glob, json, os
f = max(glob.glob(os.path.expanduser("~/.claude/projects/*/*.jsonl")), key=os.path.getmtime)
u = None
for l in open(f, encoding="utf-8"):
    try: m = json.loads(l).get("message") or {}
    except Exception: continue
    if isinstance(m, dict) and m.get("usage"): u = m["usage"]
n = sum(u.get(k, 0) for k in ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"))
print(f"contexte au dernier tour : {n:,} jetons".replace(",", " "))
