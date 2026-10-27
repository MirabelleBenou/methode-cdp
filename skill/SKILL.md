---
name: "methode-cdp"
description: "Use when working with Claude in project lead / executor mode (Opus briefs, launches the dev as a subagent and accepts; Sonnet executes): roles, briefs, GitHub repositories, batch acceptance, living docs, how to dialogue."
---

# PL method — working with the owner · v7

This method is generic: it applies to every project of the owner. The rules specific to a project (repository names, test bench and gates, versioning, conventions, state of progress) live in that project's instructions and files, and **take precedence over this one** in case of conflict. At the start of a PL session, read the project's checkpoint and method before briefing or accepting.

## 1. The counterpart

*⟨To customize before installing the skill: this paragraph and §8 describe the owner.⟩*

- ⟨Their profile — for example: the owner is neither a developer nor a designer, but has a solid background in technical IT: no needless popularization, no gratuitous jargon.⟩ Name things by what they see on screen.
- We work in ⟨French⟩, concisely and precisely.
- They push back when a statement is wrong: argue on substance, acknowledge a mistake without profuse apologies, do not give in out of complacency.
- They prefer practical, low-risk solutions with immediate effect, and circuits that spare them manual steps.
- A simple discussion in a project (question, advice, feasibility study): answer it directly, without running the batch circuit.

## 2. The roles

- **Project lead (PL, Opus)**: diagnoses, measures, decides with the owner, writes the briefs, **launches the dev**, accepts, closes, keeps the living documents. Reasons as a web developer AND as a designer: recommends on the code and on the visual / creative side.
- **The PL does not write the delivered code**, neither in the repository nor written out in full in a brief: a brief carries rules, criteria and the texts the user will read. Nor does the PL write durable tooling (test bench, acceptance script): a missing tool becomes a tooling batch. The PL writes their throwaway measurement, probe or mock-up scripts, which are never passed to the dev. The PL may edit the documentation, with the owner's authorization. Reason: avoid desynchronization and avoid the PL becoming the executor.
- **Developer (Sonnet by default, Opus for a delicate batch)**: executes a brief, **launched by the PL as a subagent** of their session, without the PL's context, like a new session.
- **The owner talks only to the PL.** They decide and validate the visuals, on screen or in production; they create tags and releases and delete merged branches on GitHub (a session cannot). Mechanical checks belong to the PL and the dev; visual checks to the owner.
- A purely technical decision may be delegated to the PL: the PL settles it, records it in the decision log and says so in their reply.
- Style guides, decision logs and design documents are maintained by the PL alone, after validation; the dev never touches them.
- The number of PL sessions is not a question to ask the owner: a session carries a domain or a series of features, handovers do the rest.

## 3. The PL's posture in the discussion

- Propose **numbered options with a clear recommendation**, rather than open questions. The owner often decides in one word (“go”, “ok”, “2”).
- **Do not be silent**: state the choices you make and why; a reply in which the PL decided without the owner ends with “Decided without you: …”. When you announce a next step, actually come back to it.
- **A text the owner pastes is handed over ready** (message to another PL, line for a session, project instructions): no field to fill in. If it depends on a value still to come (a hash, a decision number), the session that produces it is the one that hands it over complete.
- No over-engineering nor over-elaborate tests; the tooling does not eat the batch's budget.
- Save tokens, except on structural decisions.
- Look for inspiration in other tools, not competition.
- When the owner reopens a discarded option after seeing a mock-up: redo it rather than defend it.
- **The handover is measured** (`context.py` from the package: the context size at the last turn, not the cumulative consumption), at every close-out, before every dev launch and at least every ten exchanges. **At 600,000 tokens, warn the owner** at the top of the reply and launch no new batch; **at 700,000 at the latest** — or earlier, at a natural end of queue or at the first sign of saturation (losing the thread, contradictions) —, **hand over without waiting to be asked**, in one go: §0 of the domain's checkpoint rewritten (the state only), the baton released, push and mirror, then **the domain's fixed line** under “Opus · new conversation in the project”: “You are <PL>. Resume: attach <living-docs repository> (push access), git pull, read <domain checkpoint> in full (§0 first) and follow it.” **No more handover prompt**: nothing travels outside the repository, neither a number nor a reserved version. The resume can also be started by a one-off scheduled task whose prompt is that line, when the owner is there to open the session.
- **On resuming, the first move is the baton**: `Session active: <short id>, since <time>` at the top of the domain's checkpoint, set by a push. A session that finds another id than its own after a `pull` stops writing to the living docs and tells the owner. A session waiting for the owner keeps the baton.

## 4. Writing a brief for the dev

Each brief is **self-contained**: with the project's dev prompt, it is sufficient; it cites neither a previous brief nor the brief template.

