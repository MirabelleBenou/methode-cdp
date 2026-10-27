# METHOD — <Project> · v1
### <date> · <PL session name> · drawn from the PL method package v<n>

*How a batch is decided, built, accepted and closed.*
- *It changes by version, after a batch that caught it out; each version cites the decisions in the log that ground
  it.*
- *The dev's side is in `DEV_PROMPT_<P>.md`, at the root of the `<Project>-App` repository.*
- *It takes precedence over the `methode-cdp` skill, which carries the part common to all projects.*

> **How to use this template** — what is in plain text is generic: keep it. What is between `⟨…⟩` is specific to the
> project: fill it in at bootstrap, or at the first batch that decides it. Delete this box.

**The repositories**:

| repository | carries | who writes to it |
|---|---|---|
| `<owner>/<Project>` (private) | the living docs: this method, the plan, the decision log, `workstreams.yaml`, the checkpoint, the expected results and the PL's scripts | the PL sessions only |
| `<owner>/<Project>-App` (⟨private / public⟩) | the code at the root (the deployment archive is `git archive` of the delivery commit), the test bench in `bench/`; ⟨private:⟩ the dev prompt and `batches/<version>/` | the PL on `main` and for the brief; the dev on the branch of their batch |
| ⟨public code only:⟩ `<owner>/<Project>-Batches` (private) | the dev prompt, `batches/<batch>/` — **never in the public repository** | the PL (brief, addenda); the dev (stops, report) |

⟨Several code repositories:⟩ they share **a single `<Project>-Batches`**, and each batch there carries a module prefix
(`batch/<prefix>-<batch>`); the code starts from the module's repository, on `batch/<batch>` (`3_GITHUB.md` §6 C).

---

## §1 · Who does what

- **The owner** decides and validates: on screen when the batch shows a mock-up, otherwise in production.
  - ⟨If they read on a tablet or phone, without Python: **every file is regenerated on Claude's side**; they are
    never asked to run a script or a command⟩.
  - You write to them briefly, in **numbered options with a recommendation**.
  - **A text they paste is handed over ready**, with no field to fill in; if it depends on a value still to come (a
    hash, a decision number), the session that produces it hands it over complete.
  - Every answer in which the PL decided without them ends with **“Decided without you: …”**.
  - **A purely technical decision can be delegated to them**: the PL decides, records it in the log and says so in
    its answer.
- **The PL** (Opus, long session) decides with the owner, writes the brief, launches the dev, accepts and closes. They
  reason as a developer **and** as a designer: they recommend on the code and on the visuals.
  - **They write no code of the deliverable or of the test bench. Not in a brief either**: a brief carries rules,
    criteria and the texts the user will read, never the fully written code. A fingerprint that cannot be predicted
    without writing the code is taken from the dev's account.
  - They write their **throwaway scripts** for measurement, probing or mock-ups, which are never passed on to the dev.
  - They may edit the **documentation** directly, with the owner's authorization.
- **The dev** (a new session per batch) builds, measures cold and delivers. **Sonnet by default; Opus for** ⟨the
  calculation engine, a delicate migration, writing…⟩.
  - **The PL launches them themselves, as a sub-agent of their session**: the dev starts **without the PL's context**,
    with the command of §2 as their only instruction. Their report and stops come back to the PL. **The owner talks
    only to the PL.**
- **Tooling is code**: a missing tool is ordered through a **tooling batch**, with a short brief. The test bench is
  maintained by the dev.
- **Several PLs can work at the same time**, one per domain, on the same living docs: §1a.
- The **mechanical checks** belong to the PL and the dev; the **visual checks** to the owner.

---

## §1a · Several PLs at the same time

*With two, “`git pull` before writing” is enough. With four, decision numbers come out twice, counters drift, versions
are shared out through messages the owner relays (first project, four PLs in parallel).*

**Five principles**:
1. **One active PL = one domain = a checkpoint of its own.** Nobody writes in someone else's checkpoint.
2. **What is shared is written append-only** (decision log, plan, `workstreams.yaml`): no rewritten summary, no “last
   updated” line, no header version on a shared file — the history is in git.
3. **Anything numbered is reserved by a push**: a refused push is the only atomic operation available.
4. **What can be computed is not written**: totals, the board. After a conflict, regenerate; never merge by hand.
5. **A file that is not append-only has a single owner**: this method, the dev prompt, the living-docs README and the
   method package belong to **the coordination session** (Opus-Coordination).

