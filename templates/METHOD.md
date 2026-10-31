# METHOD — <Project> · v1
### <date> · <PL session name> · drawn from the PL method package v<n>

*How a batch is decided, built, accepted and closed.*
- *It changes by version, after a batch that caught it out; each version cites the decisions in the log that ground
  it.*
- *The dev's side is in `DEV_PROMPT_<P>.md`, at the root of the `<Project>-App` repository.*
- *It takes precedence over the `methode-cdp` skill, which carries the part common to all projects.*
- *The terms (baton, queue, batch, deliverable, living docs…) are defined in the package's `GLOSSARY.md`.*
- *It carries only what holds for all the domains: every PL re-reads it, and on the first project 40% of its text served
  only a single product (measurements, mock-up, test bench, screen pitfalls). **What is specific to a product goes to its
  product sheet** (the one the coordination keeps when a product has several PLs) **or to the checkpoint of its
  domain** — a paragraph is enough here to point to it.*

> **How to use this template** — what is in plain text is generic: keep it. What is between `⟨…⟩` is specific to the
> project: fill it in at bootstrap, or at the first batch that decides it. Delete this box.

**The repositories**:

| repository | carries | who writes to it |
|---|---|---|
| `<owner>/<Project>` (private) | the living docs: this method, the plan, the decision log, `workstreams.yaml`, the checkpoint, the expected results and the PL's scripts | the PL sessions only |
| `<owner>/<Project>-App` (⟨private / public⟩) | the code at the root (the deployment archive is `git archive` of the delivery commit), the test bench in `bench/`; ⟨private:⟩ the dev prompt and `batches/<version>/` | the PL on `main` and for the brief; the dev on the branch of their batch |
| ⟨public code only:⟩ `<owner>/<Project>-Batches` (private) | the dev prompt, `batches/<batch>/` — **never in the public repository** | the PL (brief, addenda); the dev (stops, report) |
| ⟨production server with a server runner:⟩ `<owner>/<Project>-Orders` (private) — the orders repository, **and the file-exchange bridge** (`transfers/`) | `ordres/<id>.json` (orders), `resultats/<id>.md` (reports), the order format in `LISEZ_MOI.md` (§4a); `transfers/<domain>/<edition>/`: the data produced in a session, for as long as it takes to serve it | the PL (the orders, and the transfers: whoever produces the data); the server runner (the reports); **never the dev** |

⟨Several code repositories:⟩ they share **a single `<Project>-Batches`**, and each batch there carries a module prefix
(`batch/<prefix>-<batch>`); the code starts from the module's repository, on `batch/<batch>` (`3_GITHUB.md` §6 C).

---

## §1 · Who does what

- **The owner** decides and validates: on screen when the batch has a mock-up (the PL shows it to them), otherwise in production. ⟨With a server
  runner: they no longer drop anything; they say “go” naming the action, then validate (§4a).⟩
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
    only to the PL, and the dev too: it talks only to the PL**, through what it pushes and through its final reply; the
    owner does not read it.
- **Tooling is code**: a missing tool is ordered through a **tooling batch**, with a short brief. The test bench is
  maintained by the dev.
- **Several PLs can work at the same time**, one per domain, on the same living docs: §1a.
- ⟨**The server runner** (a program on the production server) deploys the PL's orders; it decides nothing (§4a).⟩
- **The owner's machine** (a game, an application, the screen): **the PL's session works on it itself, through the
  bridge** of the Claude app — linked folders (read, write), a terminal if one is offered, the screen through computer
  use, the owner validating the access in the PL's conversation. **The local runner**, driven by files
  (`templates/LOCAL_RUNNER.md` of the package), **is now only the fallback**, when the bridge is not offered: it got stuck
  when the owner was away from their machine. Everything stays under the project folder, never in an application's; **a
  workstream that needs the machine is a debt as long as the owner is not there**.
- The **mechanical checks** belong to the PL and the dev; the **visual checks** to the owner.

---

