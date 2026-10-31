# THE LIVING-DOCS ARBITER — <Project> · v4
### <date> · <coordination session> · read by the daily scheduled task · drawn from the PL method package

*A fresh session, started every morning by a scheduled task, that checks the shared living docs **and the checkpoints**
and **reports without correcting**: it reads, it files `for:` workstreams, it **archives** the accepted workstreams (its
only mechanical write), on Mondays it re-reads the checkpoints against the week's decisions, it keeps a log, it
summarizes. It reserves no number, takes no deliverable, launches no dev, sends no message anywhere else.*

> **How to use this template** — optional: useful when several PLs write to the same living docs (`GUIDE.md` §2a and
> §2b of the package: useless in A, optional in B, recommended in C). The coordinator copies it to `Method/ARBITER.md`
> in the living-docs repository, fills in the `<…>` and adapts the `⟨…⟩` (paths, the table in §2), creates the domain
> table `Method/domains.yaml` (template `templates/domains.yaml`), seeds `Method/ARBITER_LOG.md` (§1.5), creates
> `Archives/` and creates the scheduled task (§4). §0 explains to a reader new to the method what the arbiter is and
> why; §1 to §3 are the procedure the session follows to the letter; §4 and §5 are for the coordinator and the owner.
> Delete this box.

---

## §0 · The arbiter in nine questions

*For the human reader — the owner, the coordinator, a PL. The scheduled task's session may skip this §, which adds no
rule to the procedure of §1 to §3.*

### 0.1 · What is it?

When several project leads (PLs) work at the same time, they write to the same **shared living docs**: the decision
log, `workstreams.yaml` (the list of everything to do, in progress or done) and the page regenerated from it, the plan's
log, and one checkpoint per domain (the current state, entry point of the next session). Each PL only reads their own
domain: **nobody sees the whole**. The arbiter is the missing eye.

It is **a read-and-report session**, started every morning by a scheduled task, with no memory from one run to the
next: everything is rebuilt from the living-docs repository. It is neither a PL nor the coordinator: **it corrects
nothing**, whoever holds the file corrects. A single write, mechanical: the archiving of the accepted workstreams
(§1.4a), by `archive_workstreams.py` — never by hand.

- **What it sees**: duplicate decision numbers or a gap, duplicate workstream ids (living or archived), a workstream in
  flight without `pl:`, two batches in flight on the same deliverable or the same resource, a board that no longer
  matches the yaml, a plan log ahead of the workstreams (`check_living_docs.py`, checks 1 to 8); **a checkpoint that
  lags behind the workstreams** (check 9, and the Monday reading); **a checkpoint that is too big** (check 10);
  **forgotten sessions** that keep a baton.
- **What it does not see**: the quality of a decision, the state of the code, production. It only judges the form of
  the shared living docs.

### 0.2 · Why does it exist?

Because, with several PLs, the same accidents come back, and each one is invisible from a single domain. These are real
cases, on the first project run this way:

1. **Two sessions took the same decision number.** Each had chosen it before its `pull`; git sees no conflict between
   two distinct lines carrying the same number. Three times in two days. → check 1.
2. **Counters kept by hand drifted** from one entry to the next. → what is computed is not written (method §1a); check 1 verifies the sequence of numbers.
3. **A workstream stayed in flight with no declared project lead**, and two batches were ready to start on **the same
   deliverable**. → checks 5 and 8.
4. **The published workstreams board no longer matched the file**: the yaml had changed, the page had not, and the page
   is what the owner reads. → check 6.
5. **Forgotten sessions kept a baton** and blocked the resumption of a domain. The first rule judged the baton's age: it
   reported two very much alive sessions, which were only waiting for a move from the owner. It became the *silence*
   rule: no commit from the session for 24 hours. → §1.3.
6. **The workstreams file grew without end** (169 KB, then nearly 200 KB, three quarters of it finished workstreams).
   → the automatic archiving, §1.4a.
