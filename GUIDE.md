# PL METHOD PACKAGE · v19
### 31 October 2026 · to start a new project under the PL method

*This package reproduces a way of working proven batch after batch: a **project lead** (PL, Opus) who decides
with you, writes the briefs, launches the dev and accepts; a **dev** who builds one batch at a time;
**you**, who decide and validate on screen. Everything flows through GitHub; you upload nothing and run no command.*

**Where to start**: if you start alone with a PL, first read **[`CORE.md`](CORE.md)** — it is enough to start, with at the
end the table of extensions (what you install only the day the sign you have lived through occurs). The rest of this
guide adds to the core, it does not come before it. **The terms** of the method are in **[`GLOSSARY.md`](GLOSSARY.md)**; **what the
method assumes of the Claude product**, and the fallback when a function changes, in **[`CLAUDE_DEPENDENCIES.md`](CLAUDE_DEPENDENCIES.md)**. **The
method has been proven on three projects, one of them complex** (several PLs in parallel on several products, a
production server).

**The owner**, in the templates and the skill, is you: the person who decides and validates. What is between `<…>` or
`⟨…⟩` is to be filled in — the PL does it at bootstrap, except for the skill, which you customize yourself (§1 and §8).

---

## 1 · What is in the package

| file | used for | where it ends up |
|---|---|---|
| `GUIDE.md` | these instructions for use | nowhere, it is for you |
| `CORE.md` | **to read first**: the method of an owner alone with a PL (mode A), enough to start — roles, layers and moves to start, the cycle of a batch, checkpoint and handover, what does not forgive — and the table of extensions | nowhere, it is for you |
| `GLOSSARY.md` | every term of the method, one or two lines and the document where it lives | nowhere, it is for you |
| `CLAUDE_DEPENDENCIES.md` | what the method assumes of the Claude product, what breaks if a function changes, the fallback; **a dated survey, to be re-read at every version** | nowhere, it is for you |
| [`1_PROJECT_INSTRUCTIONS.md`](1_PROJECT_INSTRUCTIONS.md) | the text to paste into **the claude.ai project instructions** | project instructions |
| [`2_PL_BOOTSTRAP_PROMPT.md`](2_PL_BOOTSTRAP_PROMPT.md) | the **first message** of the first PL session; §D, the one that opens the coordination | pasted into a conversation |
| [`3_GITHUB.md`](3_GITHUB.md) | the repositories, their structure, the circuit of a batch, the pitfalls | read by the PL when a question requires it |
| [`templates/METHOD.md`](templates/METHOD.md) | the generic method, to adapt; **the only source of the method's figures** (§6) | `Method/METHOD_<P>.md` in the living-docs repository |
| [`templates/DEV_PROMPT.md`](templates/DEV_PROMPT.md) | the dev's standing command | root of the code repository |
| [`templates/BRIEF.md`](templates/BRIEF.md) | the template of a batch brief, and its short form for a low-complexity batch | used by the PL, **never cited** by a brief |
| [`templates/BATCH_FILES.md`](templates/BATCH_FILES.md) | addendum, stop, dev report | used by the PL and the dev |
| [`templates/DEV_COMMAND.md`](templates/DEV_COMMAND.md) | the command of the dev sub-agent, and the fallback line | used by the PL |
| [`templates/CHECKPOINT.md`](templates/CHECKPOINT.md) | the current state, entry point of every session | living-docs repository |
| [`templates/DECISION_LOG.md`](templates/DECISION_LOG.md) | the decisions, numbered D1, D2… | living-docs repository |
| [`templates/PLAN.md`](templates/PLAN.md) | the roadmap, and the version log: the only source of a batch's facts | living-docs repository |
| `templates/workstreams.yaml` | the single source of the workstreams | living-docs repository |
| `templates/context.py` | measures the context of the PL session, to decide the handover (thresholds: method §6) | `pl_tools/` in the living-docs repository |
| `templates/make_board.py` | **“published board” extension** — the page `workstreams.html` and its data file `workstreams.json` | living-docs repository |
| `templates/check_living_docs.py` | read-only check of the living docs — eleven checks, described in its docstring | living-docs repository |
| `templates/archive_workstreams.py` | moves the accepted workstreams out to the month's archive (delay: method §6); `search`, `normalize` | living-docs repository |
| `templates/domains.yaml` | **modes B and C** — the domain table that check 9 reads | `Method/domains.yaml` in the living-docs repository |
| [`templates/ARBITER.md`](templates/ARBITER.md), `templates/arbiter.py`, `templates/living-docs-repo/arbiter.yml` | **optional, mode C** — the living-docs arbiter, a daily GitHub Action | `Method/` and `.github/workflows/` in the living-docs repository |
| [`templates/CONTROLLER.md`](templates/CONTROLLER.md) | **optional, mode C** — the controller, a weekly session that judges the form of the documents | `Method/CONTROLLER.md` in the living-docs repository |
| [`templates/LOCAL_RUNNER.md`](templates/LOCAL_RUNNER.md) | **the fallback** — the local runner on the PC, when the bridge does not give your machine | used by the PL and the runner |
| [`templates/SERVER_RUNNER.md`](templates/SERVER_RUNNER.md) | **optional** — the server runner and the orders repository (§2c). **No production server: skip it** | used by the PL, and by you at installation |
| `templates/server-runner/` | **optional** — its reference implementation (Python, systemd, installer, tests), in French | the project's code repository, then the server |
| `templates/living-docs-repo/` | [`README.md`](templates/living-docs-repo/README.md) of the living-docs repository | living-docs repository |
| `templates/code-repo/` | `.gitattributes`, `.gitignore`, [`CHANGELOG.md`](templates/code-repo/CHANGELOG.md) of the code repository | code repository |
| [`skill/SKILL.md`](skill/SKILL.md) | the personal skill `methode-cdp`, **to customize (§1 and §8) then install** — **v19**: what a session knows before reading the project's method | your claude.ai skills |
| `fr/` | the same package in French | the same places as its English counterpart |