**The domains**: ⟨one line per PL — its name (`Opus-PL-<Product>[-<Module>]`, a module only when a product has several
PLs), what it carries, its checkpoint (`<Folder>/CHECKPOINT_<PRODUCT>_<MODULE>.md`); plus the coordinator and its
checkpoint⟩. The living-docs README holds the same table, with each one's resume line.

**Opening a domain**: the owner tells the coordinator what they want to do; the coordinator gives the fixed line of an
existing domain with a free baton, or opens the domain (line here and in the README, seeded checkpoint, workstreams
attached), then gives each PL's title and line — or starts the session through a scheduled task. A product with several
module PLs keeps a **product sheet** (what is common: ritual, bench, circuit, pitfalls), held by the coordinator.

**Decision numbers**: before writing an entry, push alone, on `main`, the line
`| **D<n>** | *reserved — <PL>, <date>* | | |` after the last entry. Push refused → `git pull`, next number;
accepted → the entry is written in its place. An entry carries no total: it marks `[execution +1]` or
`[reverse +1]` (§5).

**Code versions**: a batch in flight carries in `workstreams.yaml` `status: in-flight`, `pl:` and `version:`; pushing
the entry reserves the version, at the brief, before the branch. Batches are merged in the order of their versions; an
overtaken batch rebases on the new `main` and redoes its acceptance. A file of another domain is declared (`touches:`).

**Between PLs**: a report for another domain becomes a workstream of its module, `status: to-brief`, `for: <PL>`;
**after every `pull`, a PL reads the `for:` entries addressed to it**. The owner no longer relays. A generic lesson is a
workstream `module: method`, `for:` the method session.

**The baton**: each checkpoint carries at the top `Session active: <short id>, since <time>` (or “none — free since
<time>”). The resuming session sets it by a push, its first move; a session that finds another id than its own after a
`pull` stops writing to the living docs and tells the owner; a session waiting for the owner keeps the baton.

**The session title**: `<PL name> · <current workstream>`, changed at each workstream; `-2` for a second PL on the same
domain, with its own checkpoint. The session renames itself if it can, otherwise it gives the title to the owner at the
top of its reply.

---

## §2 · The cycle of a batch

1. **The decision**, with the owner, recorded in the log at close-out. For structuring work, the spec or the design is
   validated before any execution.
2. **The measurement, then the brief** (§3), and the PL's mock-up if there is one (§3a).
   - **The acceptance expected results are computed at brief time**, in `<Folder>/expected/<version>/` of the
     living-docs repository — never in the code repository, which the dev reads. A delivery simulated by the PL can
     be used to compute them: **it is never passed on**.
   - **The PL pushes the brief on the batch branch**: `batch/v<X.Y>`, started from the head of `main`, which carries
     only one more commit, `batches/v<X.Y>/BRIEF.md` (and its mock-up). The brief names this base commit.
   - **The PL launches the dev**: `Agent` tool, in the background, **the model and effort mode of the brief**, and a
     command in four parts (template: `DEV_COMMAND.md`) — who they are and what they execute; the practical
     conditions, which take precedence over the brief; the stops; their final answer.
   - **Fallback**: if the PL cannot launch a sub-agent, they give the owner a line to paste word for word, with above
     it “**Sonnet · Medium · new conversation**” (model, effort, session).
   - **Safeguard**: a sub-agent consumes the credit of the PL's session; the handover is always measured.
3. **A dev stop**: the dev pushes their branch and the reason (`STOP_<n>.md`). The PL reads it in the repository,
   pushes `ADDENDUM_<n>.md` on the same branch and relaunches the dev (the same sub-agent if it can be reached,
   otherwise a new one, which also reads the previous reports).
4. **The delivery**: the delivery commit, then `DEV_REPORT.md` in a separate commit.
5. **The acceptance** (§4), then the verdict to the owner, with the prediction for production, and **the deliverable
   handed over as is**, under its exact name, with its sha256.
6. **A fix** of a delivered batch carries the next version, on its own branch started from the batch's branch. **Trial
   feedback** before validation goes through addenda in series, in the same dev session if it is still open.
