# PL METHOD PACKAGE · v6
### 26 October 2026 · to start a new project under the PL method

*This package reproduces a way of working proven batch after batch: a **project lead** (PL, Opus) who decides
with you, writes the briefs, launches the dev and accepts; a **dev** (Sonnet by default) who builds one batch at a time;
**you**, who decide and validate on screen. Everything flows through GitHub; you upload nothing and run no command.*

**The owner**, in the templates and the skill, is you: the person who decides and validates. What is between `<…>` or
`⟨…⟩` is to be filled in — the PL does it at bootstrap, except for the skill, which you customize yourself (§1 and §8).

---

## 1 · What is in the package

| file | used for | where it ends up |
|---|---|---|
| `GUIDE.md` | these instructions for use | nowhere, it is for you |
| `1_PROJECT_INSTRUCTIONS.md` | the text to paste into **the claude.ai project instructions** | project instructions |
| `2_PL_BOOTSTRAP_PROMPT.md` | the **first message** of the first PL session | pasted into a conversation |
| `3_GITHUB.md` | the repositories, their structure, the circuit of a batch, the pitfalls | read by the PL at bootstrap |
| `templates/METHOD.md` | the generic method, to adapt | `Method/METHOD_<P>.md` in the living-docs repository, mirror in the project |
| `templates/DEV_PROMPT.md` | the dev's standing command | root of the code repository, mirror in the project |
| `templates/BRIEF.md` | the template of a batch brief | used by the PL, **never cited** by a brief |
| `templates/BATCH_FILES.md` | addendum, stop, dev report | used by the PL and the dev |
| `templates/DEV_COMMAND.md` | the command of the dev sub-agent, and the fallback line | used by the PL |
| `templates/CHECKPOINT.md` | the current state, entry point of every session | living-docs repository, mirror in the project |
| `templates/DECISION_LOG.md` | the decisions, numbered D1, D2… | living-docs repository, mirror in the project |
| `templates/PLAN.md` | the roadmap and the version log | living-docs repository, mirror in the project |
| `templates/workstreams.yaml` | the single source of the workstreams (upcoming, debts, delivered) | living-docs repository, mirror in the project |
| `templates/context.py` | measures the context of the PL session: warn at 600,000 tokens, hand over at 700,000 | `pl_tools/` in the living-docs repository |
| `templates/make_board.py` | builds `workstreams.html`, the readable page of the workstreams, at every write of the yaml | living-docs repository, mirror in the project |
| `templates/LOCAL_RUNNER.md` | the local Claude Code runner on the PC, driven by files (`sync\`) | used by the PL and the runner |
| `templates/living-docs-repo/` | `README.md` of the living-docs repository | living-docs repository |
| `templates/code-repo/` | `.gitattributes`, `.gitignore`, `CHANGELOG.md` of the code repository | code repository |
| `skill/SKILL.md` | the personal skill `methode-cdp`, **to customize (§1 and §8) then install** | your claude.ai skills |
| `fr/` | the same package in French | the same places as its English counterpart |

---

## 2 · The architecture: three layers, from the most general to the most precise

```
┌──────────────────────────────────────────────────────────────────────────┐
│ 1. PERSONAL SKILL  methode-cdp           (your account, all projects)    │
│    Who you are, the roles, the posture, the generic GitHub circuit.      │
│    → Rarely changes. Updated when the method evolves.                    │
├──────────────────────────────────────────────────────────────────────────┤
│ 2. PROJECT INSTRUCTIONS                  (one claude.ai project)         │
│    Your profile for this project, what you expect, WHERE the living      │
│    docs are, WHICH repositories. About ten lines, pointers, no rules.    │
│    → Changes when a repository or a reference document is renamed.       │
├──────────────────────────────────────────────────────────────────────────┤
│ 3. LIVING DOCUMENTS + REPOSITORIES       (the project itself)            │
│    METHOD_<P> (overrides the skill), DEV_PROMPT_<P>, CHECKPOINT,         │
│    DECISION_LOG, PLAN, workstreams.yaml; code and batches/ in code repo. │
│    → Changes at every closed batch, by the PL alone.                     │
└──────────────────────────────────────────────────────────────────────────┘
```

**Precedence rule**: the project's method overrides the skill; a batch's brief overrides the dev prompt for what the
batch does; your decisions in the decision log override everything.

**Why three layers**: the skill spares you from re-explaining the collaboration for each project; the instructions stay
short so they do not drift; the living docs carry what moves, under stable names, versioned by git.

**What does not go into Claude's memory**: the method and the state of the project. Memory keeps facts about you;
it does not replace a versioned document that a fresh dev can read.

---

## 3 · Starting a new project — your actions, in order

1. **On GitHub, create two empty private repositories** (without README):
   - `<Project>` — the living docs (method, checkpoint, decision log, plan, workstreams);
   - `<Project>-App` — the code.
   *Public code (GitHub Pages, open license): also create `<Project>-Batches`, private — the dev prompt and the batch
   folders go there, never into the public repository (`3_GITHUB.md` §6 B).*
2. **On claude.ai, create the project** and paste into its instructions the text of `1_PROJECT_INSTRUCTIONS.md`, once
   the `<…>` are filled in.
3. **Install the `methode-cdp` skill**: first customize its §1 and §8 (they are what describe you: your
   profile, your workstation constraints), then create it in your claude.ai skills with the content of `skill/SKILL.md`.
4. **Put the package within reach of the first session** — your choice:
   - (recommended) the PL reads it directly from the public repository `MirabelleBenou/methode-cdp` (at the root),
     read-only: nothing to upload;
   - or you upload the zip into the first conversation.
5. **Open a conversation with Opus in the project** and paste `2_PL_BOOTSTRAP_PROMPT.md`, completed with what you want
   to build.
6. **Answer the PL's questions** (numbered options, a recommendation each time). It initializes the two
   repositories, writes the project's method and dev prompt, the first living docs, and copies them as a mirror into the
   project.

From then on, you talk only to the PL. Your only remaining manual actions: **validate on screen**, set **the tags and
releases**, **delete the merged branches** on GitHub (a session cannot), and drop the deliverable where it is
deployed.

---

## 4 · What goes where

| item | reference location | mirror in the project? | who writes | when |
|---|---|---|---|---|
| Project method | living-docs repository `Method/` | yes | PL | at a version, after a batch that caught it out |
| Dev prompt | root of the code repository — **`<Project>-Batches` repository if the code is public** | yes | PL | at a version |
| Checkpoint | living-docs repository | yes | PL | at every handover |
| Decision log | living-docs repository | yes | PL | at every closed batch |
| Plan + version log | living-docs repository | yes | PL | at every batch that takes a version |
| `workstreams.yaml` and `workstreams.html` | living-docs repository | yes, and the page as an artifact | PL | at every write of the yaml |
| Acceptance expected results | living-docs repository `expected/<version>/` | no | PL | at the brief |
| The PL's throwaway scripts | living-docs repository `pl_tools/` | no | PL | as needed |
| Code, test bench, `CHANGELOG` | code repository | no | dev | within a batch |
| Brief, addenda, stops, report, mock-up | code repository `batches/<version>/` — **`<Project>-Batches` repository if the code is public** | **no** | PL (brief, addenda), dev (stops, report) | during the batch |
| Specs, style guide, studies | project, written once | — | PL | once, never rewritten |
| Production data, logs | **no repository** | no | you | uploaded into the session that needs them |
| Images (tiles, visuals) | **in the conversation** | never | you | importing them into the project corrupts them silently |

**The claude.ai project holds only** the mirrors of the living docs (copied over by the PL at every close-out, from their
clone) and the references written once, sorted into folders by theme (`Method/`, `<SubProject>/`, `Archives/`…).

---

## 5 · What is generic, what is to adapt

**Generic, to keep as is**: the roles; the cycle of a batch; the self-contained brief; the criteria as deltas,
measured on the delivered archive; the dev's stops; the cold acceptance; the PL looking at the renders themselves;
the living docs in the repository and their mirror; the fast-forward merge after your validation; the session pitfalls.

**To adapt at the project's first batch** (the PL asks you at bootstrap):
- **the test bench**: the tooling that measures an archive (file count, tests, lint, i18n, CSS, hashes);
- **the gates** of the dev (P0 to Pn) and what it never touches;
- **versioning**: who bumps the version, by how much, with your agreement or pre-authorized;
- **the deliverable**: deployment zip, single HTML file, PDF, an agent's archive… and where it is dropped;
- **the proof specific to the type of project**: byte-exact rebuild for a built HTML, tests and migration for an app,
  replay for a calculation engine, DOM checks for a page.

**The test bench is built by a tooling batch**, briefed short by the PL and built by the dev — never by the PL.

---

## 6 · The costs to expect (measured on a first project)

- an ordinary batch: 5 to 20 minutes of dev, a few minutes of acceptance;
- a screen with a PL mock-up: 15 minutes to 1 h 30 of dev, one or two mock-up passes with you;
- an addendum launched by the PL: a few minutes, without a single action on your part;
- a PL session: hand over before ~700,000 tokens of context, or at a natural end of the queue.

*A dev sub-agent consumes the credit of the PL session. The first project costs a tooling batch (the test bench) before
the first product batch.*

---

## 7 · Keeping the package alive

- **The source is the public repository `MirabelleBenou/methode-cdp`** — or your copy, if you evolve the method for
  yourself (a fork, or a private repository you push it to); the `methode-cdp` skill is its installed copy
  (`skill/SKILL.md` is authoritative).
- **When a project's method changes version on a generic lesson** (one that would hold for any project), the PL
  of that project carries it over here — templates, `3_GITHUB.md`, skill — in a commit “Package vN: …”, tells you, and
  offers you the updated skill. A lesson specific to the project stays in its method.
- **A project already bootstrapped does not realign by itself**: its method prevails; its PL takes up a change of the
  package at its next method version, if relevant.
- Package version in the header of this file; the history in git; neither tag nor release needed. The French version
  lives in `fr/` and is kept in step with the English one, version for version.
- **The templates and the skill stay generic**: no project name, no decision number from a project.

**History**: v1, 23 October 2026. v2, 26 October 2026 — the workstreams board regenerated at every
write; a private `-Batches` repository when the code is public; the local runner (Claude Code on the PC,
driven by files); the measured handover (warn at 600,000 tokens, hand over at 700,000). v3 — a single batches
repository for a suite of several code repositories, module prefix in the batch names. v4 — a text to paste is handed
over ready, with no field to fill in. v5 — the public version. v6, 27 October 2026 — several PLs at the same time
(a checkpoint and a baton per domain, numbers and versions reserved by a push, append-only, computed totals, messages
through workstreams); the handover without a handover prompt, by a fixed line per domain.