## §1a · Several PLs at the same time

*With two, “`git pull` before writing” is enough. With four, decision numbers come out twice, counters drift, versions
are shared out through messages the owner relays (first project, four PLs in parallel).*
*A single PL, independent modules, or linked modules with a coordinator: what applies in each case is in the method
package's `GUIDE.md` §2a.*

**Five principles**:
1. **One active PL = one domain = a checkpoint of its own.** Nobody writes in someone else's checkpoint.
2. **What is shared is written append-only** (decision log, plan, `workstreams.yaml`): no rewritten summary, no “last
   updated” line, no header version on a shared file — the history is in git.
3. **Whatever can be taken only once is taken by a push** (a decision number, a deliverable): a refused push is the
   only atomic operation available.
4. **What can be computed is not written**: totals, the board. After a conflict, regenerate; never merge by hand.
5. **A file that is not append-only has a single owner**: this method, the dev prompt, the living-docs README and the
   method package belong to **the coordination session** (Opus-Coordination).

**The domains**: ⟨one line per PL — its name (`Opus-PL-<Product>[-<Module>]`, a module only when a product has several
PLs), what it carries, its checkpoint (`<Folder>/CHECKPOINT_<PRODUCT>_<MODULE>.md`); plus the coordinator and its
checkpoint⟩. The living-docs README holds the same table, with each one's resume line;
**`Method/domains.yaml`** (template `templates/domains.yaml` of the package) holds it in the form the checker reads
(check 9): a domain, its PL, its checkpoint, the title of its queue section (§6), its modules. **The coordination has
its line in all three, like a domain**: it has a queue like the others (`Method/CHECKPOINT_METHOD.md`). **The coordinator
keeps the three in step**: a domain opened or closed changes all three. **A renamed queue section changes the domain's
`queue:` line in the same commit, by the PL that renames it** — the only line of the table it touches; an empty `queue:`
is a gap of the domain, which the checker flags.

**Opening a domain**: the owner tells the coordinator what they want to do; the coordinator gives the fixed line of an
existing domain with a free baton, or opens the domain (line here, in the README and in `Method/domains.yaml`, seeded checkpoint, workstreams
attached), then gives each PL's title and line — or starts the session through a scheduled task. A product with several
module PLs keeps a **product sheet** (what is common: ritual, bench, circuit, pitfalls; never the state), held by the
coordinator. The coordinator briefs no product batch; **it briefs and launches the tooling batches of the method and of
the living docs** (`check_living_docs.py`, `make_board.py`, the arbiter — `Method/ARBITER.md`, drawn from
`templates/ARBITER.md` of the package: role, why, procedure, scheduled task).

**Closing a domain**: a finished or dormant domain closes on the owner's decision, between two batches. The coordinator
(in B, the PL that holds the method) marks its checkpoint “closed” (it stays as a reference), removes the domain from
the table in the three places, attaches its open workstreams to a living domain (a `for:` workstream to its PL) and
records the decision. Moving from one mode to another, in either direction: `GUIDE.md` §3b of the package.

**Decision numbers**: before writing an entry, push alone, on `main`, the line
`| **D<n>** | *reserved — <PL>, <date>* | | |` after the last entry. Push refused → `git pull`, next number;
accepted → the entry is written in its place. An entry carries no total: it marks `[execution +1]` or
`[reverse +1]` (§5).

**The deliverable and its version**: the deliverable is the code repository the release comes out of. **One
deliverable, a single batch in flight**: the batch in flight carries in `workstreams.yaml` `status: in-flight`, `pl:`
and `deliverable:`, and pushing that entry takes the deliverable. **Another batch of the same deliverable is
suspended**, even from another PL: it stays `to-brief` with `waits: <id>`, no brief pushed, no branch, no dev, until the
first one is validated in production and merged (or, for a deliverable published by release, merged after acceptance —
see below; or abandoned on the owner's decision). **Study and pre-brief stay free**: the pre-brief (rules, criteria,
texts, no version, no expected results) may be pushed to the batches repository, under `batches/<batch>/PRE_BRIEF.md`; it
becomes the brief when the batch takes the deliverable. A file of another deliverable is declared (`touches:`). A batch
with no release (a probe, a played study, documentation) carries no `deliverable:`.

