# GLOSSARY — the words of the PL method
### 31 October 2026 · one term, one or two lines, the document where it lives

*The paths are those of the package. To start, you only need the terms of the first part: the core (`CORE.md`) uses all
of them; the other parts serve when you add an extension (table of `CORE.md` §6).*

---

## 1 · The people and the sessions

| term | what it is | where it lives |
|---|---|---|
| **owner** | you: the one who decides and validates on screen, creates the tags and the releases, deletes the merged branches. They talk only to the PL (or to the coordination). | `CORE.md` §1; `skill/SKILL.md` §2 |
| **PL** (project lead) | the long Opus session that decides with you, measures, writes the briefs, launches the dev, accepts, closes and keeps the living docs. It does not write the delivered code. | `CORE.md` §1; `templates/METHOD.md` §1 |
| **dev** | the session (Sonnet by default) that executes a brief, one batch at a time. It talks only to the PL: through what it pushes and through its final reply. | `templates/DEV_PROMPT.md`; `skill/SKILL.md` §10 |
| **sub-agent** | a session the PL launches from its own (Agent tool), without its context, with a command in four parts. The dev is one; a delegated reading is another. | `templates/DEV_COMMAND.md` §A; `CLAUDE_DEPENDENCIES.md` |
| **coordination** (the coordinator) | the session that keeps the method, the domain table, the launching of PLs, the package, the living-docs tooling and the arbiter. It briefs no product batch. | `GUIDE.md` §2a; `skill/SKILL.md` §11 |
| **domain** | a PL, its scope, its checkpoint and its baton. One line of the domain table. | `templates/METHOD.md` §1a; `templates/domains.yaml` |

## 2 · The batch, from the brief to the close-out

| term | what it is | where it lives |
|---|---|---|
| **batch** | a dev's unit of work: a brief, a `batch/<version>` branch, a delivery commit, a report. | `3_GITHUB.md` §3; `templates/METHOD.md` §2 |
| **brief** | a batch's self-contained document: what it does, what does not move, the exact list of allowed files, criteria as deltas against the base, the stops. The dev starts from it. | `templates/BRIEF.md`; `templates/METHOD.md` §3 |
| **pre-brief** | the rules, criteria and texts of a batch that has not yet taken its deliverable, with no version and no expected results; it becomes the brief when the batch takes it. | `templates/METHOD.md` §1a |
| **addendum** | `ADDENDUM_<n>.md`, written by the PL to lift a stop or correct a gap, as long as nothing has been handed over or deployed. | `templates/BATCH_FILES.md` §A |
| **stop** | `STOP_<n>.md`, written by the dev when a point is ambiguous, impossible or contrary to the actual state: it stops instead of deciding. A justified stop is never a reproach. | `templates/BATCH_FILES.md` §B |
| **mock-up** | the render of a screen before it is built: either the PL's, made through the real code; or requested from the dev, who delivers it through a stop (`MOCKUP_<n>.md`). | `templates/METHOD.md` §2 and §3a |
| **test bench** | the tooling that measures an archive (files, tests, lint, fingerprints); it is built by a tooling batch. | `GUIDE.md` §5 |
| **gates** | the test bench's measurements that the dev passes on its delivery (P0 to Pn). | `templates/DEV_PROMPT.md` §4 |
| **expected results** | the acceptance's expected results, computed at the brief by the PL, never where the dev reads. | `templates/METHOD.md` §2 |
| **cold acceptance** | the PL re-measures independently, on `git archive` of the delivered commit: criteria as deltas, diff read against the rules, renders looked at. What the dev's report says is never copied. | `templates/METHOD.md` §4 |
| **close-out** | what the PL does once per accepted batch: fast-forward merge after your validation, decision log, workstreams, “Batch closed” commit, mirror in the project, checkpoint. | `templates/METHOD.md` §6 |
| **deliverable** | what is handed over or deployed; in the workstreams, the code repository the release comes out of. A single batch in flight per deliverable. | `templates/METHOD.md` §1a |
| **shared resource** | a machine or a piece of software only one batch at a time can occupy (your machine and its game); it is taken like a deliverable (`resource:`). | `templates/METHOD.md` §1a |
| **version** (the two *versioning regimes*) | *deployed per batch* (application in production, agent, deployer): the version is computed when the batch takes the deliverable, `main` plus one. *Released* (a tool downloaded as a package): the batch carries no version, it completes the “Unreleased” section of the CHANGELOG; the release is made at your request. One delivery = one new number. | `templates/METHOD.md` §1a, §6; `templates/code-repo/CHANGELOG.md` |

## 3 · The living docs