**The tooling**: the scripts use only Python's standard library and are tested in CI. Two tests guard the documents:
`templates/tests/test_links.py` (every relative link leads to a file that exists) and `templates/tests/test_parity.py`
(each figure of the method is written only at its source, and each French document has the same headings as its English
counterpart).

---

## 2 · The architecture: three layers, from the most general to the most precise

```
┌──────────────────────────────────────────────────────────────────────────┐
│ 1. PERSONAL SKILL  methode-cdp           (your account, all projects)    │
│    Who you are, the roles, the posture, how a session starts.            │
│    → Rarely changes. Updated when the method evolves.                    │
├──────────────────────────────────────────────────────────────────────────┤
│ 2. PROJECT INSTRUCTIONS                  (one claude.ai project)         │
│    Your profile for this project, what you expect, WHERE the living      │
│    docs are, WHICH repositories. About ten lines, pointers, no rules.    │
│    → Changes when a repository or a reference document is renamed.       │
├──────────────────────────────────────────────────────────────────────────┤
│ 3. LIVING DOCUMENTS + REPOSITORIES       (the project itself)            │
│    METHOD_<P> (overrides the skill), CHECKPOINT, DECISION_LOG, PLAN,     │
│    workstreams.yaml; code, DEV_PROMPT_<P> and batches/ in code repo.     │
│    → Changes at every closed batch, by the PL alone.                     │
└──────────────────────────────────────────────────────────────────────────┘
```

**Precedence rule**: your decisions in the decision log override everything; the project's method overrides the skill; for
a dev, the practical conditions of its command override the brief and the dev prompt, and the brief overrides the prompt
for what the batch does.

**Why three layers**: the skill spares you from re-explaining the collaboration for each project; the instructions stay
short so they do not drift; the living docs carry what moves, under stable names, versioned by git.

**What does not go into Claude's memory**: the method and the state of the project. Memory keeps facts about you;
it does not replace a versioned document that a fresh dev can read.

---

## 2a · Three ways to organize

```
A · ONE PL          B · INDEPENDENT MODULES      C · LINKED MODULES
owner               owner                        owner
   │                   │                            │
  PL ── dev         ┌──┴─────┐                Coordinator ── method,
   │               PL-1    PL-2                     │      domains, arbiter
living docs        (each its own dev)         ┌─────┼─────┐
+ code                 │       │             PL-a   PL-b   PL-c
                    shared living docs,      shared living docs;
                    append-only,             common deliverables,
                    one checkpoint each;     resources and files
                    separate code, releases
```