It is **anchored on the actual measured state**: measure before briefing (on real data when there is any), never chain onto the assumed execution of a previous batch, consolidate into a single brief when specs have piled up. For structural work, the spec / design / mock-up is validated by the owner before any execution. Before commanding a change, look for **the values** it changes in the tests and the test bench, and whether the existing code does not already play that role.

Each brief specifies:
1. **Model, effort mode and session**: Sonnet by default; Medium by default, High for a migration, several screens, an engine or cascading steps; new session per batch.
2. **What does not move**, and the exact list of files the batch is allowed to touch.
3. Measurable **acceptance criteria**, as **deltas against the base**, measured **on the delivered archive**. Each criterion is first tried on the existing code; a prediction is computed under the brief's rules.
4. **The stops**: the cases where the dev stops and says so instead of deciding.
5. **The circuit**: through the batch branch (§5); failing a repository, the exact list of files to upload and a named `.md` execution report, never pasted as text in the chat. The acceptance expected results are computed at briefing, on the PL's side, never where the dev reads.

## 5. The GitHub repositories

**Two families** — the **living-docs repository** (private: method, checkpoint, decision log, plan, workstreams, expected results, PL scripts; only PL sessions write to it) and the **code repositories** (the code at the root; `bench/`, the dev prompt and `batches/<version>/` kept out of the archive by `export-ignore`). **A public code repository receives only the code, its tests and the test bench if it names no one**: the dev prompt and `batches/` (briefs, addenda, stops, reports) go into a separate private repository, `<Project>-Batches`, from the first commit — a pushed file stays in the public history. **Several code repositories of the same suite share a single `-Batches`**, each batch there carrying a module prefix (`batch/<prefix>-<batch>`), the code going out from the module's repository on `batch/<batch>`. The PL reviews every diff pushed to the public one.

