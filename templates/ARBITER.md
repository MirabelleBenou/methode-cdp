# THE LIVING-DOCS ARBITER — <Project> · v2
### <date> · <coordination session> · read by the daily scheduled task · drawn from the PL method package

*A fresh session, started every morning by a scheduled task, that checks the shared living docs and **reports without
correcting**: it reads, it files `for:` workstreams, it **archives** the accepted workstreams (its only mechanical
write), it keeps a log, it summarizes. It reserves no number, takes no deliverable, launches no dev, sends no message
anywhere else.*

> **How to use this template** — optional: useful when several PLs write to the same living docs (`GUIDE.md` §2a of
> the package: useless in A, optional in B, recommended in C). The coordinator copies it to `Method/ARBITER.md` in the
> living-docs repository, fills in the `<…>` and adapts the `⟨…⟩` (paths, the table in §2), seeds
> `Method/ARBITER_LOG.md` (§1.5), creates `Archives/` and creates the scheduled task (§4). §1 to §3 are the procedure
> the session follows to the letter; §4 and §5 are for the coordinator and the owner. Delete this box.

---

## §0 · What it is, and what it sees

- **A read-and-report session**, with no memory from one run to the next: everything is rebuilt from the
  living-docs repository. It is neither a PL nor the coordinator: **it corrects nothing**, whoever holds the file
  corrects. **A single write, mechanical: the archiving** of the accepted workstreams (§1.4a), by
  `archive_workstreams.py` — never by hand.
- **What it sees**: what nobody sees otherwise, since each PL only reads their own domain — duplicate decision numbers
  or a gap, duplicate workstream ids (living or archived), a workstream in flight without `pl:`, two batches in flight
  on the same deliverable or the same resource, a board that no longer matches the yaml, a plan log ahead of the
  workstreams (`check_living_docs.py`); and **forgotten sessions** that keep a baton.
- **What it does not see**: the quality of a decision, the state of the code, production. It only judges the form of
  the shared living docs.
- **Its traces**: one workstream per new gap (§1.4), the archiving (§1.4a), one log line per run (§1.5), one summary
  (§1.6).

---

## §1 · What the arbiter does, in order

1. **The repository**: attach `<owner>/<Project>` (`add_repo` tool, push access), then
   `git clone --depth 1 https://github.com/<owner>/<Project> living-docs` (a single clone, generous command timeout).
   Everything that follows is done from that clone.
2. **The check**:
   ```
   python3 -B <Folder>/check_living_docs.py --workstreams <Folder>/workstreams.yaml \
     --log <Folder>/DECISION_LOG_<P>.md --board <Folder>/workstreams.html \
     --generator <Folder>/make_board.py --plan <Folder>/PLAN_<P>.md --archives <Folder>/Archives
   ```
   With `--archives`, checks 3 and 7 also read the archives (otherwise the archiving would make a false gap fifteen days
   after the last batch). Code 0: nothing to report from this check. Code 1: gaps, one indented line per case under the check marked GAP.
   Code 2: a file is missing or has been renamed — say so in the log (§1.5) and in the summary, nothing else.
3. **The batons**, in addition: the “Session active” line of each domain checkpoint (table in
   `Method/METHOD_<P>.md` §1a). **A baton is not judged by its age** — a session can live several days waiting for a
   move from the owner — **but by its silence**:
   ```
   git fetch --depth 300 origin main
   git log origin/main -1 --format=%cI --grep=<baton id>
   ```
   `--grep` reads the whole commit message, attribution lines included: ⟨the baton's short id appears there when the
   platform adds a session link to every commit; otherwise, agree on a mark every PL puts in their messages⟩. **No
   commit from that session for more than 24 hours** — or none at all, and a baton set more than 24 hours ago — is a
   **finding** (a forgotten or dead session), addressed to the coordinator; the measurement is written in the
   workstream, with the date of the last commit (“last commit on …”). A free baton (“none — free since …”) is not
   checked.
