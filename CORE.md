# CORE — the PL method for a project with a single PL
### 31 October 2026 · two pages that stand on their own · mode A (`GUIDE.md` §2a)

*If you start alone with a PL, read this and nothing else: the rest of the package is added when a sign you have lived
through calls for it (the table, at the end). The terms are in `GLOSSARY.md`.*

## 1 · The three roles

- **You, the owner**: you decide and validate on screen; you talk only to the PL; you create the tags and the releases
  (a session cannot). You run no command.
- **The PL** (project lead, Opus, long session): it decides with you, measures the actual state, writes the brief,
  launches the dev, accepts, closes and keeps the living docs. **It does not write the delivered code**: a missing tool
  becomes a batch.
- **The dev** (Sonnet by default): launched by the PL as a sub-agent of its session, without its context, it executes
  **one brief** and talks only to the PL, through what it pushes and through its final reply.

**The PL's posture**: it proposes numbered options with a recommendation; when it has decided without you, its reply
ends with “Decided without you: …”; a simple question gets a direct answer, without the batch circuit.

## 2 · The three layers

1. **The personal skill `methode-cdp`** (your account, all your projects): the roles, the posture, the general circuit.
2. **The project instructions** (claude.ai): your profile, where the living docs are, which repositories. Pointers, not
   rules: a rule copied here would drift.
3. **The living docs and the repositories**: the project's method, the checkpoint, the decision log, the plan,
   `workstreams.yaml` (in the living-docs repository), and the code. They change at every closed batch, by the PL alone.

**Precedence**: the project's method overrides the skill; the brief overrides the dev prompt for what the batch does;
your decisions in the decision log override everything.

## 3 · The cycle of a batch

1. **The study**: the PL measures the actual state (never the assumed one) and decides with you, in numbered options
   with a recommendation.
2. **The brief**: a single self-contained document — what the batch does, **what does not move**, the exact list of
   allowed files, criteria **as deltas against the base**, the stops. Pushed alone on the `batch/<version>` branch.
3. **The dev**: it builds, measures, delivers a commit then a report. If it hits a point that is ambiguous, impossible or
   contrary to the actual state, **it stops** (`STOP_<n>.md`) instead of deciding.
4. **The cold acceptance**: the PL re-measures on `git archive` of the delivered commit, reads the diff against the
   brief's rules, looks at the renders itself; you validate on screen.
5. **The close-out**: fast-forward merge after your validation, an entry in the decision log, the workstreams up to date,
   a “Batch closed” commit in the living docs, then the mirror in the project.

## 4 · The checkpoint and the handover

The **checkpoint** states the project's actual state in 10 KB; it is the entry point of every PL session, which reads it
first and sets its **baton** in it (“session active: <last eight characters of the session identifier>”).

**The handover is measured** (`templates/context.py`), because every turn re-reads the whole context: the bigger it is,
the more each turn costs and the more quality drops. **At 450,000 tokens**, the PL warns you at the top of its reply
and launches no new batch; **at 550,000 at the latest**, at a natural end of the queue or at the first sign of
saturation, it **hands over**: it rewrites §0 of the checkpoint, releases the baton, pushes, then gives you the **fixed
resume line** to paste into a new conversation. Every handover notes the saturation signs seen (or “none”). Nothing
travels outside the repository.

## 5 · What does not forgive

- **Nothing is believed, everything is measured**: cold, on the delivered archive, as deltas; never copied from the dev's
  report.
- **One delivery = one new number**: what is handed over or deployed to you carries a version never handed over before;
  a fix is a following batch. No version change without your agreement.
- **The dev pushes only its batch's branch**: never `main`, never a tag, never `--force`.
- **A justified stop by the dev is never a reproach**: execution is often right against the brief.
- **The project's invariants** (a file, a fingerprint) move only on your written authorization in the brief.
- **A public code repository receives only the code**: the dev prompt and the batches go to a private repository.
- **No secret in a repository**, nor production data; the PL deletes nothing without your agreement.

## 6 · The extensions: when you need one, where to read it

Each is added without migrating anything. As long as the sign has not occurred, do not install it.

| extension | when: the sign you have lived through | where |
|---|---|---|
| **Several PLs** (modes B and C) | a second module starts, or you want two subjects at the same time in two conversations | `GUIDE.md` §2a, §3a, §3b; `templates/METHOD.md` §1a |
| **The living-docs arbiter** | duplicated decision numbers, a board out of line, or a forgotten session that keeps its baton | `GUIDE.md` §2b; `templates/ARBITER.md` |
| **The orders repository** | data produced in a session must reach the server, and you do not want to drop it by hand | `GUIDE.md` §2c; `templates/SERVER_RUNNER.md` §5 |
| **The local runner** | you drive a game or an application on your PC and the Claude app's bridge does not give your machine | `templates/LOCAL_RUNNER.md`; `skill/SKILL.md` §5a |
| **The server runner and the deployment** | you administer a production server and you drop the deliverable by hand at every batch | `templates/SERVER_RUNNER.md`; `templates/METHOD.md` §4a |
| **The published board** | you no longer read `workstreams.yaml` as it is: you want to see at a glance what is to be done | `templates/METHOD.md` §6 (“The workstreams board”); `templates/make_board.py` |
| **The product sheet** | one product has several module PLs, and what is common (ritual, test bench, pitfalls) repeats in each checkpoint | `templates/METHOD.md` §1a; `skill/SKILL.md` §11 |

*To start: `GUIDE.md` §3, then `2_PL_BOOTSTRAP_PROMPT.md` §A.*
