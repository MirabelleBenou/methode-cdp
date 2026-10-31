# THE LIVING-DOCS ARBITER — <Project> · v6
### <date> · <coordination session> · drawn from the PL method package v19

***The arbiter is a GitHub Action**, `.github/workflows/arbiter.yml`: every day, with no session, it runs
`<Folder>/arbiter.py`, commits and pushes as `github-actions[bot]`, then **fails if it has filed a new workstream** — it is
GitHub's e-mail that warns the owner; its summary is on the run's page. It measures, it does not judge: **judging the
documents is the controller's job** ([CONTROLLER.md](CONTROLLER.md)). This document says what the script does, in order;
it is not executed, it is read.*

> **How to use the template** — optional: useful when several PLs write the same living docs ([GUIDE.md](../GUIDE.md) §2b:
> useless in A, optional in B, recommended in C). The coordinator copies it to `Method/ARBITER.md` of the living-docs
> repository, fills in the `<…>` and adapts the `⟨…⟩` (the table of §2), then does the installation of §4. When copying, the links to the package become plain text. Delete this box.

---

## §0 · The arbiter in nine questions

*For the human reader; adds no rule to §1.*

1. **What is it?** A script, run every day by a scheduled action. With several PLs, each reads only its domain and
   **nobody sees the whole** of the shared living docs (decision log, `workstreams.yaml`, board, plan log, one checkpoint
   per domain): it is the missing eye. No memory from one run to the next, no model token, no secret.
2. **Why?** The same accidents come back, invisible from a single domain: two sessions take the same decision number
   (check 1); a workstream stays in flight with no PL, or two batches aim at the same deliverable (5 and 8); the
   published board no longer follows the yaml (6); a forgotten session keeps its baton; the workstreams file swells
   (archiving); a checkpoint queue announces a finished workstream as to do (9); a checkpoint passes its cap (10); a `.yaml`
   is no longer valid YAML (11). A script has no stake in a domain, runs when nobody is writing, and leaves a dated trace
   even when all is well.
3. **When do I need it?** Mode A: never. Mode B: at the first gap or when the living docs grow. Mode C: as soon as
   several PLs write the same living docs on the same day. The sign: the first duplicated decision number, or the first
   forgotten session that keeps a baton.
4. **What does it do?** It normalizes, checks, files one workstream per new gap, judges the batons, archives, regenerates
   the board, writes a line to its log, summarizes (§1).
5. **What does it never do?** Correct, decide, write anywhere but in its workstreams, its log and the archiving (§3).
6. **How is it installed?** Copy the script and its workflow, write the domain table, seed the log, run a first run (§4).
7. **What it costs**: a minute of machine a day, one commit a day at most; nothing to the owner but the e-mail of a
   failure; to the PLs, reading after each `pull` the `for:` workstreams aimed at them.
8. **How to read what it produces?** The log, one line per run, even without a gap — **it is the proof it ran**: date
   and time · gaps · new findings · batons · archiving · checkpoints · footprint (method, sheet and checkpoints, in KB;
   it must go down or stabilize). A finding is a `to-brief` workstream, `for:` its owner, with the id `arbiter-c<n>-<key>`.
9. **How to judge whether to keep it?** After a week: does the log have a line per day, were the findings true, did the
   PLs do something with them, did the archiving lose nothing? **A false positive is fixed in the script, not case by
   case.**

---

## §1 · What the script does, in order

1. **Normalize**: `archive_workstreams.py normalize` puts in double quotes only the values a YAML reader would misread
   (strict format, check 11); it changes no value read.
2. **Check**: `check_living_docs.py` with `--archives` and `--domains` (eleven checks; 9 cross-checks each checkpoint's queue
   with `workstreams.yaml`, 10 measures their size against the cap of the method §6, 11 the format). A missing file: code 2, nothing is
   written, the log says “check impossible: <file>”.
3. **File one workstream per new gap**, at the end of `workstreams.yaml`, in strict format: id `arbiter-c<n>-<key>` (`<n>`
   the check, `<key>` the workstream concerned, `D<n>`, `board`, `log`). **Never twice**: a living workstream with the
   same id is enough; an archived id is not reused (add `-<YYYYMMDD>`). **Check 9 and check 10, one workstream per
   domain** (`arbiter-c9-checkpoint-<domain>-<date>`, `arbiter-c10-short-checkpoint-<domain>-<date>`), not filed again while
   an open workstream of the same name awaits its PL; **a fault of the table itself**: a single workstream
   `arbiter-c9-table-<date>`, for the coordinator.
4. **The batons**: the “Session active” line of each checkpoint. **A baton is judged not by its age but by its silence**:
   no commit carrying its identifier for more than 24 hours. ⟨The baton is the last eight characters of the session
   identifier in the commits' attribution lines; without that line, agree on a mark that each PL puts in its messages.⟩
   It is **information** (log, summary), never a workstream. **The coordination is excluded**: a long consultation
   session, silent for days without being forgotten.
5. **The late checkpoint**: a workstream of the domain that became accepted after the last commit of its checkpoint joins
   that domain's check-9 workstream.