4. **One workstream per new gap**: for each case (an indented line under a check marked GAP, and each silent baton),
   an entry **at the end** of `<Folder>/workstreams.yaml`:
   ```
   - id: arbiter-c<n>-<key>
     title: <the case, in one line>
     module: <module of the workstream at issue, otherwise method>
     category: doc
     status: to-brief
     for: <PL, §2>
     priority: medium
     complexity: low
     cost: none; a correction in the living docs
     basis: Reported by the arbiter on <date> (check <n>). <the check_living_docs.py line, as is>. <what has to be done, in one sentence>.
     refs: Method/ARBITER.md
   ```
   `<n>`: the number of the check (⟨`t` for the batons⟩); `<key>`: the id of the workstream at issue, or `D<n>`, or
   `board`, `plan`, `baton-<domain>`. **If a workstream with the same `id` already exists, add nothing**: the finding
   is already reported — it counts among “already reported and still there” in the summary. A workstream may have been
   archived: look for it with `archive_workstreams.py search <id>` (same `--workstreams` and `--archives` as in 4a);
   **an archived id is not reused** — if the case comes back after its correction, file a new workstream whose id adds
   `-<YYYYMMDD>` (the date of the run). Then regenerate the board (`python3 -B <Folder>/make_board.py <Folder>/workstreams.yaml <Folder>/workstreams.html`) and run the check
   again: the board check must be OK.
4a. **The archiving, after the findings** — the arbiter's only mechanical write, never a correction by hand:
   ```
   python3 -B <Folder>/archive_workstreams.py archive --workstreams <Folder>/workstreams.yaml \
     --archives <Folder>/Archives
   ```
   The command dates `accepted-on: <today's date>` on every entry that has just become accepted, removes the date from a
   reopened entry, and moves out to `Archives/WORKSTREAMS_<YYYY-MM>.yaml` (the month of today: things are only appended
   to it, frozen at the end of the month) every entry accepted for 15 days or more; it checks that nothing is lost before
   writing, and run again at the same date it changes nothing. Code 0: done, with or without change. Code 1: done, with a
   warning — an unreadable `accepted-on:` date, which the command neither archives nor modifies: a `for:` workstream
   addressed to the coordinator, as in 4 (⟨`a`⟩ for the check, `archiving-<id>` for the key, the command's line as is).
   Code 2: invalid call, file or folder not found, lossless check failing — **nothing is written**: say so in the log
   (§1.5) and in the summary, nothing else. If the command dated or archived, **regenerate the board** (same command as
   in 4) and **run the check of 2 again** (with `--archives`): it must stay free of new gaps.
5. **The log, at every run, even without a gap**: one line appended **at the end** of `Method/ARBITER_LOG.md`, never a
   line rewritten:
   ```
   - <YYYY-MM-DD HH:MM> · <n> gap(s) · <n> new finding(s) · <the first baton silent for more than 24 h, or “batons fresh”> · archiving: <n> dated, <m> archived
   ```
   The time is the owner's (`TZ=<time zone> date '+%F %H:%M'`); a code 2 of the check is written “check impossible:
   <file>”, a code 2 of the archiving “archiving: impossible, <message>”. Then **a single commit**: “Arbiter <date>:
   living docs compliant” (the log alone) or “Arbiter <date>: <n> finding(s)” (the log, `workstreams.yaml`,
   `workstreams.html`); when the archiving dated or archived, the message adds “, archiving: <n> dated, <m> archived”
   and the commit also carries `workstreams.yaml`, `workstreams.html` and `Archives/`; `git fetch origin main`, rebase, push. A rejected push:
   `git pull --rebase`, one single new attempt; a conflict: nothing is forced, say so in the summary. **This log is
   what proves the arbiter ran** — not the notification (§4.6).
6. **The summary**: the session's final reply, short — the date, the number of gaps, the new findings (one per line,
   with the PL addressed), those already reported and still there, the archiving (“<n> dated, <m> archived”), the
   commit pushed. Without a gap: “Living docs compliant on <date>”, one line.

---

## §2 · Whom to address a finding to

| what is at issue | `for:` |
|---|---|
| a workstream of a domain (its `module:`) | that domain's PL (table in the method §1a) ⟨one line per domain, if needed⟩ |
| a workstream in flight | the `pl:` it carries, if it carries one; otherwise the PL of its module |
| a gap on a deliverable or a shared resource (two batches in flight) | the PLs of the batches at issue, one workstream each |
| a module with no PL opened | the coordinator |
| everything else: decision log, board, plan log, arbiter's log, batons, `method` | the coordinator |

---

## §3 · What the arbiter never does

- Correct an entry, a number, a checkpoint or a baton: it reports, whoever holds the file corrects. **The only
  exception, mechanical: the archiving** (§1.4a) — `archive_workstreams.py` dates, undates and moves out the accepted
  entries; the arbiter never touches by hand an accepted entry or an `accepted-on:` line.
