# CORE — the PL method for a project with a single PL
### 1 November 2026 · the document that is enough to start · mode A (`GUIDE.md` §2a)

*Alone with a PL, read this first; each template is read when it is filled in. The rest of the package is added when a
sign you have lived through calls for it (the table, at the end). The terms are in [`GLOSSARY.md`](GLOSSARY.md).*

## 1 · The three roles

- **You, the owner**: you decide and validate on screen; you talk only to the PL; you create the tags and the releases
  (a session cannot). You run no command.
- **The PL** (project lead, Opus, long session): it decides with you, measures the actual state, writes the brief,
  launches the dev, accepts, closes and keeps the living docs. **It does not write the delivered code**: a missing tool
  becomes a batch (one exception: the static files its mock-up fixed, taken over by the dev, verified by sha256).
- **The dev** (the model of the method §6): launched by the PL as a sub-agent of its session, without its context, it
  executes **one brief** and talks only to the PL, through what it pushes and through its final reply.

**The PL's posture**: numbered options with a recommendation; when it has decided without you, its reply ends with
“Decided without you: …”; a simple question gets a direct answer, without the batch circuit.

## 2 · The three layers, and your moves to start

1. **The personal skill `methode-cdp`** (your account, all your projects): what a session knows before reading the
   project's method.
2. **The project instructions** (claude.ai): your profile, where the living docs are, which repositories. Pointers, not
   rules: a rule copied here would drift.
3. **The living docs and the repositories**: the project's method, the checkpoint, the decision log, the plan,
   `workstreams.yaml` (in the living-docs repository), and the code. They change at every closed batch, by the PL alone.

**Precedence**: your decisions in the decision log override everything; the project's method overrides the skill; for a
dev, the practical conditions of its command override the brief, which overrides the dev prompt for what the batch does.

**Your moves, before the first session**:
1. On GitHub, **create two empty private repositories**: `<Project>` (the living docs) and `<Project>-App` (the code);
   protect `main` against force-push and deletion, and turn on **secret protection at push** for the account — it only
   blocks pushes to **public** repositories; for a private repository, push protection only exists in a **paid
   organization** (GitHub Team or Enterprise): **a personal account has no option**. On a free account, GitHub does not
   apply branch rules to private repositories either: **in mode A, on a personal account, no technical
   safeguard**; the only one is the test bench's secret scan (gate P12 of the dev prompt; [`3_GITHUB.md`](3_GITHUB.md) §5).
2. On claude.ai, **create the project**; paste into its instructions
   [`1_PROJECT_INSTRUCTIONS.md`](1_PROJECT_INSTRUCTIONS.md) (short version), the `<…>` filled in.
3. **Customize the skill** ([`skill/SKILL.md`](skill/SKILL.md): its §1 and §8 describe you) and install it in your
   skills.
4. Open a conversation with Opus in the project and paste
   [`2_PL_BOOTSTRAP_PROMPT.md`](2_PL_BOOTSTRAP_PROMPT.md) §A, completed with what you want to build.

**What the PL creates at bootstrap, in mode A**: in the living-docs repository, a README, the project's method, the
checkpoint, the decision log, the plan (and its version log), `workstreams.yaml`, and the scripts copied from the
package (`archive_workstreams.py`, `make_board.py` for later, `pl_tools/context.py`); in the code repository,
`.gitattributes`, `.gitignore`, the `CHANGELOG` and the dev prompt. Nothing else without a sign.

## 3 · The cycle of a batch

**The first batch is the test bench** (a tooling batch: what measures an archive — tests, lint, fingerprints): without
it, no gate can be measured. The first product batch comes next.

1. **The study**: the PL measures the actual state (never the assumed one) and decides with you.
2. **The brief**: a single self-contained document — what the batch does, **what does not move**, the exact list of
   allowed files, criteria **as deltas against the base**, the stops. Pushed alone on the batch's branch.
3. **The dev**: it builds, measures, delivers a commit then a report. If it hits a point that is ambiguous, impossible or
   contrary to the actual state, **it stops** (`STOP_<n>.md`) instead of deciding. **If the PL cannot launch a
   sub-agent**, it gives you a line to paste word for word into a new conversation, with the model, the effort and the
   session above it ([`templates/DEV_COMMAND.md`](templates/DEV_COMMAND.md) §B).
4. **The cold acceptance**: the PL re-measures on `git archive` of the delivered commit, reads the diff against the
   brief's rules, looks at the renders; a medium or high batch, or a new dependency: a sub-agent of another model reads
   the diff; you validate on screen.
5. **The close-out**: fast-forward merge after your validation, the version log line, an entry in the decision log, the
   workstreams up to date, a “Batch closed” commit in the living docs.