**A — one project, one PL**: an application with a single module. One checkpoint, one baton, no sharing rule to
apply; the PL also keeps the method and the package. The simplest: stay there as long as only one domain moves at a
time.

**B — several independent modules, one PL each**: for example a web application and two standalone tools, each with its
own code repository and release. One checkpoint and one baton per domain; the shared living docs append-only (decision
log, plan, workstreams); the decision number taken by a push; no common deliverable, so no waiting between them; the
rare messages from one domain to another go through a `for:` workstream. **Without a coordination, the method, the dev prompt
and the living-docs README keep a single owner**: the first PL, or a coordinator as soon as the project grows.

**C — several linked modules, one PL per domain and a coordinator**: modules that share a deliverable (the same
application), a resource (your machine), files or a server. Everything in B, plus: a single batch in flight per
deliverable and per resource (taken by the push of the in-flight entry; the other batch `waits:`, the study and the
pre-brief stay free); `touches:` for a file of another domain; **the coordination session** opens and closes the
domains, gives the fixed lines, keeps the method, the dev prompt, the package, the living-docs tooling, the arbiter and the
controller (if they exist); a product sheet when a product has several module PLs.

**Moving from one mode to another**: you start in A; you move to B when a second independent module starts; to C as soon
as two PLs share a deliverable, a resource or files, or a cross-cutting change appears. Nothing is migrated: you add a
checkpoint, a line to the domain table, and the coordinator. **Starting with several PLs: §3a; moving from one mode to
another along the way (A → B, B → C, A → C, and back): §3b.**

**The living-docs arbiter and controller**: two guards, useless in A, optional in B, recommended in C. The arbiter is a
daily GitHub Action that measures; the controller, a weekly session that judges (§2b). **Who archives** the accepted
workstreams: the arbiter, if there is one; without it (modes A and B), the PL or the coordinator runs
`archive_workstreams.py` at their close-out.

**Three things the method fixes so that the tools find their way.** *The baton*: a session's short id is the last eight
characters of its session identifier (the one in the attribution line of its commits); all the sessions of one account
share the beginning; a baton is judged by its silence, **except the coordination's**, which you keep open for days
without a commit. *The queue*: each checkpoint carries it under a stable title `## §<n> · The queue`, with the list
itself; the domain table names that title, an empty `queue:` line is a gap, and the coordination has an entry of its own
there. *Your machine*: when the project drives a game or an application on your PC, the PL's session uses it **through
the Claude app's bridge** (linked folders, a terminal if one is offered, the screen, which you validate); the local
runner is only the fallback, and a workstream that needs the machine stays in debt while you are not there.

**How the PLs talk to each other**:

| channel | what it carries | who writes | who reads |
|---|---|---|---|
| workstream `for: <PL>` in `workstreams.yaml` | a report or a request for another domain; a lesson for the method (`for:` the coordinator) | any PL, the arbiter, the controller | the PL addressed, after every `pull` |
| `in-flight` entry (`pl:`, `deliverable:`, `resource:`, `waits:`) | who holds which deliverable or which resource | the PL who takes it, by a push | everyone, before briefing |
| decision log | the decisions, number reserved by a push | the PL who closes | everyone |
| checkpoint baton | who is active on a domain | the session that resumes, by a push | the coordinator, you, the arbiter |
| arbiter's and controller's logs (`Method/ARBITER_LOG.md`, `Method/CONTROLLER_LOG.md`) | one dated line per run, even without a gap: the proof they ran | the arbiter, the controller, append-only | the coordinator, you |
| message ready to paste | a method change that affects an active PL (baton free: a `for:` workstream) | the coordinator | you, who paste it to the PL; the coordinator then checks its reply in the repository |
| **never** | a message you relay from memory, nor a resume text travelling outside the repository | — | — |

In A, none of these channels is needed; in B, the `for:` workstreams and the decision log are enough; in C, all of them.

---

## 2b · The living-docs arbiter and controller

*Two guards, useless in A, optional in B, recommended in C. Their templates answer “why, when, how much, how” on their
own: [`templates/ARBITER.md`](templates/ARBITER.md) §0 and [`templates/CONTROLLER.md`](templates/CONTROLLER.md).*

