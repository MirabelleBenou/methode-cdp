#!/usr/bin/env python3
"""Session context at the last turn — the handover measure.

    python3 -B context.py [<log.jsonl>]

The PL's throwaway tool (copied into <Folder>/pl_tools/). Reads the session log and adds up,
for the last turn, input_tokens + cache_read_input_tokens + cache_creation_input_tokens. This is
the size of the context, not the total consumed since the session began.

The log is the one given as an argument; without an argument, the most recent of
~/.claude/projects/*/*.jsonl, leaving out every file under a "subagents/" folder. Only the lines
of the main session count: a line marked "isSidechain": true (a subagent) is ignored, an
unreadable line is skipped. Without a log or without a "usage" line, the script says so in one
line (on the error output) and exits with code 1. If the log carries a compaction mark
("isCompactSummary": true or "subtype": "compact_boundary"), a second line says so: the
measure is of the compacted context.

Python 3.11 and later, standard library only.
"""
import glob
import json
import os
import sys

KEYS = ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens")


def latest_log():
    """The most recent log of ~/.claude/projects/*/*.jsonl outside a "subagents/" folder; None if there is none."""
    candidates = [c for c in glob.glob(os.path.expanduser("~/.claude/projects/*/*.jsonl"))
                  if "subagents" not in os.path.normpath(c).split(os.sep) and os.path.isfile(c)]
    return max(candidates, key=os.path.getmtime) if candidates else None


def measure(path):
    """(last "usage" of the main session or None, compaction seen?)."""
    usage, compaction = None, False
    with open(path, encoding="utf-8", errors="replace") as log:
        for line in log:
            try:
                entry = json.loads(line)
            except ValueError:
                continue
            if not isinstance(entry, dict) or entry.get("isSidechain") is True:
                continue
            if entry.get("isCompactSummary") is True or entry.get("subtype") == "compact_boundary":
                compaction = True
            message = entry.get("message")
            if isinstance(message, dict) and isinstance(message.get("usage"), dict) and message["usage"]:
                usage = message["usage"]
    return usage, compaction


def main(argv):
    path = argv[0] if argv else latest_log()
    if not path:
        print("context: no log found (~/.claude/projects/*/*.jsonl)", file=sys.stderr)
        return 1
    try:
        usage, compaction = measure(path)
    except OSError as error:
        print(f"context: log unreadable ({path}): {error.strerror or error}", file=sys.stderr)
        return 1
    if usage is None:
        print(f"context: no usage line in {path}", file=sys.stderr)
        return 1
    total = sum(v for v in (usage.get(k, 0) for k in KEYS) if isinstance(v, (int, float)))
    print(f"context at the last turn: {total:,} tokens".replace(",", " "))
    if compaction:
        print("compaction seen: the measure is of the compacted context")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