7. **Checkpoints fell behind the workstreams.** Ten subjects existed only in checkpoints — which the owner does not
   read —, among them a feature announced “for later” and never registered; other queues announced as to do
   workstreams that were already finished. → the rule “a checkpoint's queue carries only registered workstreams”
   (method §6), check 9 and the Monday reading. Check 9 itself had its blind spots: two domains escaped it, one whose queue
   section only carried a pointer (“everything is in §0”), the other which declared none (empty `queue:`). → the
   `## §<n> · The queue` section that carries the list itself, and the empty `queue:` made a gap of the domain.
8. **The living docs grew back within days**: a workstreams file went from 95 to 146 KB in one day, a decision log
   reached 206 KB, a checkpoint 47 KB — the messages between PLs piled up in the entries, and every PL re-reads everything
   at every resume. → the caps (method §6), the archiving after seven days, check 10.

**Why a fresh, scheduled session, rather than a PL taking it on**: it has **no stake in any domain**, so no reason to
play a gap down; it runs **when nobody is working**, so no write conflict; it leaves **a dated trace even when all is
well**, so its silence is not mistaken for a breakdown; it **corrects nothing**, so it cannot make an error worse —
whoever holds the file corrects.

### 0.3 · When do I need it?

| mode (`GUIDE.md` §2a) | arbiter | why |
|---|---|---|
| **A** — one project, one PL | **useless** | a single PL writes, and sees what they write; no domain table to keep |
| **B** — independent modules, one PL each | **optional** | useful if the shared living docs grow, or from the first gap (a duplicate number, a board out of step); the domain table then has one domain per module |
| **C** — linked modules, a coordinator | **recommended** | as soon as several PLs write the same living docs on the same day: that is where the eight cases above happen |

The sign that it is time: the first duplicate decision number, or the first forgotten session that keeps a baton.

### 0.4 · What does it do every morning, and on Mondays?

**Every morning** (the detail is in §1):
1. it clones the living docs;
2. it runs `check_living_docs.py` with `--archives` **and `--domains`**: ten checks, including check 9 on the
   checkpoints and check 10, their size;
3. it judges the batons by their silence;
4. it files **one `for:` workstream per new gap** — except check 9, **grouped into a single workstream per domain**
   (check 10 has one line per domain, so one workstream per domain too);
5. it archives the workstreams accepted for seven days;
6. it adds a line to the log, even without a gap;
7. it pushes a single commit and summarizes.

**On Mondays**, in addition (§1.4b): it reads each checkpoint in full, against the decisions of the last seven days and
the domain's workstreams, and **flags only what a decision or a workstream contradicts**, quoting the sentence and the
evidence, with no opinion. One `arbiter-reading-<domain>-<YYYYMMDD>` workstream per domain flagged.

### 0.5 · What does it never do?

**It corrects nothing, decides nothing and writes nowhere other than in its log, its `for:` workstreams and the
archiving** (full list in §3).

### 0.6 · How do I set it up, step by step, and who does what?

Five moves, all in §4 (the “who does what” table is in §4.9):
1. **the coordinator** copies the three scripts, `Archives/` and this file into the living docs;
2. **the coordinator** writes the domain table (`Method/domains.yaml`) and checks that every checkpoint has its queue
   section; **each PL** keeps their queue in step;
3. **the coordinator** seeds the log and pushes;
4. **the coordinator or the owner** creates the scheduled task (off-the-hour time, prompt, push); **the owner** installs
   the mobile app and allows its notifications;
5. **the coordinator** starts the first run by hand and reads the log line and the commit.

### 0.7 · What does it cost?

- **For the machine**: a run lasts **one to two minutes**; it pushes **one commit a day** (the log, and
  `workstreams.yaml`, the board or `Archives/` when there are findings or archiving); the Monday reading costs
  **a few tens of thousands of tokens more**.
- **For the owner**: nothing day to day. One log line a day, to skim if you wish. To receive the push: the Claude app on
  the phone, its notifications allowed.
- **For the PLs**: what they already do — read, after every `pull`, the `for:` workstreams addressed to them — and keep
  their queue in step with the workstreams (once, at the first run, if they were behind).