6. **Archive**: `archive_workstreams.py archive` dates `accepted-on:` and moves to `<Folder>/Archives/WORKSTREAMS_<YYYY-MM>.yaml` the
   workstreams accepted for the delay of the method §6 (the script's default: do not pass `--delay`); it checks that it loses no line. An unreadable
   date: an `archiving-<id>` workstream. Code 2: nothing is written.
7. **Regenerate** the board if `workstreams.yaml` changed, then check again.
8. **The log**, at the end of `Method/ARBITER_LOG.md`, never a line rewritten:
   ```
   - <YYYY-MM-DD HH:MM> · <n> gap(s) · <n> new finding(s) · <first silent baton, or “batons fresh”> · archiving: <n> dated, <m> archived · checkpoints: <domains reported, or “up to date”> · footprint: <n> KB
   ```
9. **The summary and the exit code**: the summary (date, gaps, new findings with the PL aimed at, those already reported,
   the commit) goes to the run's page; the last line, `Commit: <message>`, is the message of the single commit the workflow
   pushes (`git pull --rebase`, a single new attempt, never a force). **Code 0**: nothing new; **1**: at least one
   workstream filed; **2**: a file is missing or a script fails. The workflow fails on 1 and 2.

## §2 · Whom to address a finding to

| what is concerned | `for:` |
|---|---|
| a workstream of a domain (its `module:`) | the PL of that domain (method table §1a) ⟨one line per domain, if needed⟩ |
| a workstream in flight | the `pl:` it carries |
| two batches in flight on one deliverable or resource | the PLs of the batches concerned, one workstream each |
| the lag (check 9) or the size (check 10) of a checkpoint | the `pl` of the domain in `Method/domains.yaml` |
| everything else: decision log, board, logs, domain table, `method` | the coordinator (the table entry whose `pl` contains “Coordination”) |

## §3 · What the arbiter never does

- Correct an entry, a number, a checkpoint, a baton or the table: it reports, the owner corrects. The only mechanical
  writes: archiving and normalizing (`archive_workstreams.py`), never by hand.
- Write anywhere but at the end of `workstreams.yaml`, in the regenerated board, at the end of the log and in `<Folder>/Archives/`.
- Judge a document (contradiction, duplicate, history, style): that is the controller's job.
- Reserve a decision number, take a deliverable, launch a dev, open a session, send a message.
- Push more than one commit per run, or force a push.

## §4 · The installation, step by step

*For the coordinator and the owner.*

1. **Copy** into `<Folder>/` (the living-docs folder, the one of `workstreams.yaml`) `arbiter.py`, `check_living_docs.py`, `archive_workstreams.py` and `make_board.py`
   (package templates: the arbiter finds the other three next to it); create `<Folder>/Archives/` (a `.gitkeep`).
2. **Write the domain table** `Method/domains.yaml` (template `templates/domains.yaml`): one entry per PL, the coordination
   included; **each checkpoint** has its `## §<n> · The queue` section (template [`templates/CHECKPOINT.md`](CHECKPOINT.md)), which `file:`
   names. The coordinator keeps it: at each domain opened, closed, or section renamed.
3. **Seed** `Method/ARBITER_LOG.md` (a title and a line of explanation), copy this file to `Method/ARBITER.md`.
4. **Copy the workflow** `templates/living-docs-repo/arbiter.yml` to `.github/workflows/arbiter.yml` of the living-docs
   repository and adapt only the `env:` block (the paths). It runs every day at 5:42 UTC, or by hand (“Run workflow”), with
   the sole right to write to the repository (`contents: write`). **On a free account** (branch rules:
   `3_GITHUB.md` §5), the action pushes to the default branch, with no rule to get around.
5. **Warn the PLs** that they will receive `for:` workstreams from the arbiter. **The first run is chatty** on an advanced
   project: every open workstream that the checkpoints do not yet cite falls at once (one workstream per domain); after
   that, only what is new.
6. **Run the first run by hand** (Actions tab); check the log line and the commit “Arbiter <date>: …”.
7. **GitHub's e-mails**: the owner leaves active the notifications of a failed workflow. **The failure is the signal**; the
   log is authoritative, not the e-mail. A missed run (no line) is not made up: the next one checks everything.

| gesture | who | when |
|---|---|---|
| copy the scripts, `<Folder>/Archives/`, the workflow; write the domain table | coordinator | before |
| give each checkpoint its queue section, each subject cited by its id | each PL | before the first run, then at each resumption |
| run the first run; read the log and the commit | coordinator | day 1 |
| read the `for:` workstreams after each `pull`; correct | each PL | continuously |
| keep the domain table | coordinator | at each change |

## §5 · The trial and the judgment

A week, then the coordinator judges with the owner: **keep, tune or stop**. They look at the log (a line per day), the
truth of the findings, what the PLs did with them, the archiving (nothing is missing: `archive_workstreams.py search`),
check 9 falling to “up to date” once the queues are back in step. The decision is written to the decision log.