**Nobody decides a version number in advance**: no checkpoint, workstream, study or message announces “such version for
such batch”. **Two versioning regimes, depending on the deliverable**:
- **deployed per batch** (an application in production, its agent, the deployer): the version is computed when the batch
  takes the deliverable, before its branch: the version of `main` plus one; it is then written in `version:` of the
  in-flight entry and in the brief; a suspended batch that resumes computes it on the new `main`, redoes its base and its
  expected results;
- **released** (a tool downloaded as a package): **the batch carries no version** (neither `version:` nor a number in the
  brief); it completes the “Unreleased” section of the `CHANGELOG` (and the files to download, if there are any) and
  **frees the deliverable at its merge, after acceptance**. **The release is made at the owner's request**: the PL then
  fixes the number by the repository's `CHANGELOG` rule, renames the section, rebuilds the packages in one pass and
  hands the owner the text and the packages. For this regime, validation in production is that release; whatever depends
  on a release (data dropped on a server) waits for the release.

*Why two regimes*: “the version is computed when the batch takes the deliverable” holds for what is deployed at every
batch. For a suite downloaded by release, a release per batch is noise for those who download it, and brings them
nothing: the batches are grouped into a release the owner asks for.

**A shared resource is taken like a deliverable**: the owner's machine and what it runs for a batch (the local runner,
a game, a driven piece of software) host one batch at a time, whatever its domain. The batch that occupies it carries
`resource: <name>` in its `in-flight` entry; another one waits (`waits: <id>`), study and pre-brief staying free. It is
released when the runner has returned its last report and the PL has accepted it.

**Between PLs**: a report for another domain becomes a workstream of its module, `status: to-brief`, `for: <PL>`;
**after every `pull`, a PL reads the `for:` entries addressed to it**. The owner no longer relays. A generic lesson is a
workstream `module: method`, `for:` the method session.

**The baton**: each checkpoint carries at the top `Session active: <short id>, since <time>` (or “none — free since
<time>”). **The short id is the last eight characters of the session's identifier**, the one in the session attribution
line of its commits: it was defined nowhere, three forms coexisted, and all the sessions of one account share the same
beginning of identifier — which can mislead the arbiter looking for the baton in the commits. The resuming session sets
it by a push, its first move; a session that finds another id than its own after a
`pull` stops writing to the living docs and tells the owner; a session waiting for the owner keeps the baton. **A baton
is judged by its silence, not by its age**: a session can live several days waiting for the owner; it is the absence
of any commit from that session for more than 24 hours that signals a forgotten session (the arbiter's check, if there
is one). **The coordination is the exception**: it keeps its baton between two pieces of work, because the owner consults
it to reopen a workstream or take a fixed line, and it can stay days without a commit (the arbiter used to flag it as a
forgotten session, wrongly). The baton silence check excludes it; its other checks (checkpoints, size) remain; **it hands
over on the measure of its context (§6), not on silence**.

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
     conditions, which take precedence over the brief; the stops; their final answer. **The standing conditions are in
     the dev prompt** (repositories already attached; clones in `/home/claude/dev_<batch>/`, never at the paths of the
     PL's copies; push to the batch's branches only; no process left running in the background): **the command only
     repeats what changes from one batch to the next**. While the dev works, **the PL does not touch the paths it
     occupies**. **The dev talks only to the PL.**
   - **Fallback**: if the PL cannot launch a sub-agent, they give the owner a line to paste word for word, with above
     it “**Sonnet · Medium · new conversation**” (model, effort, session); the dev prompt then tells the dev to tell the
     owner only, in one sentence, when it stops or delivers.
   - **Safeguard**: a sub-agent consumes the credit of the PL's session; the handover is always measured.