- **For the coordinator**: the set-up, once; the domain table to keep (one line per domain); the verdict after a week.

### 0.8 · How do I read what it produces?

- **The log** (`Method/ARBITER_LOG.md`): one line per run, even without a gap — **it is the proof it ran**. A line is
  read field by field:
  ```
  - 2026-11-02 06:42 · 1 gap(s) · 2 new finding(s) · batons fresh · archiving: 0 dated, 3 archived · checkpoints: <domain-1> · reading: <domain-2>
  ```
  the date and time of the run; the number of checks in gap; the number of workstreams filed that day; the first silent
  baton (or “batons fresh”); the archiving; the domains reported by checks 9 and 10 (“up to date” when there is none); and **on
  Mondays only**, the domains flagged by the reading (“nothing” otherwise). A day without a gap:
  `… · 0 gap(s) · 0 new finding(s) · batons fresh · archiving: 0 dated, 0 archived · checkpoints: up to date`.
- **The summary**: the session's final reply, visible in the scheduled task's session. Without a gap, one line: “Living
  docs compliant on <date>”.
- **The workstreams**: a finding is a `status: to-brief` workstream, `for:` the PL concerned (or the coordinator), with a
  recognizable id — `arbiter-c<n>-<key>` (check `<n>`), `arbiter-c9-checkpoint-<domain>-<date>` (a checkpoint lagging,
  a single one per domain), `arbiter-c10-short-checkpoint-<domain>-<date>` (a checkpoint beyond 10 KB, a single one per
  domain), `arbiter-reading-<domain>-<date>` (the Monday reading). They show up on the board
  (`workstreams.html`); the PL addressed reads them after their `pull`, corrects, moves the workstream to accepted; it
  moves out to `Archives/` seven days later.
- **The notifications**: the push only arrives if the platform judges the run “notable”; **no notification does not mean
  no run** — the log is authoritative (§4.6).

### 0.9 · How do I judge whether to keep it?

After a one-week trial (which includes at least one Monday), the coordinator and the owner choose: **keep**, **adjust** or
**stop** (§5). Look at whether the log has a line every day, whether the findings were true, whether the PLs did something
with them, whether the archiving lost nothing, and whether check 9 falls to “up to date” once the checkpoints are back in
step. **A false positive is corrected in the procedure, not case by case.**

---

## §1 · What the arbiter does, in order

1. **The repository**: attach `<owner>/<Project>` (`add_repo` tool, push access), then
   `git clone --depth 1 https://github.com/<owner>/<Project> living-docs` (a single clone, generous command timeout).
   Everything that follows is done from that clone, from its root.
2. **The check**:
   ```
   python3 -B <Folder>/check_living_docs.py --workstreams <Folder>/workstreams.yaml \
     --log <Folder>/DECISION_LOG_<P>.md --board <Folder>/workstreams.html \
     --generator <Folder>/make_board.py --plan <Folder>/PLAN_<P>.md --archives <Folder>/Archives \
     --domains Method/domains.yaml
   ```
   With `--archives`, checks 3 and 7 also read the archives (otherwise the archiving would make a false gap seven days
   after the last batch). With `--domains`, **check 9 “checkpoints”** reads the domain table: for each domain, it opens
   the checkpoint, takes its queue section and cross-checks it with `workstreams.yaml`. Two gaps: **9b**, the queue
   cites a closed workstream (accepted or archived); **9c**, an open workstream of the domain (upcoming, to brief, debt,
   in flight — except `for:` messages) that the checkpoint does not cite between backticks. An empty `queue:` in the table is
   also a gap **of the domain** (“no queue section declared”): the PL gives its checkpoint its `## §<n> · The queue`
   section and the `queue:` line that names it. A fault in the table itself
   (checkpoint or queue section not found, entry with no domain or no checkpoint) is also a gap. **Check 10** measures the
   size of each checkpoint: beyond 10,240 bytes (the default cap, `--checkpoint-cap`), a line “<domain>: <path> weighs <n>
   bytes, cap <p>”. The table's paths are read from the root of the clone: run from elsewhere, add `--root <the clone>`.
   Code 0: nothing to report from this check. Code 1: gaps, one indented line per case under the check marked GAP.
   Code 2: a file is missing or has been renamed — say so in the log (§1.5) and in the summary, nothing else.