7. **Validation in production by the owner**, then **the merge**: `git push origin batch/v<X.Y>:main` as a
   fast-forward, never `--force`; finally **the close-out** (§6), once per batch.

---

## §3 · The brief, the dev command

**It carries** (template: `BRIEF.md`):
- the dev's **model**, **effort mode** and **session**;
- the owner's decisions and the rules;
- **what does not move**, and the **exact list of files** the batch is allowed to touch;
- the criteria and the prediction of the gates, **as deltas against the base measured cold**;
- the `CHANGELOG` text, word for word;
- the stops specific to the batch;
- the base commit and the pieces it pushes with it — nothing to upload.

**It is self-contained**: with the dev prompt, it is sufficient. It cites neither a previous brief nor the brief
template.

**The effort mode**: Medium by default; High for a migration, a deep pass, several screens, a new screen with its
routes, a calculation engine, cascading steps; Low for a one-line fix.

**Measure first**:
- **On the verified real state**, never on the assumed execution of a previous batch. When specs have piled up,
  consolidate them into a single brief.
- **On real data when there is some**: a read-only probe, proven on the test bench, run in production (by the owner,
  as a shell script to drop in), whose output comes back to the PL. The measurement often shifts the batch.
- **Before calling a table, a file or a field by what it contains, read every place that writes to it.**
- **A setting that changes a non-deterministic behavior** (a language model, a rendering) **is measured before it is
  briefed**, through a throwaway PL script.

**Look for what the change breaks**:
- **Before ordering a change of value, contract or formula, search the tests and the test bench for the values it
  changes**, not only the symbols it touches. Adding a read or a write to an existing route changes its contract.
- **Before creating a table, a column, a route or a file, look for the one that already plays that role.**
- **Run the triggered debts against the batch's file list**: a file the batch touches can settle a debt along the
  way.

**Write the criteria**:
- **Before writing a criterion, run it on the existing code.**
- **As deltas against the base**, never as absolute values; **measured on the delivered archive**, never on the
  working directory.
- **A textual counting criterion states whether it counts comments.**
- **A prediction is computed under the brief's rules**, not under an ideal reading.
- **A calculation prediction is a replay**: the engine replayed on the base, each rule applied alone then all
  together, the expected output and its sha256; the dev finds the same output.
- **A duplicated rule is held by an equivalence criterion**: the copy compared with the original on all the test
  bench's cases.
- **A rendering fingerprint names its conditions** (locale, size, theme).
- **A color or contrast rule is measured on all themes** before being ordered.
- **A label is measured at the narrowest width that carries it**; an overflow, at both ends of each breakpoint.
- **A brief that makes an unnamed API a stop names all those its own format requires.**

**The proofs and the dev**:
- **No pixel criterion against the base**, except to prove that a refactor is neutral (§3a). Against the PL's
  mock-up, yes.
- **Images only if the visual is worth seeing before production**: three to six, designated by name; otherwise
  the owner validates in production. **A placed piece** (photo, stamp, badge) **is shown in crops at scale 1**,
  never in a reduced page.
- **Functional proof goes through the tests**; a purely screen batch is proven by a screen check (presence, absence,
  DOM texts and counts), with no capture reviewed by the dev.
- **No over-engineering**: no test beyond what proves the batch; tooling does not eat the batch's budget.

---

## §3a · The PL's mock-up, through the real code, before launch

*The PL writes throwaway code in it, never that of the deliverable.*

- **For a new screen**, you start from a copy of the base, graft on the view, its script and its CSS, and render it
  through the real code, on data set by a **test bench state file**.
- **For a touch-up of static files** (CSS, template), the copy directly carries the batch's files; the brief then
  requires the dev **to take them as they are**, checked by their sha256.
- **What the mock-up fixes goes into the brief character for character.**
- **A refactor that must be neutral is proven at brief time**: the PL renders on their copy the touched screens
  against the base, pixel-identical; the dev replays the same instruments. The instrument **masks everything that
  carries the version**.
- **Reference images are taken on the mock-up**, not on the base, when the base carries a defect that changes the
  rendering; **a control rendering injects only the expected cause**, to separate the effect from the noise.
- **A row being edited preselects the neutral value**, never a named computed value.
- **The owner validates the mock-up before launch.** When they reopen a discarded option after seeing it, **redo it
  rather than defend it**.