3. **A dev stop**: the dev pushes their branch and the reason (`STOP_<n>.md`). The PL reads it in the repository,
   pushes `ADDENDUM_<n>.md` on the same branch and relaunches the dev **by message** (the same sub-agent if it can be
   reached, otherwise a new one, which also reads the previous stops and reports). **An addendum never reopens a batch
   handed over to the owner** (step 6).
   - **A mock-up requested from the dev goes through a stop**: it renders, pushes the images and
     `batches/v<X.Y>/MOCKUP_<n>.md` (one line per image, the fingerprint of the rendered code) to the brief's branch, and
     stops. **The PL looks at the images, shows them to the owner, then relaunches the same sub-agent by message with the
     owner's verdict, word for word.** A requested change that stays within the brief makes a new round
     (`MOCKUP_<n+1>.md`); a change that would touch what the brief says is immovable goes back through the brief.
     Once validated, the mock-up fixes the code's fingerprint: the dev touches it no more, not a line. *(The dev prompt
     still told the dev to show the mock-up to the owner: every launch had to correct it by hand.)*
4. **The delivery**: the delivery commit, then `DEV_REPORT.md` in a separate commit.
5. **The acceptance** (§4), then the verdict to the owner, with the prediction for production, and **the deliverable
   handed over as is**, under its exact name, with its sha256 — ⟨with a server runner: **deployed by an order** (§4a),
   the hand-over becoming the fallback⟩.
6. **One delivery = one new number.** Whatever is handed over to the owner or deployed carries a version never handed
   over before. A fix or trial feedback after a hand-over makes **a batch of the next version**, which keeps the
   deliverable, on its own branch started from the batch's branch, in the same dev session if it is still open.
   **An addendum under the same version only serves while nothing has been handed over or deployed**: lifting a stop,
   correcting a gap found at acceptance.
7. **Validation in production by the owner**, then **the merge**: `git push origin batch/v<X.Y>:main` as a
   fast-forward, never `--force`; finally **the close-out** (§6), once per batch. *(For a deliverable published by
   release, there is neither a version nor a validation in production per batch: the merge happens after acceptance, and
   the release at the owner's request — §1a.)*

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
  never in a reduced page. These images are rendered by the dev, through a stop (§2, step 3).
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
   to deploy (an HTML page) is handed over **outside a zip**. ⟨With a server runner: the archive is still produced and
   kept; **the order names the accepted commit** (and the sha256 for a static file); the hand-over becomes the fallback
   (§4a).⟩
8. **The verdict**: compliant, or a fix (next version). **A justified dev stop is never a reproach**: execution is
   often right against the brief.

---

## §4a · Deployment ⟨optional: project with a production server and a server runner⟩

*No production server administered by the owner: delete this section; the deliverable is handed over (§4, step 7). The
guide and the reference implementation: `templates/SERVER_RUNNER.md` and `templates/server-runner/` of the package.*

**The principle**: a deterministic program on the server (⟨its name in this project⟩) pulls the orders from the orders
repository every minute, runs only a whitelist of actions and pushes its report there. **No AI in the deployment
path**; an agent on a production server, if there is one, is bounded (no secrets, no database writes, no root).

**The circuit, after an acceptance with no gap**:
1. **An application that has users**: the PL asks the owner for **a “go” that names the action** (“go deployment
   v<X.Y>”) and quotes it in the order's `go` field. **Static files with instant rollback** (a self-contained HTML
   page): direct deployment, no go.
2. They push `ordres/<id>.json`; the identifier `YYYY-MM-DD-NN` is **the next one in the repository, taken by the push**
   (push refused → `pull`, next number). **An order is never written onto a file that exists**: the identifier is read
   **after** `git pull`, never from a list read before; the write refuses to overwrite (`set -o noclobber` before
   `cat >`, or an `[ -e ordres/<id>.json ]` test that stops everything); before the push,
   `git diff --cached --name-status` shows only **one line `A ordres/<id>.json`** — an `M` stops everything. An order
   is never rewritten: to correct, a new order. *(A lesson learned the hard way: a session took an identifier from a list read before its
   `pull` and overwrote, by `cat >`, the already-played order of another session; the push refused nothing — a
   modification, not an addition.)*