- **The arbiter measures, every day**: a GitHub Action, with no session, that runs the checker, files one `for:`
  workstream per new gap, archives and keeps its log; it fails when it has filed, and GitHub's e-mail warns you. **Its
  sign**: the first duplicated decision number, or the first forgotten session that keeps a baton.
- **The controller judges, every Monday**: a fresh Opus session, by scheduled task (automatic approval), that returns at
  most five proved findings on the form of the documents. **Its sign**: the first document that swells or contradicts
  itself without anyone saying so.
- **Neither corrects**: the owner corrects.

---

## 2c · The orders repository, the file-exchange bridge

*Only with a server runner ([`templates/SERVER_RUNNER.md`](templates/SERVER_RUNNER.md)): otherwise, skip this section.
The detail — the circuit, the limits, the why — is in the server runner's guide, §3 point 9, §5, §12 and §13.*

**The sign**: data produced in a session (a package of rendered pages, tiles) must reach the server, and you do not want
to drop it by hand. **The rule**: the orders repository also serves as the bridge, through a `transfers/` folder — no
extra repository or key; never the history of a public code repository.

| the data is… | it arrives through | state |
|---|---|---|
| **produced in a session** | `transfers/<domain>/<edition>/` of the orders repository, then a `fichiers` order | **coming** (`SERVER_RUNNER.md` §13) |
| **produced on your PC** | `rsync` into the server's `entree/`, then a `fichiers` order | in service |
| **published elsewhere** | a `fichiers` order: `telecharger` | in service |

The dev never reads or writes that repository; the PL keeps a clone of it only while deploying (`templates/METHOD.md` §4a).

---

## 3 · Starting a new project — your actions, in order

**Your moves are in [`CORE.md`](CORE.md) §2**: the empty repositories to create and protect, the project instructions,
the skill to customize, the bootstrap prompt. What adds to them:
- **the code is public**: also create `<Project>-Batches`, private ([`3_GITHUB.md`](3_GITHUB.md) §6 B); **on a free
  account**, what the protection of `main` becomes: `3_GITHUB.md` §5;
- **the package within reach of the first session**: the PL reads it directly from the public repository
  `MirabelleBenou/methode-cdp` (at the root), read-only — nothing to upload; or you attach the zip to the first
  conversation.

From then on, you talk only to the PL. Your only remaining manual actions: **validate on screen**, set **the tags and
releases**, **delete the merged branches** on GitHub (a session cannot), and drop the deliverable where it is
deployed — unless the project has a server runner: you then say “go” naming the action, the PL deploys.

## 3a · Several PLs — starting in B or C, or moving there

*§3 starts a project with a single PL (mode A, §2a). A project with several modules starts the same way, then the
domains are added one by one: nothing is migrated, things are added.*

**Your actions, in order:**

1. **Start in A (§3) with the first module**, even if you already know there will be several. Tell the first PL at
   bootstrap (“other modules will come: <which>”): it names its domain and its checkpoint accordingly
   (`Opus-PL-<Product>[-<Module>]`, `<Folder>/CHECKPOINT_<…>.md`) and opens the domain table (method §1a, living-docs
   README). The shared living docs — method, decision log, plan, `workstreams.yaml` — then serve everyone.
2. **For each additional module (mode B)**:
   - on GitHub, create its empty code repository (`<Project>-<Module>`, private or public) — **no second batches
     repository**: a suite keeps a single `-Batches`, each batch carrying a module prefix there (`3_GITHUB.md`);
   - ask the PL in place — or the coordination, if it exists — “open the <module> domain”: it bootstraps the domain's
     checkpoint, adds its line to the domain table and gives you **the fixed line** of the new PL (it names all its
     repositories);
   - open a new conversation with Opus, **in the same claude.ai project**, paste that fixed line, and title the
     conversation `<PL name> · <workstream>`;
   - replace the project instructions with the text the PL gives you back (the new checkpoint is named in it).
3. **When the modules touch each other (mode C)** — two PLs share a deliverable, your machine, files or a server, or a
   change touches every domain — **open the coordination**: a new conversation with Opus, the prompt
   `2_PL_BOOTSTRAP_PROMPT.md` §D. The coordination session takes over the method, the dev prompt, the living-docs README
   and the package; it creates its checkpoint, keeps the domain table (including `Method/domains.yaml`) and gives you
   back the project instructions in their several-PL version (`1_PROJECT_INSTRUCTIONS.md`).