3. **The batons**, in addition: the “Session active” line of each domain checkpoint (table in
   `Method/METHOD_<P>.md` §1a). **A baton is not judged by its age** — a session can live several days waiting for a
   move from the owner — **but by its silence**:
   ```
   git fetch --depth 300 origin main
   git log origin/main -1 --format=%cI --grep=<baton id>
   ```
   `--grep` reads the whole commit message, attribution lines included: ⟨**the baton is the last eight characters of the
   session's identifier** — the one in the session attribution line of its commits, when the platform adds one to every
   commit; look for **that whole sequence, never the beginning** of the identifier, which all the sessions of one account
   share; with no attribution line, agree on a mark every PL puts in their messages⟩. **No
   commit from that session for more than 24 hours** — or none at all, and a baton set more than 24 hours ago — is a
   **finding** (a forgotten or dead session), addressed to the coordinator; the measurement is written in the
   workstream, with the date of the last commit (“last commit on …”). A free baton (“none — free since …”) is not
   checked.
4. **One workstream per new gap**: for each case (an indented line under a check marked GAP — **except check 9, grouped
   below, and check 10, which has its own id** — and each silent baton), an entry **at the end** of `<Folder>/workstreams.yaml`:
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
   `-<YYYYMMDD>` (the date of the run).

   **Check 9, grouped by domain**: its lines do not make one workstream each. For each domain that has at least one line,
   **a single** workstream `arbiter-c9-checkpoint-<domain>-<YYYYMMDD>`, `for:` the `pl` of the domain in
   `Method/domains.yaml`, module `method`, title “The <domain> checkpoint lags behind its workstreams”, the `basis`
   carrying **all** the domain's lines as they are (put end to end on the same line, separated by “; ”), then “cite every
   open workstream of your domain by its id in your checkpoint, remove the closed workstreams from your queue (method
   §6)”. **If a workstream `arbiter-c9-checkpoint-<domain>-*` already exists without being accepted, add nothing** for
   that domain: the PL has not resumed yet. **A fault of the table itself** — checkpoint not found, queue section not
   found, entry with no domain or no checkpoint — does not go to the PL: the table belongs to the coordinator. All such
   lines make **a single** workstream `arbiter-c9-table-<YYYYMMDD>`, `for:` the coordinator, never filed again while an
   `arbiter-c9-table-*` is open (the PL may have renamed the checkpoint or its section: the coordinator aligns the table,
   or asks the PL to return to the agreed title).

   **Check 10, one workstream per domain**: for each line “<domain>: <path> weighs <n> bytes, cap <p>”, a workstream
   `arbiter-c10-short-checkpoint-<domain>-<YYYYMMDD>`, `for:` the `pl` of the domain in `Method/domains.yaml`, module
   `method`, title “The <domain> checkpoint exceeds its 10 KB cap”, the `basis` carrying the line as it is, then “move the
   history to a domain archive to get back under 10 KB (method §6)”. **If a workstream
   `arbiter-c10-short-checkpoint-<domain>-*` already exists without being accepted, add nothing** for that domain: the PL
   has not resumed yet.

   Then regenerate the board (`python3 -B <Folder>/make_board.py <Folder>/workstreams.yaml <Folder>/workstreams.html`)
   and run the check again: the board check must be OK. The commit is made at §1.5.