3. They read `resultats/<id>.md` with a **bounded wait** (one to two minutes normally), never an endless loop.
4. They tell the owner the version served, the health, the backup taken, the counts before and after; the owner
   validates on screen; **then** the merge into `main` (§2, step 7).
5. **Rollback**: `revenir` — on go for the application, refused after a migration; without go for a static file.
   **File operations**: action `fichiers`, within the zones declared on the server; emptying the trash on go.
6. **A failed report**: the PL says so, with the backup's name; a stopped queue only reopens on the owner's decision.
   **Never a database restore by the server runner**: manual procedure ⟨where it is written⟩.

**The fallback**: the server runner down, the deliverable is handed to the owner as is (§4, step 7) and the manual
procedure applies. **Each PL who deploys attaches the orders repository with write access; the dev never reads or
writes it.**

**How data gets onto the server** (a package of rendered pages, tiles, maps — the orders repository is also the
**file-exchange bridge**):
- **Produced in a session**: the PL who produces it pushes it to the orders repository under
  `transfers/<domain>/<edition>/` (**never the dev**; **a file of 95 MiB at most**, the host refuses anything beyond
  100 MB; larger: split, or another route); then a `fichiers` order: `telecharger` **from the orders repository, at the
  40-hex commit, sha256 mandatory**, `decompresser` into a new folder, `basculer` — **the PL tells the owner before
  replacing what is served**. Once the report has succeeded, it **removes the folder from the tree** by a commit (the
  history keeps it; a partial copy at the commit reads only what is needed).
- **Produced on the owner's PC** (captures, large backgrounds): `rsync` into `entree/` (`SERVER_RUNNER.md` §4), then a
  `fichiers` order.
- **Published elsewhere** (a release, a known public repository, an authorized host): `telecharger`, as for any file.
- **Never the history of a public code repository**: every edition would stay there forever and weigh down every clone.
- *Points of attention*: the runner keeps a clone of the orders repository up to date every minute — if it is complete,
  the files pushed then removed stay in its history: the defence (partial copy, or `transfers/` outside the orders clone)
  is decided **at set-up** ⟨and noted here⟩; reading a file at a commit is a private source of `telecharger` that the
  reference implementation does not have yet (`SERVER_RUNNER.md` §13). The why, and the step by step: `SERVER_RUNNER.md`
  §3 point 9 and §5.

⟨What is specific to the project: the actions in service, the static files and the zones, the counted tables, the
manual procedure, the date it went into service.⟩

---

## §5 · What is unforgiving

- **Nothing is believed, everything is measured**, on the archive unpacked cold. The gates are read as deltas.
- **The version**: ⟨who bumps it — `release` script on the dev side, pre-authorized, +1 step per batch / only with
  the owner's explicit agreement⟩. A batch that does not change the code (method, test bench) takes no version, nor
  does a batch of a deliverable published by release (§1a, “The deliverable and its version”).
- ⟨The project's invariants: a file, a module or a fingerprint that only move on the owner's written authorization
  carried by the brief.⟩
- **Produced texts remain gender-neutral**: never presume a person's gender from a pseudonym.
- ⟨With a server runner: never an application order without the owner's go naming the action; never an action
  outside the whitelist; an order is never rewritten; neither secret nor production data in an order or in the orders
  repository; the data invariants (`SERVER_RUNNER.md` §8).⟩
- ⟨Public code: the dev prompt and `batches/` in the private batches repository, never in the public one; zero
  private reference in the pushed diff (first name, profile, method, decision log) — a pushed file stays in the
  public history.⟩
- **The “execution is right” count** is kept in the decision log: each justified stop or report from the dev is
  added to it. A PL defect seen in production opens the reverse count.