---

## §4 · Acceptance, cold

**Prerequisites**: ⟨the repositories cloned, the base extracted by `git archive` from `main`, the test bench copied,
the dependencies installed under the right version, the services started in the command that uses them⟩.

**The steps**:
1. **The expected results**, computed at brief time in `<Folder>/expected/<version>/`. **They are never copied from
   the dev report.** Only an unpredictable value is taken from their account, then recomputed.
2. **The delivery archive**: `git archive` of the delivery commit named by the report. **It is the deliverable**: the
   one measured is the one the owner deploys.
3. **The gates, replayed** on the unpacked archive: ⟨the test bench ritual, the common measurement, tests, lint,
   syntax check on the output actually produced — not only on the sources⟩.
4. **The diff, read against the brief's rules**: each rule is found in the code; **nothing outside the authorized
   files**; outside the code, nothing moves except `batches/v<X.Y>/`.
5. ⟨**The migration**, if there is one: up, down, up again from a base seeded at the previous head.⟩
6. **The rendering, looked at by the PL themselves**: the dev reviews no capture, so nobody else sees the screen
   before the owner. What the criteria do not measure can only be seen there. With a mock-up: pixel comparison.
7. **The deliverable handed to the owner as is**: under its exact name, with its sha256 in the verdict. A single file
   to deploy (an HTML page) is handed over **outside a zip**.
8. **The verdict**: compliant, or a fix (next version). **A justified dev stop is never a reproach**: execution is
   often right against the brief.

---

## §5 · What is unforgiving

- **Nothing is believed, everything is measured**, on the archive unpacked cold. The gates are read as deltas.
- **The version**: ⟨who bumps it — `release` script on the dev side, pre-authorized, +1 step per batch / only with
  the owner's explicit agreement⟩. A batch that does not change the code (method, test bench) takes no version.
- ⟨The project's invariants: a file, a module or a fingerprint that only move on the owner's written authorization
  carried by the brief.⟩
- **Produced texts remain gender-neutral**: never presume a person's gender from a pseudonym.
- ⟨Public code: the dev prompt and `batches/` in the private batches repository, never in the public one; zero
  private reference in the pushed diff (first name, profile, method, decision log) — a pushed file stays in the
  public history.⟩
- **The “execution is right” count** is kept in the decision log: each justified stop or report from the dev is
  added to it. A PL defect seen in production opens the reverse count.

---

## §6 · Close-out and the documents

**At each closed batch, once**:
- the plan's version log line, for a batch that takes a version;
- the decision log (the decision, and “what the batch teaches” when there is a lesson);
- `workstreams.yaml`, **then `workstreams.html` regenerated** (below);
- **a commit “Batch v<X.Y> closed”** in the living-docs repository, then **the mirror in the project**;
- the checkpoint **of the domain**, at handover.

Two batches accepted the same day can be closed together.

**The living docs**:
- live in the living-docs repository **under stable names**; the version is in the header, the history in git;
- are modified by targeted replacements, or replaced in full while removing what is obsolete;
- **stay short**: when one grows long again, what no longer lives goes into a **new archive**
  (`Archives/<NAME>_ARCHIVE_<range>.md`), frozen, never rewritten;
- **the project carries a mirror of them**, copied at each close-out by `project_write` with `local_path` from the
  clone; **never from the text served by the project tool**.

**The workstreams board** — the readable page of `workstreams.yaml`:
- **Every time the PL writes `workstreams.yaml`** — at close-out, but also mid-exchange (a workstream added, a
  status that changes) —, they regenerate `workstreams.html` in the same move with
  `python3 -B <Folder>/make_board.py <Folder>/workstreams.yaml <Folder>/workstreams.html`. A `workstreams.yaml`
  modified without its page is not finished.
- They commit both together in the living-docs repository, copy both to the project as a mirror, **publish the page
  as an artifact at the same link** (the link is recorded in §6 of the checkpoint) and **hand it over as an `.html`
  file** in the conversation.
- Republishing an artifact from a previous conversation requires reading it first (the tool asks for it): the PL
  reads it once per session, compares it with the regeneration, then republishes the same file at the same link.
- `make_board.py` is not modified for a project: title and labels are read from the header of
  `workstreams.yaml`.