4a. **The archiving, after the findings** — the arbiter's only mechanical write, never a correction by hand:
   ```
   python3 -B <Folder>/archive_workstreams.py archive --workstreams <Folder>/workstreams.yaml \
     --archives <Folder>/Archives
   ```
   The command dates `accepted-on: <today's date>` on every entry that has just become accepted, removes the date from a
   reopened entry, and moves out to `Archives/WORKSTREAMS_<YYYY-MM>.yaml` (the month of today: things are only appended
   to it, frozen at the end of the month) every entry accepted for seven days or more (the default delay: **do not pass `--delay`**); it checks that nothing is lost before
   writing, and run again at the same date it changes nothing. Code 0: done, with or without change. Code 1: done, with a
   warning — an unreadable `accepted-on:` date, which the command neither archives nor modifies: a `for:` workstream
   addressed to the coordinator, as in 4 (⟨`a`⟩ for the check, `archiving-<id>` for the key, the command's line as is).
   Code 2: invalid call, file or folder not found, lossless check failing — **nothing is written**: say so in the log
   (§1.5) and in the summary, nothing else. If the command dated or archived, **regenerate the board** (same command as
   in 4) and **run the check of 2 again** (with `--archives` and `--domains`): it must stay free of new gaps.
4b. **The reading of the checkpoints, on Mondays only** (`TZ=<time zone> date +%u` is `1`; on other days, nothing): read
   **each checkpoint** of `Method/domains.yaml` **in full**, against (a) the decision-log entries of the **last seven
   days** (the dates are in the text of each decision) and (b) the domain's workstreams. Flag **only** what can be proved
   by a quotation:
   - a sentence that a decision or a workstream contradicts — a domain attached, a rule changed, a closed subject still
     announced, a PL's or a file's name that has changed;
   - a queue subject written in plain words, with no workstream.

   Each flag: the checkpoint's sentence between quotation marks, and the decision or the id that contradicts it. **No
   opinion**, no style, no “one could”. For each domain that has at least one flag, **a single** workstream
   `arbiter-reading-<domain>-<YYYYMMDD>`, `for:` its `pl`, module `method`, title “The <domain> checkpoint contradicts the
   living docs”, the flags in the `basis` (on one line, separated by “; ”). **If a workstream `arbiter-reading-<domain>-*`
   already exists without being accepted, add nothing** for that domain: last week's flags are still waiting for their
   PL. Then regenerate the board and run the check of
   2 again, as in 4.
5. **The log, at every run, even without a gap**: one line appended **at the end** of `Method/ARBITER_LOG.md`, never a
   line rewritten:
   ```
   - <YYYY-MM-DD HH:MM> · <n> gap(s) · <n> new finding(s) · <the first baton silent for more than 24 h, or “batons fresh”> · archiving: <n> dated, <m> archived · checkpoints: <domains reported by checks 9 and 10, or “up to date”>
   ```
   `<n> gap(s)` is the number given by the last line of the check (“LIVING DOCS · <n> gap(s)”). On Mondays, the line adds **at the end** ` · reading: <domains flagged, or “nothing”>`; on other days, nothing. A “new
   finding” is a workstream filed that day (entries the archiving dates or moves out do not count). The time is the
   owner's (`TZ=<time zone> date '+%F %H:%M'`); a code 2 of the check is written “check impossible: <file>”, a code 2 of
   the archiving “archiving: impossible, <message>”. Then **a single commit**: “Arbiter <date>: living docs compliant”
   (the log alone) or “Arbiter <date>: <n> finding(s)” (the log, `workstreams.yaml`, `workstreams.html`); when the
   archiving dated or archived, the message adds “, archiving: <n> dated, <m> archived” and the commit also carries
   `workstreams.yaml`, `workstreams.html` and `Archives/`; `git fetch origin main`, rebase, push. A rejected push:
   `git pull --rebase`, one single new attempt; a conflict: nothing is forced, say so in the summary. **This log is
   what proves the arbiter ran** — not the notification (§4.6).
6. **The summary**: the session's final reply, short — the date, the number of gaps, the new findings (one per line,
   with the PL addressed), those already reported and still there, the archiving (“<n> dated, <m> archived”), the
   domains reported by checks 9 and 10 and, on Mondays, those flagged by the reading, the commit pushed. Without a gap: “Living
   docs compliant on <date>”, one line.

---

## §2 · Whom to address a finding to

