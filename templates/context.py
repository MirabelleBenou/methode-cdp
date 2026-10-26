#!/usr/bin/env python3
"""Session context at the last turn — the handover measure.

    python3 -B context.py

The PL's throwaway tool (copied into <Folder>/pl_tools/). Reads the session
log (~/.claude/projects/*/*.jsonl, the most recent one) and adds up, for the
last turn, input_tokens + cache_read_input_tokens + cache_creation_input_tokens.
This is the size of the context, not the total consumed since the session began.
"""
import glob, json, os
f = max(glob.glob(os.path.expanduser("~/.claude/projects/*/*.jsonl")), key=os.path.getmtime)
u = None
for l in open(f, encoding="utf-8"):
    try: m = json.loads(l).get("message") or {}
    except Exception: continue
    if isinstance(m, dict) and m.get("usage"): u = m["usage"]
n = sum(u.get(k, 0) for k in ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"))
print(f"context at the last turn: {n:,} tokens".replace(",", " "))