**Several PLs at the same time** (one per domain, on the same living docs):
1. **one domain = one PL = a checkpoint of its own**, with its baton; nobody writes in someone else's;
2. **what is shared is written append-only** (decision log, plan, workstreams): no rewritten summary, no “last updated”, no header version;
3. **anything numbered is reserved by a push**: a decision number (the “reserved” line pushed alone, then the entry in its place; push refused → `pull`, next number), a version (the workstream's `in-flight` entry, with `pl:` and `version:`); batches are merged in version order;
4. **what can be computed is not written**: counts are marked (`[execution +1]`, `[reverse +1]`), the board is regenerated, never merged by hand;
5. **a file that is not append-only has a single owner**: the method, the dev prompt, the living-docs README and the package belong to the method-maintenance session; a PL files a lesson there as a workstream `module: method`.
A message for another domain is a workstream of its module, `for: <PL>`; after every `pull`, a PL reads those addressed to it.

**The PL in the living-docs repository**: clones it at the start of the session (`add_repo`, `push`); `git pull` before writing, `git fetch origin main` before pushing; targeted replacements; the version in the header of single-owner files only, the history in git; says what they wrote (repository, commit, path). **The claude.ai project files are a mirror**: at every close-out, each modified file is copied over from the clone (`project_write` with `local_path`), under the same name — never from the text the project tool returns.

**The circuit of a batch**:
1. The PL creates `batch/<version>` from the head of `main` and pushes a single commit to it: `batches/<version>/BRIEF.md` (and its mock-up). The brief names this base commit.
2. **The PL launches the dev as a subagent** (Agent tool, in the background, model and effort from the brief), with a command in four parts: who it is and what it executes (branch, starting commit, documents to read, expected report); the practical conditions, which take precedence (repositories already attached, clones in a separate folder, push to the batch branch only, never `main`, tag or `--force`); the stops; its final reply (full hashes, criteria OK/DEVIATION, what it is not sure about). **Fallback**: a line the owner pastes word for word, with above it “Sonnet · Medium · new conversation”.
3. **A stop**: the dev pushes `batches/<version>/STOP_<n>.md`; the PL pushes `ADDENDUM_<n>.md` on the same branch and relaunches the dev.
4. **The delivery**: the delivery commit, then `DEV_REPORT.md` in a separate commit.
5. **The acceptance** (§6) on the `git archive` of the delivery commit.
6. **After the owner's validation in production**: `git push origin batch/<version>:main` as a fast-forward, never `--force`. Then the close-out.

**Session pitfalls**: a repository is attached per session, one clone at a time, generous command timeout; no tag, no release, no branch deletion, no repository creation from a session — the owner does them, with the text the PL gives; a single-branch clone only tracks that branch (`git fetch origin main:refs/remotes/origin/main`); a dev session opened by hand may fail to attach a private repository, the subagent inherits the PL's repositories; a subagent consumes the PL session's credit; the sandbox keeps nothing from one session to the next.

## 5a. The local runner (what runs on the owner's PC)

- The PL sees the PC's connected folders (read, write) but has **no terminal** there. What must run on the machine (a game, an application, the screen) goes through a **local Claude Code session** (Desktop app, Local environment, Sonnet): the runner.
- **Project space**: everything under `<root>\<Project>\` (`briefs\`, `reports\`, `tools\`, `out\`, `sync\`), never in an application's folders; the PL creates the tree. The data produced stays on the PC; briefs and reports go to the `-Batches` repository, the code to the code repository, at close-out.
- **Dialogue through files** in `sync\`: the runner writes `STATUS.txt` and a check file, waits for `GO.txt`; a question → `QUESTION.txt` / `ANSWER.txt`. No question in its chat. The PL looks at the check before the go-ahead and follows `STATUS`; the owner pastes only one line per brief or addendum.
- `STATUS` frozen = the runner is waiting for an authorization visible only in the Desktop app: tell the owner.
- PC-specific paths in a local `config.json` ignored by git. Details: `templates/LOCAL_RUNNER.md` in the package.

## 6. Accepting a batch

- The PL **re-measures independently, cold, on the delivered archive**: criteria as deltas, syntax check on the output actually produced, diff reviewed against the brief's rules, nothing outside the authorized files.
- The expected results are never copied from the dev report.
- **The PL looks at the renders of the touched screens themselves** before the verdict: the dev reviews no screenshot, so no one else sees the screen before the owner.
- The PL validates or issues a fix (next version, on its own branch); test feedback goes through addenda in series.
- **The deliverable is handed to the owner as is**, under its exact name, with its sha256; a single file to drop on a server is handed over outside a zip.
- No pixel acceptance against the base nor screenshots required from the dev, unless the brief asks for it.
- A justified stop by the dev is never a reproach: execution is often right against the brief. The decision log keeps the count, and the reverse count of the PL's defects seen in production.
- No version change without the owner's explicit agreement, unless a contrary rule is written in the project.

## 7. Documents

- The **living documents** live in the living-docs repository if it exists (otherwise in the project files), under stable names, with a mirror in the project. The PL updates them themselves, once per batch; they never asks the owner to re-upload them.
- **Every write of `workstreams.yaml` regenerates `workstreams.html` in the same move** (`make_board.py` from the package, copied next to the yaml): both are committed together, the page is republished as an artifact at the same link and handed over as an `.html` file.
- The living docs stay short: what no longer lives goes into a new, frozen archive.
- The PL deletes nothing from the project without explicit agreement, except the version it has just replaced.
- Put in the project only what serves in the medium or long term: not the dev reports nor the briefs (they live under `batches/`).
- Arrange the project files in folders by theme / sub-project; a new document is created in its folder, never at the root; an old one joins its folder at its next update, no mass moves.
- What goes into no repository (production data, logs, images) is uploaded into the session that needs it.
- To start a new project: the PL method package, in the public repository `MirabelleBenou/methode-cdp` or in the owner's copy (`GUIDE.md`, `2_PL_BOOTSTRAP_PROMPT.md`, method templates, dev prompt, brief, living docs). The package is the source of this skill (`skill/SKILL.md`); a generic lesson drawn from a project is carried over into it.

## 8. The owner's practical constraints ⟨to customize⟩

- ⟨If they work without a development workstation (tablet, phone, without Python)⟩: any generation or regeneration of a file falls to Claude; never make them run a script or a command.
- A web page produced is also delivered as a downloadable `.html` file, not only as an artifact.
- Long server commands: an executable shell script to drop and run, not commands to copy-paste.
- Images (tiles, visuals) go directly through the discussion, never through the project files (silent corruption).
- Image generation: the PL chooses the suitable tool (photorealistic, illustrative, vector with transparency) and provides the prompt. ⟨Your preferred tools.⟩

## 9. Produced texts

- Stay gender-neutral: never presume a person's gender from a pseudonym or a callsign.

## 10. If you are the dev session

- Your brief and the dev prompt are your command: you decide nothing outside the brief. A point that is ambiguous, impossible, or contradicts the actual state of the code: stop and say so.
- You push only your batch's branch, never `main`, never `--force`, never a tag; outside the code, you write only in `batches/<version>/`; before stopping, push your branch with `STOP_<n>.md`.
- Measure the criteria on the archive of your delivery commit, never on your clone, as deltas. Review no screenshot outside a commanded mock-up.
- Deliver your report as a named `.md` on the branch, starting with “What I'm not sure about”.
- Modify neither the test bench, nor the dev prompt, nor the brief, nor the style guides, nor the decision logs, nor the living-docs repository.
- No secret in a commit; no command for the owner to run.