**The two versioning regimes**: a deliverable **deployed per batch** (an application in service) takes one version per
batch, announced in the brief (branch `batch/v<X.Y>`): the highest version already taken by a batch, handed over or
refused, plus one — the exact rule: method §2, step 6; a deliverable
**published by release** (a tool downloaded as a package) takes no version per batch (branch `batch/<batch name>`): the
batch completes the “Unreleased” section of the `CHANGELOG`, and the release is made when you ask for it.

## 4 · The checkpoint and the handover

The **checkpoint** states the actual state under a cap (method §6); every PL session reads it first and sets its
**baton** in it (“session active: <last eight characters of the session identifier>”). **Alone, the baton protects you
from one thing**: a second conversation opened by mistake on the project sees it, and does not write to the living docs.

**The handover is measured** (`templates/context.py`): every turn re-reads the whole context, and the bigger it is, the
more it costs and the less accurate it is. At the thresholds of [`templates/METHOD.md`](templates/METHOD.md) §6, the PL
warns you, stops launching batches, then **hands over** — never with a dev in flight: §0 of the checkpoint up to date,
baton released, push, and the **fixed resume line** to paste into a new conversation. Nothing travels outside the
repository.

**The fixed line**, at the top of the checkpoint, under “Opus · new conversation in the project”: “You are
Opus-PL-<Project>. Resume: attach with push access the repositories <owner> <Project>, <Project>-App (one clone at a
time), git pull in <Project>, read `<Folder>/CHECKPOINT_<P>.md` in full (§0 first) and follow it.” It names all the
repositories: a session refuses an attachment you have not asked for in so many words, and the pasted line stands for
that request.

## 5 · What does not forgive

- **Nothing is believed, everything is measured**: cold, on the delivered archive, as deltas; never copied from the dev's
  report.
- **One delivery = one new number**: what is handed over or deployed to you carries a number never taken (§3), never
  `main` plus one; a fix is a following batch. Published by release: the number is fixed at the release you ask for.
- **The dev pushes only its batch's branch**: never `main`, never a tag, never `--force`.
- **A justified stop by the dev is never a reproach**: execution is often right against the brief.
- **The project's invariants** (a file, a fingerprint) move only on your written authorization in the brief.
- **No secret in a repository**, nor production data; the PL deletes nothing without your agreement.

## 6 · The extensions: when you need one, where to read it

Each is added without migrating anything. As long as the sign has not occurred, do not install it.

| extension | when: the sign you have lived through | where |
|---|---|---|
| **Several PLs** (modes B and C) | a second module starts, or you want two subjects at the same time in two conversations | [`GUIDE.md`](GUIDE.md) §2a, §3a, §3b; `templates/METHOD.md` §1a |
| **The public repository** | the code is public: the dev prompt and the batches go to a third, private repository, `<Project>-Batches` | `3_GITHUB.md` §6 B |
| **The mirror in the project** | a conversation without a clone must read the living docs (the project carries a copy) | `templates/METHOD.md` §6 (“The living docs”); `3_GITHUB.md` §4 |
| **The living-docs arbiter** | duplicated decision numbers, a board out of line, or a forgotten session that keeps its baton | `GUIDE.md` §2b; [`templates/ARBITER.md`](templates/ARBITER.md) (a GitHub Action) |
| **The controller** | after the arbiter: the documents swell, repeat themselves or contradict each other, and nothing says so early enough | `GUIDE.md` §2b; [`templates/CONTROLLER.md`](templates/CONTROLLER.md) (a weekly session) |
| **The orders repository** | data produced in a session must reach the server without you | `GUIDE.md` §2c; [`templates/SERVER_RUNNER.md`](templates/SERVER_RUNNER.md) §5 |
| **The local runner** | you drive a game or an application on your PC and the Claude app's bridge does not give your machine | [`templates/LOCAL_RUNNER.md`](templates/LOCAL_RUNNER.md); `templates/METHOD.md` §1 |
| **The server runner and the deployment** | you administer a production server and you drop the deliverable by hand at every batch | `templates/SERVER_RUNNER.md`; `templates/METHOD.md` §4a |
| **The published board** | you want to see at a glance what is to be done, without reading `workstreams.yaml` | `templates/METHOD.md` §6 (“The workstreams board”); `templates/make_board.py` |
| **The product sheet** | one product has several module PLs, and what is common (ritual, test bench, pitfalls) repeats in each checkpoint | `templates/METHOD.md` §1a |

*This document is enough to bootstrap a project in mode A, with [`2_PL_BOOTSTRAP_PROMPT.md`](2_PL_BOOTSTRAP_PROMPT.md) §A.*