4. **In C, install the arbiter and the controller** (recommended, §2b): the coordination prepares them and proposes them to
   you; you leave GitHub's notifications for a failed workflow active and you approve the controller's scheduled task
   (automatic approval).

**Then, day to day:**
- **one conversation per domain**, titled `<PL name> · <current workstream>`; you talk to each PL in its own, about its
  domain only;
- **resuming a PL**: a new conversation and its domain's fixed line (living-docs README), if its baton is free; if it
  is taken, the previous session is still alive: go back to it instead;
- **to the coordination**: opening or closing a domain, putting two PLs on the same product, a cross-cutting subject, a
  doubt, a method question;
- **you never relay a message from one PL to another**: they write to each other through `for:` workstreams (§2a);
- **you read only the workstreams board**: every subject of a domain has its entry there (method §6), and the arbiter
  checks it every morning.

## 3b · Moving from one mode to another, as the project grows (or shrinks)

*A project almost always starts in A and grows more complex over time. **Nothing is migrated: things are added** — a
checkpoint, a line in the domain table, a coordinator. The living docs, the decision numbers, the history and the
workstreams stay where they are. A move happens **between two batches**, never with a batch in flight, and is recorded
in the decision log as a decision.*

**The signs that it is time:**

| move | when |
|---|---|
| **A → B** | a second **independent** module starts (its own code repository, its own release, nothing in common with the first); or you want two subjects to move forward in two conversations at the same time |
| **B → C** | two PLs share something: **a deliverable** (the same application), **a resource** (your machine, a game, a server), **files**; or a change touches every domain (the method, the deployment); or you catch yourself **relaying a message** from one PL to another; or decision numbers come out duplicated |
| **A → C** directly | from the start of the second module, it shares a deliverable, a resource or a server with the first (for example a second module **inside the same application**) |
| **C → B → A** (back) | a domain is finished or has been dormant for a long time; only one or two active PLs remain, with nothing in common |

**A → B — your actions:**
1. In the conversation of the PL in place: “the project moves to B: a second module, <which>”. It reserves a decision
   number and records the move.
2. On GitHub, create the module's code repository; if it is public and no `-Batches` exists yet, also create
   `<Project>-Batches` (private) — a single one for the whole suite.
3. The PL opens the domain (§3a, point 2) and gives you the new PL's fixed line; you paste it into a new conversation
   of the same project.
4. You replace the project instructions with the text it gives you back (several-PL version).