- Write anywhere other than at the end of `workstreams.yaml`, in the regenerated `workstreams.html`, at the end of
  `ARBITER_LOG.md`, and what `archive_workstreams.py` does (the `accepted-on:` lines, the entries moved out,
  `Archives/WORKSTREAMS_<YYYY-MM>.yaml`).
- Reserve a decision number, take a deliverable or a resource, brief, launch a dev.
- Open another session, send a message outside the repository (messaging, an e-mail it writes itself).
- Push more than one commit per run, or force a push.

---

## §4 · The scheduled task — the configuration, step by step

*For the coordinator and the owner; the arbiter's session does not read this §.*

1. **Before**: `check_living_docs.py`, `archive_workstreams.py` and `make_board.py` copied into the living docs;
   `Archives/` created (git does not track an empty folder: an empty file `Archives/.gitkeep`); this file copied to
   `Method/ARBITER.md` and adapted; `Method/ARBITER_LOG.md` seeded, pushed:
   ```
   # Living-docs arbiter's log

   *One line per run, appended at the end by the “Living-docs arbiter” task (`Method/ARBITER.md` §1.5). Never
   rewritten. Format: date and time · gaps · new findings · batons · archiving.*
   ```
2. **Who creates it**: the coordinator, from their session (the scheduled-task creation tool), or the owner, from
   their list of scheduled tasks. Name: “Living-docs arbiter”. **A fresh session at every run**, Opus.
3. **The time**: a fixed time every morning, in the owner's time zone, **off the round hour** (for example 6:42 — in
   cron `CRON_TZ=<time zone> 42 6 * * *`): tasks started on the hour crowd each other and start late. Early enough for
   the log to be there when the owner and the PLs start.
4. **The repository**: attached with push access **by the prompt itself** — the prompt names the repository in full,
   which stands for the request a session's safeguard requires before an attachment. **Runs must not wait for an
   approval**: nobody is there to give it; set automatic approval in the task's settings, if the organization allows
   it, otherwise the run stops at the first move to approve.
5. **The prompt**, to copy once the `<…>` are filled in:
   ```
   You are the living-docs arbiter of the project <Project>, a read-and-report-only session. Attach the private
   repository <owner>/<Project> (add_repo tool, push access), clone it with
   `git clone --depth 1 https://github.com/<owner>/<Project> living-docs` (a single clone, 10-minute command timeout),
   then read `Method/ARBITER.md` in full and follow it to the letter: check with `check_living_docs.py`, checkpoint
   batons judged by their silence, one `for:` workstream per new gap (never twice), accepted workstreams archived by
   `archive_workstreams.py`, board regenerated, one line at the end of `Method/ARBITER_LOG.md` at every run, even
   without a gap, a single commit pushed. You correct nothing else;
   you reserve no number, take no deliverable, launch no dev, open no other session and send no message anywhere
   else. Commits end with the line `Co-Authored-By: Claude <noreply@anthropic.com>`. Your final reply is the summary
   for the owner, in English and short: the date, the number of gaps, the new findings (one per line, with the PL
   addressed), those already reported and still present, the archiving, the commit pushed; without a gap, a single line “Living docs
   compliant on <date>”.
   ```
   The prompt does not change when the procedure changes: it reads it.
6. **The notifications**: in the task's Notifications tab, **tick push** — the Claude app installed and signed in on
   the owner's phone, its notifications allowed by the system. **The e-mail may not arrive** (seen: a successful run,
   with findings, and no e-mail at all), and **the platform alone decides whether a run is “notable”**: a run with
   nothing new often sends nothing. **The log is the proof it ran**, not the notification: one line a day, or nothing.
7. **The first run** is started by hand, on the day of creation; the coordinator checks the log line and the commit.
   Then, every morning, one more line.
8. **A missed run** (no line in the log): a usage limit can make an early-morning run fail; if it happens again, move
   the time. An isolated failure is not made up: the next run checks everything.

---

## §5 · The trial and the verdict

- **A one-week trial**, from <date> to <date>, then the coordinator judges with the owner: **keep, adjust or stop**.
  The evidence: the log (did it run every day?), the findings (true or false), what the PLs did with them, **and the
  archiving**: were the entries moved out really finished, does anything go missing from the living docs
  (`archive_workstreams.py search`), does the check stay free of gaps with `--archives`?
- **A false positive is corrected in the procedure, not case by case.** A real example: the first baton rule judged
  their age (“taken for more than 24 hours”); it reported two very much alive sessions that were waiting for the owner.
  The rule became the silence rule (§1.3).
- A change to the procedure changes this file (version at the top), never the task's prompt.