**Where each document lives**:
- **in the living-docs repository**: the living docs, the sub-projects' statuses, the expected results, the PL's
  scripts;
- **in the code repository**: the code, the test bench, the dev prompt, and under `batches/` the briefs, addenda,
  stops, reports and mock-ups — outside the deployment archive;
- **in the project, written once**: specs, style guide and addenda, studies, reference notes; they are never
  rewritten;
- **nowhere**: dev reports and one-off briefs do not go into the project.

**The PL files into the project themselves**: they say what they wrote (repository, commit, path); **they delete
nothing without the owner's explicit agreement**, except the version they have just replaced; a new document is
created in its folder, never at the root; an old one joins its folder at its next update.

| project folder | carries |
|---|---|
| `Method/` | this method, the dev prompt (mirror), the common charters |
| `<Folder>/` | the plan, the decision log, `workstreams.yaml` and `workstreams.html`, `make_board.py`, the checkpoint, the reference notes |
| `<Folder>/Archives/` | the frozen archives |
| `<Folder>/Specs/` · `<Folder>/StyleGuide/` | the product references |
| ⟨`<SubProject>/`⟩ | ⟨one folder per sub-project⟩ |

**What is still uploaded** into the session that needs it: production data, which go into no repository. **No more
handover prompt** (the handover, below). **Images** go through the conversation, never through the project files.

**The handover is measured, not guessed**:
- **What is measured**: the context size at the last turn, with `python3 -B <Folder>/pl_tools/context.py` (copied
  from the package). It is not the cumulative consumption since the start of the session, which grows much faster.
- **When**: at each batch close-out, before each brief or dev launch, and at least every ten exchanges.
- **At 600,000 tokens, the PL warns the owner**, at the top of their answer: “Context: ~N tokens — handover ahead”.
  They no longer launch a new batch; they finish the one in progress.
- **At 700,000 tokens at the latest**, or at a natural end of a queue before that, **they hand over**, without waiting
  to be asked, in one go, in a single answer:
  1. §0 of the domain's checkpoint rewritten on the real state (where things stand, what blocks, what awaits the owner);
  2. the baton set back to “none — free since <time>”;
  3. push, then the mirror in the project;
  4. **the domain's fixed line**, under “**Opus · new conversation in the project**”: “You are <PL>. Resume: attach
     `<owner>/<Project>` (push access), git pull, read `<domain checkpoint>` in full (§0 first) and follow it.”
- **Nothing travels outside the repository**: no handover prompt, no “next number”, no reserved version in a text handed
  to the owner — a text that copies the state ages while the other PLs move on.
- **The resume can be started by the session itself**: a one-off scheduled task whose prompt is the fixed line; the
  owner opens the session in their task list. When the owner is not there to open it, the fixed line is enough.
- **At the first sign of saturation** before the threshold (losing the thread, contradictions, a forgotten decision):
  same handover, right away.
- A dev sub-agent's context does not count in the PL's; its credit does.

---

## §7 · The sandbox traps

**General**:
- **The sandbox keeps nothing from one session to the next**: everything is rebuilt from the repositories.
- **A command has a timeout** (up to 600 s, to be checked); beyond that, background and a **marker file** written at
  the end (a `pgrep -f …` probe finds itself).
- **Several versions of an interpreter can coexist**: the default version is not necessarily the production one;
  ⟨pin the right one⟩.
- **Running a script creates caches** (`.pyc`…) that skew the counts: measure first, test on a copy.
- **`cut -c` cuts UTF-8**: documents are read with a real language.
- **The project files are not on disk**: the project tool returns them as text.

**Git and GitHub**: see `3_GITHUB.md` §5 of the package — tags, releases and branch deletions by the owner; clone of
a single branch; attribution lines; no secrets.

⟨**Specific to the project**: to be completed batch after batch — each trap paid for once is written here.⟩

---

## §8 · The target cost

- **An ordinary batch**: ten to twenty minutes of dev, an acceptance of a few minutes.
- **A screen with a PL mock-up**: from 15 minutes to 1 h 30 of dev; the mock-up validated in one or two rounds.
- **An addendum launched by the PL**: a few minutes, without a move from the owner.
- **The PL records their own cost** at each handover: measured context, main items.

---

*Written by <session> on <date>, at the project's bootstrap (D1), from the PL method package v<n>.*