---

## §6 · Close-out and the documents

**At each closed batch, once**:
- the plan's version log line, for a batch that takes a version (a deliverable deployed per batch); **for a deliverable
  published by release, the batch takes no version**: it completes the “Unreleased” section of the `CHANGELOG` and frees
  the deliverable at its merge, after acceptance (§1a);
- the decision log (the decision, and “what the batch teaches” when there is a lesson);
- `workstreams.yaml`, **then the board's page and data file regenerated** (below);
- **a commit “Batch v<X.Y> closed”** in the living-docs repository, then **the mirror in the project**;
- the checkpoint **of the domain**, at handover, **its queue re-read against `workstreams.yaml`** (below).

Two batches accepted the same day can be closed together.

**The living docs**:
- live in the living-docs repository **under stable names**; the version is in the header, the history in git;
- are modified by targeted replacements, or replaced in full while removing what is obsolete;
- **stay short**, under caps (below): when one grows long again, what no longer lives goes into a **new archive**
  (`Archives/<NAME>_ARCHIVE_<range>.md`), frozen, never rewritten; for `workstreams.yaml`, the archiving is automatic
  (below) and `search` finds an entry;
- **the project carries a mirror of them**, copied at each close-out by `project_write` with `local_path` from the
  clone; **never from the text served by the project tool**.

**The caps** — *every PL re-reads everything at every resume, and the messages between PLs piled up in the entries: on the
first project, a workstreams file went from 95 to 146 KB in one day, a decision log reached 206 KB, a checkpoint 47 KB*:
- **a workstream entry fits in ~1.5 KB**: the state, the decision, the next move; a long exchange goes to the batch
  folder or into a domain note, the entry only keeps the summary and the path;
- **a decision log entry fits in ~800 characters**;
- **a workstream accepted leaves for the archive seven days later** (below);
- **the decision log is cut into slices of fifty numbers** when it exceeds ~150 KB: one frozen archive per slice
  (`Archives/DECISION_LOG_ARCHIVE_D<a>_to_D<b>.md`), and the “execution is right” counts are carried over into a base at
  the cut (§1a of the log);
- **a checkpoint fits in 10 KB** (10,240 bytes): the fixed line, the baton, the state, the queue, what is needed to
  resume; the history goes to a domain archive (`<Folder>/Archives/CHECKPOINT_<DOMAIN>_ARCHIVE_<date>.md`). **Check 10**
  of `check_living_docs.py --domains` flags it (cap adjustable with `--checkpoint-cap`); the arbiter, if there is one,
  turns it into **one workstream per domain**, without filing a new one when its message already exists; without an
  arbiter, the coordinator runs the checker at their close-out.

**Accepted workstreams — the archiving**:
- at close-out, the entry goes to `status: accepted`, then **is no longer touched by hand**: the line
  `accepted-on: <date>` is set by `archive_workstreams.py` (it is neither written nor corrected by hand), and removed by
  it from a reopened entry;
- an entry accepted for seven days moves out to `<Folder>/Archives/WORKSTREAMS_<YYYY-MM>.yaml` (the month of the run;
  things are only appended to it, frozen at the end of the month); the script checks that nothing is lost before
  writing;
- **who archives**: the arbiter, if there is one, at every run (`Method/ARBITER.md` §1.4a); **without an arbiter**, the
  PL or the coordinator runs, at their close-out,
  `python3 -B <Folder>/archive_workstreams.py archive --workstreams <Folder>/workstreams.yaml --archives <Folder>/Archives`
  (without `--delay`: the default delay is seven days), then regenerates the board and commits;
- **an archived id is not reused**;
- the checker is run with `--archives <Folder>/Archives`: an id both living and archived is a gap, and the last version
  of the log is also looked for in the archives.