| what is at issue | `for:` |
|---|---|
| a workstream of a domain (its `module:`) | that domain's PL (table in the method §1a) ⟨one line per domain, if needed⟩ |
| a workstream in flight | the `pl:` it carries, if it carries one; otherwise the PL of its module |
| a gap on a deliverable or a shared resource (two batches in flight) | the PLs of the batches at issue, one workstream each |
| a checkpoint lagging (check 9); its size (check 10); the Monday reading | the `pl` of the domain in `Method/domains.yaml`, one workstream per domain |
| a module with no PL opened | the coordinator |
| everything else: decision log, board, plan log, arbiter's log, batons, domain table, `method` | the coordinator |

---

## §3 · What the arbiter never does

- Correct an entry, a number, a checkpoint, a baton or the domain table: it reports, whoever holds the file corrects.
  **The only exception, mechanical: the archiving** (§1.4a) — `archive_workstreams.py` dates, undates and moves out the
  accepted entries; the arbiter never touches by hand an accepted entry or an `accepted-on:` line.
- Write anywhere other than at the end of `workstreams.yaml`, in the regenerated `workstreams.html`, at the end of
  `ARBITER_LOG.md`, and what `archive_workstreams.py` does (the `accepted-on:` lines, the entries moved out,
  `Archives/WORKSTREAMS_<YYYY-MM>.yaml`).
- Judge a checkpoint on style or timeliness: the Monday reading only flags what a decision or a workstream contradicts,
  with the quotation and the evidence.
- Reserve a decision number, take a deliverable or a resource, brief, launch a dev.
- Open another session, send a message outside the repository (messaging, an e-mail it writes itself).
- Push more than one commit per run, or force a push.

---

## §4 · The scheduled task — the configuration, step by step

*For the coordinator and the owner; the arbiter's session does not read this §.*