**A → B — what the session does:** its domain takes a name (`Opus-PL-<Product>`) and a checkpoint of its own, with its
baton; the domain table is born (method §1a, living-docs README with each PL's fixed line); the sharing rules apply from
now on (method §1a: append only, numbers reserved by a push, messages through `for:` workstreams, module prefix in the
batch names); the project's method changes version; the first PL **remains the owner of the method** as long as there
is no coordination.

**B → C (or A → C) — your actions:**
1. Open the coordination: a new conversation, the prompt `2_PL_BOOTSTRAP_PROMPT.md` §D, listing the domains in
   activity in it (in A → C: the single existing domain).
2. Tell the PL that held the method, in its conversation: “the coordination is open, it takes over the method”.
3. In A → C: then ask the coordination to open the second domain (you tell it which; it gives you its fixed line).
4. Answer its proposals (product sheet, arbiter) and paste the instructions it gives you back.

**B → C — what the coordination session does:** it takes over the method, the dev prompt, the living-docs README and
the package (the PL that held them leaves them to it); it creates its checkpoint; it keeps the domain table in three
places (method §1a, README, `Method/domains.yaml`); the mode C rules enter the method (one deliverable, a single batch
in flight; a resource taken like a deliverable; `waits:`, `touches:`; the product sheet of a product with several
PLs); it proposes the arbiter; it notifies each active PL by a ready-to-paste message, which you hand to it, and then checks
its reply in the repository; a PL whose baton is free finds it through a `for:` workstream when it resumes (method §1a).

**Going back, when a domain closes:** ask the coordination (or, in B, the PL that holds the method) “close the <name>
domain”. It marks the checkpoint “closed” (it stays as a reference), removes the domain from the table in the three
places, **attaches its open workstreams to a living domain** (through a `for:` workstream to its PL) and records the
decision. When only one active PL remains and nothing is shared, the coordination can close in turn: the method goes
back to the last PL, the arbiter stops (or continues, if it still helps), you go back to the single-PL instructions.

**What never moves, whatever the move**: the living-docs repository and its files; the decision numbers (the sequence
continues); the workstreams (at most they change domain); the code repositories; the skill — it points
to the project's method, which carries the mode's rules.

---

## 4 · What goes where

*The “mirror” column holds only with the extension of the mirror in the project ([`CORE.md`](CORE.md) §6).*

| item | reference location | mirror in the project? | who writes | when |
|---|---|---|---|---|
| Project method | living-docs repository `Method/` | yes | PL | at a version, after a batch that caught it out |
| Dev prompt | root of the code repository — **`<Project>-Batches` repository if the code is public** | yes | PL | at a version |
| Checkpoint (under its cap, method §6; the history in the domain's archive) | living-docs repository | yes | PL | its §0 at every closed batch; completed at the handover |
| Decision log (cap of an entry and cut: method §6) | living-docs repository | yes | PL | at every closed batch |
| Plan + version log (the facts of each batch, written once) | living-docs repository | yes | PL | at every closed batch |
| `workstreams.yaml` ⟨and, with the published board, `workstreams.html` and `workstreams.json`⟩ | living-docs repository | yes ⟨, and the page with its data file as an artifact⟩ | PL | at every write of the yaml; artifact at close only |
| Domain table `Method/domains.yaml` | living-docs repository | yes | coordinator | a domain opened or closed, a queue section renamed |
| `<Folder>/Archives/WORKSTREAMS_<YYYY-MM>.yaml` | living-docs repository | yes | the archiving (`archive_workstreams.py`) | at every arbiter run, otherwise at the PL's close-out |
| Acceptance expected results | living-docs repository `expected/<version>/` | no | PL | at the brief |
| The PL's throwaway scripts | living-docs repository `pl_tools/` | no | PL | as needed |
| Code, test bench, `CHANGELOG` | code repository | no | dev | within a batch |
| Brief, addenda, stops, report, mock-up | code repository `batches/<version>/` — **`<Project>-Batches` repository if the code is public** | **no** | PL (brief, addenda), dev (stops, report, `MOCKUP_<n>.md`, one line per image with its fingerprint) | during the batch |
| Specs, style guide, studies | project, written once | — | PL | once, never rewritten |
| Production data, logs | **no repository** | no | you | uploaded into the session that needs them |
| Data produced in a session, to be served (a package, tiles) — with a server runner | orders repository, `transfers/<domain>/<edition>/` (§2c) | no | the PL who produces it, **never the dev** | at the edition; removed from the tree once the report has succeeded |
| Images (tiles, visuals) | **in the conversation** | never | you | importing them into the project corrupts them silently |

**The claude.ai project holds only** the references written once ⟨and, with the extension, the mirrors of the living
docs⟩, sorted into folders by theme (`Method/`, `<SubProject>/`, `Archives/`…).

---

## 5 · What is generic, what is to adapt

**Generic, to keep as is**: the roles; the cycle of a batch; the self-contained brief; the criteria as deltas,
measured on the delivered archive; the dev's stops; the cold acceptance; the PL looking at the renders themselves;
the living docs in the repository; the fast-forward merge after your validation; the session pitfalls.

**To adapt at the project's first batch** (the PL asks you at bootstrap):
- **the test bench**: the tooling that measures an archive (file count, tests, lint, i18n, CSS, hashes);
- **the gates** of the dev (P0 to Pn) and what it never touches;
- **versioning**, according to each deliverable's regime (the two regimes: [`CORE.md`](CORE.md) §3);
- **the deliverable**: deployment zip, single HTML file, PDF, an agent's archive… and where it is dropped — or, if it
  runs on a production server you administer, how it is deployed there (the server runner, optional);
- **the proof specific to the type of project**: byte-exact rebuild for a built HTML, tests and migration for an app,
  replay for a calculation engine, DOM checks for a page.

**The test bench is built by the first batch**, a tooling batch, briefed short by the PL and built by the dev
([`CORE.md`](CORE.md) §3).

**What depends on the Claude product**: the functions of the app and its sessions that the method uses can change;
`CLAUDE_DEPENDENCIES.md` says, for each, what breaks and the fallback. Re-read it at every version of the package.

---

## 6 · The costs to expect (measured on a first project)

- an ordinary batch: 5 to 20 minutes of dev, a few minutes of acceptance;
- a screen with a mock-up: 15 minutes to 1 h 30 of dev, one or two mock-up passes with you (made by the PL before the launch, or asked of the dev, who delivers it through a stop; the PL shows it to you and relays your verdict word for word);
- an addendum launched by the PL: a few minutes, without a single action on your part;
- a PL session: the handover at a natural end of the queue or at the context threshold of method §6.

*A dev sub-agent consumes the credit of the PL session. The first project costs a tooling batch (the test bench) before
the first product batch.*

---

## 7 · Keeping the package alive

- **The source is a private repository; this public repository is its anonymized, bilingual copy** — or your copy, if you
  evolve the method for yourself (a fork, or a private repository you push it to); the `methode-cdp` skill is the
  installed copy of `skill/SKILL.md`, which is authoritative.
- **When a project's method changes version on a generic lesson** (one that would hold for any project), the PL
  of that project carries it over here — templates, `3_GITHUB.md`, skill — in a commit “Package vN: …”, tells you, and
  offers you the updated skill. A lesson specific to the project stays in its method.
- **A project already bootstrapped does not realign by itself**: its method prevails; its PL takes up a change of the
  package at its next method version, if relevant. **Before reinstalling the v19 skill on a project bootstrapped
  earlier**, its PL checks that the project's method carries what the v17 skill alone used to say and completes it
  from `templates/METHOD.md` otherwise: for any project, the handover (measurement, thresholds, fixed line), the
  living docs' ceilings and the checkpoint's §0 at each closed batch; with several PLs, also the baton, the queue and
  the coordination.
- Package version in the header of this file; the history in git; neither tag nor release needed. **The skill takes
  the version of the package that publishes it**: a package version that changes the skill republishes it under its
  number. The French version
  lives in `fr/` and is kept in step with the English one, version for version; the tests of the links and of the
  parity (`templates/tests/test_links.py`, `templates/tests/test_parity.py`, and their French counterparts) pass on
  this public copy as on the source.
- **The templates and the skill stay generic**: no project name, no decision number from a project.

**History**: v1, 23 October 2026. v2, 26 October 2026 — the workstreams board regenerated at every
write; a private `-Batches` repository when the code is public; the local runner (Claude Code on the PC,
driven by files); the measured handover. v3 — a single batches
repository for a suite of several code repositories, module prefix in the batch names. v4 — a text to paste is handed
over ready, with no field to fill in. v5 — the public version. v6, 27 October 2026 — several PLs at the same time
(a checkpoint and a baton per domain, numbers and versions reserved by a push, append-only, computed totals, messages
through workstreams); the handover without a handover prompt, by a fixed line per domain; the coordinator. v7,
27 October 2026 — one delivery = one new number, everywhere: an addendum only serves while nothing has been handed over
or deployed, trial feedback makes a batch of the next version; the coordinator briefs the tooling of the method and of
the living docs; `check_living_docs.py`. v8, 27 October 2026 — one deliverable, a single batch in flight: another batch
of the same deliverable is suspended until the first one is validated and merged; nobody announces a version in
advance, it is computed when the batch takes the deliverable; the “deliverables” check of `check_living_docs.py`. v9,
27 October 2026 — a shared resource (the owner's machine and its game) is taken like a deliverable; a batch with no
release carries no deliverable; the end-of-discussion summary; check 8 of `check_living_docs.py` counts resources.
v10, 28 October 2026 — the server runner: a deterministic program on the production server pulls its orders from a
private repository, the PL deploys on the owner's go, the hand-over becomes the fallback; optional guide and reference
implementation; the server question at bootstrap; three ways to organize (§2a).
v11, 29 October 2026 — the living-docs arbiter: role, when it matters, configuration of the scheduled task, log,
notifications; the fixed line names all the domain's repositories; a baton is judged by its silence.
v12, 29 October 2026 — the archiving of accepted workstreams: `archive_workstreams.py` dates every entry that becomes
accepted and moves out to `Archives/WORKSTREAMS_<YYYY-MM>.yaml` those accepted for 15 days, `search` finds them again,
`check_living_docs.py --archives` checks the identifiers and the log against the archives; the arbiter archives too
(otherwise the PL or the coordinator, at their close-out); an order is never written onto a file that exists (server
runner).
v13, 30 October 2026 — the living-docs arbiter explained in full (`templates/ARBITER.md` v3: what it is, why — the real
cases —, when, what it costs, how to read it, the set-up and who does what, the verdict; §2b); check 9 “checkpoints” of
`check_living_docs.py` (`--domains`, `--root`) and the domain table `templates/domains.yaml`; the arbiter's Monday
reading; a checkpoint's queue carries only registered workstreams (method §6); skill v15.
v14, 30 October 2026 — starting with or moving to several PLs, your actions (§3a); the prompt that opens the
coordination (`2_PL_BOOTSTRAP_PROMPT.md` §D); the project instructions for several PLs.
v15, 30 October 2026 — moving from one mode to another along the way: the signs, your actions, what the session
does, going back when a domain closes (§3b).
v16, 30 October 2026 — the orders repository, file-exchange bridge: how data gets onto the server — produced in a session
(`transfers/<domain>/<edition>/` of the orders repository, then a `fichiers` order), produced on the PC (`entree/`),
published elsewhere (`telecharger`), never the history of a public code repository; why, the PL's step by step, limits
(95 MiB per file, the runner's clone) (§2c; `templates/SERVER_RUNNER.md` v2).
v17, 31 October 2026 — the dev stays a sub-agent of the PL up to the mock-up, which it delivers through a stop, and talks
only to the PL (`templates/DEV_PROMPT.md`, `templates/DEV_COMMAND.md`); the baton defined (the last eight characters of
the session identifier); a checkpoint's queue under a stable title `## §<n> · The queue`, an empty `queue:` line
flagged, the coordination in the domain table; the owner's machine through the Claude app's bridge, the local runner as
the fallback (`templates/LOCAL_RUNNER.md` v2); short living docs: entry caps, accepted workstreams archived at seven
days, the log cut into slices of 50 numbers, a 10 KB checkpoint and check 10 (`templates/ARBITER.md` v4: ten checks);
a project's method carries only its common part; the board republished by a light sub-agent; skill v16.
v18, 31 October 2026 — a two-page core for an owner alone with a PL (`CORE.md`, with the table of extensions, their sign and
their pointer); a glossary (`GLOSSARY.md`); the dependencies on the Claude product, their fallback and the date of the
survey (`CLAUDE_DEPENDENCIES.md`); the coordination is no longer judged by its silence (`templates/ARBITER.md` v5); the
handover: context thresholds to warn then hand over, the saturation signs noted; the published board, a
fixed page and its data file (`workstreams.html`, `workstreams.json`), what the PL reads before republishing; two versioning
regimes, deployed per batch or released (`templates/code-repo/CHANGELOG.md`, “Unreleased” section); the method, proven on
three projects, one of them complex; skill v17.
v19, 31 October 2026 — the corrections from the independent review of package v18: the number of a fix (the rule of
the method §1a), the “released” regime through to the end (`batch/<batch name>`), the complete
precedence, no handover with a dev in flight, §0 of the checkpoint refreshed at each closed batch, thresholds with a single
source (method §6), the independent review of the code, the orders repository cloned only after acceptance, the protection
of `main` and of secrets; the v19 tooling (strict YAML, eleven checks); the arbiter as a GitHub Action
(`templates/ARBITER.md` v6, rewritten shorter) and the controller (`templates/CONTROLLER.md`); the dependencies on the
product completed; relative links between the documents and a test that guards them. Then, within the same v19: a core
that is enough on its own (`CORE.md`: the moves to start, the test bench as the first batch, the fixed line, the two
regimes, the fallback without a sub-agent, the living docs of mode A; the mirror in the project and the public repository
moved to the extensions; the mode A bootstrap with neither published board nor mirror); the short skill, at v19 like the
package (what a session knows before reading the project's method; the rest moved there); a single source per rule (the
method's figures in a table of its §6, a pointer everywhere else, and a parity test in CI); a batch's facts written
once, in the plan's version log; light low-complexity batches (the short form of the brief, seven gates, expected results only when
the batch produces values to compare); check 4 verifies the number of the batch in flight.