**A checkpoint's queue — registered workstreams only**:
- **Every upcoming or to-brief subject, every debt or idea kept, first has its entry in `workstreams.yaml`**
  (`status: upcoming`, `to-brief` or `debt`), and **the checkpoint cites it by its id, between backticks**. The owner
  only reads the board (`workstreams.html`): a subject that lives only in a checkpoint exists neither for them, nor for
  the other PLs, nor for the arbiter — it gets lost, or it is still announced when it is finished.
- **At every resume and every handover**, the PL re-reads their queue against `workstreams.yaml`: they **register what
  is missing** (then cite it) and **remove from the queue what is closed** (accepted or archived) — a closed workstream
  is no longer announced.
- **Every checkpoint has its `## §<n> · The queue` section, which carries the list itself** — never a pointer
  (“everything is in §0”), which the check cannot read: two domains escaped it, one through a section that only carried
  a pointer, the other for want of declaring one. **The title is stable**: the exact start of that title is what `queue:`
  carries in the domain table (`Method/domains.yaml`, kept by the coordinator in step with the table of §1a); **a PL that
  renames this title changes, in the same commit, the `queue:` line of its domain**; an empty `queue:` is a gap of the
  domain.
- **Who checks**: check 9 of `check_living_docs.py --domains Method/domains.yaml` reports the queue that cites a closed
  workstream, every open workstream of the domain that its checkpoint does not cite, and a domain with no declared queue
  section; the arbiter, if there is one,
  runs it at every run and, **on Mondays, re-reads the checkpoints against the week's decisions** (`Method/ARBITER.md`
  §1.4b); **without an arbiter**, the coordinator runs the checker with `--domains` at their close-out.

**The workstreams board** — the readable page of `workstreams.yaml`: **a fixed page and its data file**:
- `make_board.py` writes `workstreams.html`, **a fixed page of about 11 KB, with no workstream data at all**, and
  `workstreams.json` next to it (same name); the page reads its data in that file. The command line is
  `python3 -B <Folder>/make_board.py <Folder>/workstreams.yaml <Folder>/workstreams.html`. **Check 6** of
  `check_living_docs.py` compares both files with their regeneration. A page opened from the disk does not load its
  data: it is served or published.
- **Every time the PL writes `workstreams.yaml`** — at close-out, but also mid-exchange (a workstream added, a
  status that changes) —, they regenerate both files in the same move. A `workstreams.yaml` modified without its two
  files is not finished. They commit them together in the living-docs repository and copy them to the project as a
  mirror.
- **Before republishing**:
  - **regenerate after the last `git pull` / rebase, never before** (a real case: a data file pulled before the base
    missed three workstreams of another session; check 6 saw it); **the checker passes, check 6 OK** — it is what
    guarantees the data, not a reading;
  - **the PL reads the page in full** (the artifact tool requires it; a reading “by file” does not count), about 4,000
    tokens;
  - **they re-read the diff of their own writes** in `workstreams.yaml` since their last publication.
- **They republish the page and the data file together, at the same link** (the link is recorded in §6 of the
  checkpoint), even if only the data changed, and hand the page over as an `.html` file in the conversation.
- *Why not the whole data file every time*: the tool's rule is not to distribute what one has not seen. Here the file is
  produced by the generator from a yaml that only PL sessions write: every line was seen by the session that wrote it, and
  the session that publishes re-reads its own writes. **The data file is re-read in full, by a light subagent (Haiku)**,
  in two cases only: the first publication of a board, and an entry drawn from an outside source (pasted text, a web
  page) that no session has re-read. **It is also the fallback**: if the tool were to require reading every published
  file, we go back to that subagent for every republication.
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
| `<Folder>/` | the plan, the decision log, `workstreams.yaml`, `workstreams.html` and `workstreams.json`, `make_board.py`, the checkpoint, the reference notes |
| `<Folder>/Archives/` | the frozen archives |
| `<Folder>/Specs/` · `<Folder>/StyleGuide/` | the product references |
| ⟨`<SubProject>/`⟩ | ⟨one folder per sub-project⟩ |