1. **Before**: `check_living_docs.py`, `archive_workstreams.py` and `make_board.py` copied into the living docs;
   **the domain table `Method/domains.yaml` created** (template `templates/domains.yaml`: one entry per PL,
   **the coordination included**, the exact start of the title of each checkpoint's queue section in `queue:`) and **every checkpoint given that section**
   (template `templates/CHECKPOINT.md`); `Archives/` created (git does not track an empty folder: an empty file
   `Archives/.gitkeep`); this file copied to `Method/ARBITER.md` and adapted; `Method/ARBITER_LOG.md` seeded, pushed:
   ```
   # Living-docs arbiter's log

   *One line per run, appended at the end by the “Living-docs arbiter” task (`Method/ARBITER.md` §1.5). Never
   rewritten. Format: date and time · gaps · new findings · batons · archiving · checkpoints · reading (on Mondays).*
   ```
   **Who keeps the domain table**: the coordinator, in step with the method's table §1a — **every time a domain is opened
   or closed, and every time a queue section is renamed**. A table that lags makes a gap in check 9.
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
   then read `Method/ARBITER.md` in full and follow it to the letter: check with `check_living_docs.py` (with
   `--archives` and `--domains`), one `for:` workstream per new gap (never twice) — the one for the checkpoint check
   grouped into a single one per domain —, checkpoint batons judged by their silence, accepted workstreams archived by
   `archive_workstreams.py`, board regenerated, on Mondays only the reading of the checkpoints against the week's
   decisions, one line at the end of `Method/ARBITER_LOG.md` at every run, even without a gap, a single commit pushed.
   You correct nothing else; you reserve no number, take no deliverable, launch no dev, open no other session and send
   no message anywhere else. Commits end with the line `Co-Authored-By: Claude <noreply@anthropic.com>`. Your final
   reply is the summary for the owner, in English and short: the date, the number of gaps, the new findings (one per
   line, with the PL addressed), those already reported and still present, the archiving, the domains reported by the
   checkpoint check and, on Mondays, those flagged by the reading, the commit pushed; without a gap, a single line
   “Living docs compliant on <date>”.
   ```
   The prompt does not change when the procedure changes: it reads it. (It only changes if the procedure gains or loses a
   family of moves, as here the checkpoint check and the Monday reading.)
6. **The notifications**: in the task's Notifications tab, **tick push** — the Claude app installed and signed in on
   the owner's phone, its notifications allowed by the system. **The e-mail may not arrive** (seen: a successful run,
   with findings, and no e-mail at all), and **the platform alone decides whether a run is “notable”**: a run with
   nothing new often sends nothing. **The log is the proof it ran**, not the notification: one line a day, or nothing.
7. **The first run** is started by hand, on the day of creation; the coordinator checks the log line and the commit.
   **On a project already under way, the first check 9 is chatty**: all the open workstreams the checkpoints do not
   cite yet come in at once (fifteen lines on the first trial, across six domains: six workstreams — one per domain,
   hence the grouping). The first check 10 is too: the checkpoints already beyond 10 KB come in at once, one
   workstream per domain. Warn the PLs beforehand, or accept this first batch of workstreams: afterwards, checks 9 and 10
   only report what is new. Then, every morning, one more line.
8. **A missed run** (no line in the log): a usage limit can make an early-morning run fail; if it happens again, move
   the time. An isolated failure is not made up: the next run checks everything.
9. **Who does what** — the checklist:

   | move | who | done when | proof it is done |
   |---|---|---|---|
   | copy `check_living_docs.py`, `archive_workstreams.py`, `make_board.py` into the living docs; create `Archives/` | coordinator | before | the files in the repository, `Archives/.gitkeep` |
   | write `Method/domains.yaml`, one entry per PL, the coordination included | coordinator | before | check 9 runs with no table fault |
   | give each checkpoint its queue section, each subject cited by its id | each PL | before the first run, then at every resume and handover | check 9 no longer reports their domain |
   | copy and adapt `Method/ARBITER.md`; seed `Method/ARBITER_LOG.md`; push | coordinator | before | both files in the repository |
   | create the scheduled task (name, off-the-hour time, prompt, fresh session); set automatic approval | coordinator or owner | day 1 | the task in the list of scheduled tasks |
   | install the mobile app, allow its notifications; tick push | owner | day 1 | a notable run arrives as a notification |
   | warn the PLs that they will receive `for:` workstreams from the arbiter | coordinator | before the first run | a ready-to-paste message, handed to the owner |
   | start the first run by hand; check the log line and the commit | coordinator | day 1 | the line and the “Arbiter <date> …” commit |
   | read the `for:` workstreams addressed to them after every `pull`; correct | each PL | continuously | the workstream moves to accepted |
   | keep the domain table: domain opened, closed, queue section renamed | coordinator | at every change | no “table” gap in check 9 |
   | skim the log; judge **keep, adjust, stop** | coordinator and owner | after the trial week (§5) | the decision, written down |

---

## §5 · The trial and the verdict

- **A one-week trial**, from <date> to <date> — **it must include a Monday**, so that the first reading of the
  checkpoints is judged —, then the coordinator judges with the owner: **keep, adjust or stop**. The evidence: the log
  (did it run every day?), the findings (true or false), what the PLs did with them, **the archiving** (were the entries
  moved out really finished, does anything go missing from the living docs — `archive_workstreams.py search` —, does the
  check stay free of gaps with `--archives`?), **check 9** (were the lines true: an open workstream really absent from
  the checkpoint, a closed workstream really cited? did the PLs bring their queue back in step, does the check fall to
  “up to date”?), **check 10** (were the checkpoints reported really beyond 10 KB, and did they come back under it once
  their history was archived?) **and the first Monday reading** (did each flag carry a quotation and evidence? was there a disguised
  opinion or a false flag?).
- **A false positive is corrected in the procedure, not case by case.** A real example: the first baton rule judged
  their age (“taken for more than 24 hours”); it reported two very much alive sessions that were waiting for the owner.
  The rule became the silence rule (§1.3).
- A change to the procedure changes this file (version at the top), not the task's prompt — unless the procedure gains or
  loses a family of moves (§4.5).