| term | what it is | where it lives |
|---|---|---|
| **living docs** | what moves with the project: the project's method, checkpoint, decision log, plan, `workstreams.yaml`. In the living-docs repository, with a mirror in the claude.ai project; the PL writes them alone, at every closed batch. | `GUIDE.md` §2 and §4; `templates/living-docs-repo/README.md` |
| **checkpoint** | the project's actual state, in 10 KB: the entry point of every PL session. One per domain. | `templates/CHECKPOINT.md` |
| **fixed line** (fixed resume line) | the ready-to-paste message that resumes a domain in a new conversation; it names all the domain's repositories. It is at the top of the checkpoint and in the living-docs README. | `templates/CHECKPOINT.md`; `templates/living-docs-repo/README.md` |
| **baton** | the line “Session active: <short id>” at the top of a checkpoint: who is working on the domain. The short id is the last eight characters of the session identifier. It is judged by its silence; the coordination's silence is not judged. | `templates/METHOD.md` §1a; `skill/SKILL.md` §3 |
| **queue** | the list of what remains to be done, in the `## §<n> · The queue` section of a checkpoint; it carries only registered workstreams, cited by their id. | `templates/METHOD.md` §6; `templates/CHECKPOINT.md` |
| **handover** | the move by which a PL hands over to a new session, on the measure of the context: warn at 450,000 tokens, hand over at 550,000 at the latest. | `CORE.md` §4; `templates/METHOD.md` §6 |
| **saturation sign** | what shows that a context is too full: losing the thread, contradictions, a forgotten decision. Every handover notes those it saw (or “none”). | `templates/METHOD.md` §6; `templates/CHECKPOINT.md` |
| **decision log** | the decisions, numbered D1, D2…; an entry fits in ~800 characters. | `templates/DECISION_LOG.md` |
| **reserved number** | a decision number is taken by pushing the “reserved” line alone; if the push is refused, take the next one. | `templates/METHOD.md` §1a |
| **plan and version log** | the roadmap, and the version log (one line per batch that takes a version). | `templates/PLAN.md` |
| **workstream** | an entry of `workstreams.yaml`: a subject to do, in progress or finished. Statuses: `upcoming`, `to-brief`, `in-flight` (a batch has taken the deliverable), `debt`, `accepted`. | `templates/workstreams.yaml` |
| **debt** | a retained workstream that waits for a trigger (“to group with the next batch that touches such a file”) or for your presence (access to your machine). | `templates/workstreams.yaml`; `templates/METHOD.md` §3 |
| **accepted** (the `accepted` status) | the status of a workstream delivered and validated; seven days later it moves out to the month's archive. | `templates/METHOD.md` §6 |
| **published board** | the page `workstreams.html`, fixed and with no data at all, and its *data file* `workstreams.json` next to it, published together at the same link. | `templates/METHOD.md` §6; `templates/make_board.py` |
| **data file** | `workstreams.json`, which the generator writes next to the page; the page reads it by `fetch`. | `templates/make_board.py`; `templates/living-docs-repo/README.md` |
| **checker** | `check_living_docs.py`: the read-only check of the shared living docs (ten checks, including check 6, the page and its data against their regeneration). | `templates/check_living_docs.py`; `templates/living-docs-repo/README.md` |
| **product sheet** | the checkpoint of a product that has several module PLs: what is common (ritual, test bench, circuit, pitfalls), never the state. | `templates/METHOD.md` §1a; `skill/SKILL.md` §11 |

## 4 · The extensions, the bridge and the fallback

| term | what it is | where it lives |
|---|---|---|
| **core** | the two pages that suffice for an owner alone with a PL, and the table of extensions. | `CORE.md` |
| **extension** | what the method adds when a sign you have lived through calls for it: several PLs, arbiter, orders repository, runners, published board, product sheet. | `CORE.md` §6 |
| **arbiter** | a fresh session, started every morning by a scheduled task, that checks the shared living docs and the checkpoints and reports without correcting. | `GUIDE.md` §2b; `templates/ARBITER.md` |
| **orders repository** | a private repository where the PL pushes its orders and from which the server runner pulls them; it also serves as the file-exchange bridge (`transfers/`). | `GUIDE.md` §2c; `templates/SERVER_RUNNER.md` §5 |
| **server runner** | a deterministic program on your production server: it executes the orders of an allow-list and pushes a report. No AI in the deployment path. | `templates/SERVER_RUNNER.md`; `templates/METHOD.md` §4a |
| **local runner** | a local Claude Code session on your PC, driven by files; the fallback when the bridge does not give your machine. | `templates/LOCAL_RUNNER.md` |
| **bridge** | what the Claude app offers the PL's session for your machine: linked folders, a terminal if one is offered, the screen, which you validate. | `skill/SKILL.md` §5a; `CLAUDE_DEPENDENCIES.md` |
| **fallback** (fallback line) | what serves when the normal route is missing: the line you paste into a new conversation when the PL cannot launch a sub-agent; the local runner when the bridge is missing; the hand-over of the deliverable when the server runner is silent. | `templates/DEV_COMMAND.md` §B; `templates/LOCAL_RUNNER.md` |
| **mode A / B / C** | three ways to organize: A, one PL; B, independent modules, one PL each; C, linked modules, one PL per domain and a coordination. | `GUIDE.md` §2a, §3b |