**What is still uploaded** into the session that needs it: production data, which go into no repository. **No more
handover prompt** (the handover, below). **Images** go through the conversation, never through the project files.

**The handover is measured, not guessed**:
- **What is measured**: the context size at the last turn, with `python3 -B <Folder>/pl_tools/context.py` (copied
  from the package). It is not the cumulative consumption since the start of the session, which grows much faster.
- **Why these thresholds**: every turn re-reads the whole context, cache included. The bigger it is, the more each turn
  costs and the more quality drops.
- **When**: at each batch close-out, before each brief or dev launch, and at least every ten exchanges.
- **At 450,000 tokens, the PL warns the owner**, at the top of their answer: “Context: ~N tokens — handover ahead”.
  They no longer launch a new batch; they finish the one in progress.
- **At 550,000 tokens at the latest**, or at a natural end of a queue before that, or at the first sign of saturation,
  **they hand over**, without waiting to be asked, in one go, in a single answer:
  1. §0 of the domain's checkpoint rewritten on the real state (where things stand, what blocks, what awaits the owner),
     **its queue re-read against `workstreams.yaml`** (what is missing gets registered, what is closed leaves), **the
     saturation signs seen during the session noted (or “none”)**, and the fixed line at the top checked: it names **all
     the domain's repositories** (§7);
  2. the baton set back to “none — free since <time>”;
  3. push, then the mirror in the project;
  4. **the domain's fixed line**, under “**Opus · new conversation in the project**”: “You are <PL>. Resume: attach
     with push access the repositories <owner> <domain repositories> (one clone at a time), git pull in <living-docs
     repository>, read `<domain checkpoint>` in full (§0 first) and follow it.” — each domain's exact line is in the
     living-docs README and at the top of its checkpoint.
- **Nothing travels outside the repository**: no handover prompt, no “next number”, no upcoming version in a text handed
  to the owner — a text that copies the state ages while the other PLs move on.
- **The resume can be started by the session itself**: a one-off scheduled task whose prompt is the fixed line; the
  owner opens the session in their task list. When the owner is not there to open it, the fixed line is enough.
- **At the first sign of saturation** before the threshold (losing the thread, contradictions, a forgotten decision):
  same handover, right away. **Every handover notes the signs seen, or “none”**: these notes serve to recalibrate the
  thresholds on measurements, not on an impression.
- The context of a sub-agent (the dev, or a delegated reading) does not count in the PL's; its credit does.

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
- **A workstream not found in `workstreams.yaml` may be archived**: look for it with
  `python3 -B <Folder>/archive_workstreams.py search <id or word> --workstreams <Folder>/workstreams.yaml --archives <Folder>/Archives`
  (`--everywhere`: in all the values), never by recreating the entry.
- ⟨With a server runner: attach the orders repository with write access at the start of the session; re-read
  `resultats/` with a bounded wait, never an endless loop.⟩

**Git and GitHub**: see `3_GITHUB.md` §5 of the package — tags, releases and branch deletions by the owner; clone of
a single branch; attribution lines; no secrets. **A domain's fixed line names all its repositories**, with push
access: a session's safeguard refuses an attachment the owner has not asked for in so many words, and the line they
paste stands for that request. One more repository along the way: the session asks the owner for it in a ready line
(“tell me “attach X””).

⟨**Specific to the project, common to all its domains**: to be completed batch after batch — each trap paid for once is
written here. A trap that touches only one product goes to its product sheet or to the checkpoint of its domain (at the
top of this method).⟩

---

## §8 · The target cost

- **An ordinary batch**: ten to twenty minutes of dev, an acceptance of a few minutes.
- **A screen with a PL mock-up**: from 15 minutes to 1 h 30 of dev; the mock-up validated in one or two rounds.
- **An addendum launched by the PL**: a few minutes, without a move from the owner.
- **The PL records their own cost** at each handover: measured context, saturation signs seen, main items.

---

*Written by <session> on <date>, at the project's bootstrap (D1), from the PL method package v<n>.*
