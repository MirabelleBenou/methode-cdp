# GITHUB IN THE METHOD
### The repositories, their structure, the circuit of a batch, what does not get through from a session

*The repositories replace everything that used to be uploaded: the code, the living docs, the briefs and the reports.
A PL or dev session starts from a clone and leaves by a push. The sandbox keeps nothing from one session to the next:
everything is rebuilt from the repositories.*

---

## 1 · The two families of repositories

| repository | visibility | holds | who writes there |
|---|---|---|---|
| **`<owner>/<Project>`** — the living docs | private | `README.md`; `Method/METHOD_<P>.md`; `<Folder>/`: checkpoint, decision log, plan, `workstreams.yaml`, statuses of the subprojects; `<Folder>/expected/<version>/`; `<Folder>/pl_tools/`; `<Folder>/Archives/` | **PL sessions only** |
| **`<owner>/<Project>-App`** — the code | private (public: §6 B) | the code at the root; `bench/`; `DEV_PROMPT_<P>.md`; `batches/<version>/`; `.gitattributes`, `.gitignore`, `CHANGELOG.md` | the PL on `main` (merge, brief); the dev on the branch of its batch |

**The code repository is public** (GitHub Pages, open license): **the dev prompt and `batches/` never go there** — they
name the owner, describe the method and cite the decision log. They go into a third, private repository (§6 B). A file
pushed to a public repository stays there in the history even if removed afterwards: the rule holds **from the first
commit**.

**Why two repositories**: the dev reads the whole code repository; it must not read the acceptance expected results,
nor the pending decisions, nor the other workstreams. The living docs stay with the PL.

---

## 2 · The structure of the code repository

```
<Project>-App/
├── <the delivered code>       ← exactly what the deployment archive holds
├── CHANGELOG.md               ← in the archive
├── bench/                     ← export-ignore: the measuring tooling, its README first
├── DEV_PROMPT_<P>.md          ← export-ignore: the dev's standing command
├── batches/                   ← export-ignore
│   └── v<X.Y>/
│       ├── BRIEF.md           ← the PL, a single commit on the batch's branch
│       ├── ADDENDUM_<n>.md    ← the PL, to lift a stop or a gap, before hand-over
│       ├── STOP_<n>.md        ← the dev, before stopping
│       ├── DEV_REPORT.md      ← the dev, after the delivery commit
│       └── mock-up/            ← the PL's mock-up, or the images shown
├── .gitattributes             ← export-ignore of itself too
└── .gitignore
```

**`.gitattributes`** (template in `templates/code-repo/`):

```
bench/              export-ignore
batches/            export-ignore
DEV_PROMPT_*.md     export-ignore
.gitattributes      export-ignore
```

**The deployment archive is `git archive` of the delivery commit**: `bench/`, `batches/` and the prompt do not get into
it. It is what the dev measures, what the PL re-measures, and what you deploy — the same one, byte for byte.

---

## 3 · The circuit of a batch, through the branches

```
main ────●──────────────────────────────────────────●  (fast-forward after your validation)
          \                                        /
batch/vX.Y ●─ BRIEF ─ … work … ─ DELIVERY ─ REPORT
              (PL)    (dev)      (dev)      (dev)
                         └ STOP_1 (dev) ─ ADDENDUM_1 (PL) ┘  if needed
```

1. **The PL creates `batch/v<X.Y>` from the head of `main`** and pushes **a single commit** to it:
   `batches/v<X.Y>/BRIEF.md` (and its mock-up if there is one). The brief names the base commit (the head of `main`).
2. **The PL launches the dev as a sub-agent** (`templates/DEV_COMMAND.md`): model and effort from the brief, clone in a
   separate folder, nothing else in context. *Fallback: a line you paste into a new conversation.*
3. **A stop**: the dev pushes its branch with `STOP_<n>.md` and stops. The PL reads it, pushes `ADDENDUM_<n>.md` on the
   same branch, relaunches the dev.
4. **The delivery**: the dev pushes its delivery commit, **then** `DEV_REPORT.md` in a separate commit (the report
   does not enter the archive, the hash does not depend on it).
5. **The acceptance**: the PL redoes `git archive` of the delivery commit, re-measures cold, rereads the diff, looks at
   the renders. It hands you the deliverable under its exact name, with its sha256.
6. **After your validation in production**: `git push origin batch/v<X.Y>:main` — **fast-forward, never `--force`**.
   Then the close-out of the living docs, a commit “Batch v<X.Y> closed” in the living-docs repository, the mirror in
   the project.

**One delivery = one new number**: a fix or trial feedback after a hand-over makes a batch of the next version, on its
own branch started from the batch's branch, one commit and one report each. An addendum under the same version only
serves while nothing has been handed over or deployed.

---

## 4 · The PL in the living-docs repository

- It attaches it (`add_repo`, `push` access) and clones it at the start of the session: **it is its working copy**.
- `git pull` before writing, `git fetch origin main` before pushing.
- It edits by targeted replacements; **a document's version is in its header, the history in git**; file
  names stay stable.
- **Several PLs can share the living docs**, one per domain (method §1a): each its own checkpoint and baton; decision
  log, plan and workstreams append-only; a decision number is reserved by a push; a deliverable has a single batch in flight, its
  version is computed when the batch takes it; `pull` before every write, a
  conflict shows at the `pull` instead of being overwritten.
- **The mirror in the project**: at every close-out, each modified file is copied over with the project tool by sending
  the file from the clone (`project_write` with `local_path`), under the same name. **Never from the text the project
  tool returns**: it returns everything as text, with no byte-exact proof. A GitHub “Sync now” of the project is not
  automatic — the mirror by the PL spares you that action.
- It says in its answer what it wrote: repository, commit, path.

---

## 5 · What does not get through from a session — and the other pitfalls

| pitfall | what happens | the remedy |
|---|---|---|
| **Tags and releases** | pushing a tag gets cut off, the API answers 403 | **you set them on GitHub**, with the text the PL gives you |
| **Branch deletion** | 403 refusal | you delete the merged branches; the checkpoint lists them |
| **Repository creation** | impossible from a session | you create the empty repository; the session attaches it |
| **One repository per session** | each session attaches its repositories (`add_repo`) | one clone at a time, generous command timeout |
| **Dev session opened by hand** | it may fail to attach a private repository | the PL's sub-agent inherits the repositories of their session |
| **Single-branch clone** | `git fetch origin main` does not create `origin/main` | write `git fetch origin main:refs/remotes/origin/main` |
| **Batch branch tracking `origin/main`** | the end-of-turn hook believes there are unpushed commits | set `branch.<batch>.merge` and add the branch to `remote.origin.fetch` |
| **Attribution lines** | the session imposes its lines in the commits | on a public repository, they show: be aware of it |
| **Secrets** | a pushed `.env` is published forever | only `.env.example` holds values, dummy ones; check before the first push |
| **`dist/` folder ignored but tracked** | `git add` does not pick it up | `git add -f` |
| **HTTP 413 rejection on push** | push of a copy that is not up to date | `git fetch origin main` before pushing |
| **Case of the repository name** | the session clones in lowercase | both work; the canonical address is the one from creation |

---

## 6 · Variants

**A · Project without code** (documentation, campaign, data): a single repository, the living-docs one; the deliverables
live there under `deliverables/`, versioned by commit. No dev sub-agent if the PL produces only documents — the rule
“the PL does not write what is delivered” applies to code, not to documentation, which the PL may edit with your
authorization.

**B · Public code** (open license, GitHub Pages): **three repositories**, which you create empty before the bootstrap.

| repository | visibility | holds |
|---|---|---|
| `<Project>` | private | the living docs, as usual |
| `<Project>-App` | **public** | the code, its tests, the test bench if it names no one, `.gitattributes`, `.github/` — and nothing else |
| `<Project>-Batches` | private | `DEV_PROMPT_<P>.md` at the root; `batches/<batch>/` (brief, addenda, stops, report, mock-up) on the branch `batch/<batch>` |

- **The circuit**: the PL pushes the brief to `batch/<batch>` of the batches repository; it names the commit of the
  public repository the code starts from. The dev reads the prompt and the brief in the batches repository, clones the
  public repository, pushes the code there on its own branch `batch/<batch>`, and pushes stops and report to the batches
  repository. The sub-agent inherits the three repositories.
- **The dev does not read the living docs**: that is why the prompt and the batches do not go into the living-docs
  repository, where the acceptance expected results are.
- **A simple tool can do without a dev prompt**: the brief is then enough on its own, and names the functions to read
  in a large build file.
- After your validation: fast-forward of the public `main` (byte-exact to the accepted archive); at the milestone, the
  `CHANGELOG` and what GitHub Pages serves, then **you set the tag and the release**.
- **The PL rereads every diff pushed to the public repository**: no first name, no profile, no reference to the method,
  the decision log or another project. The attribution lines of the commits, imposed by the session, show there.

**C · Several subprojects**: a single living-docs repository, one folder per subproject, a single decision log and a
single `workstreams.yaml` (a `module` field), one status per subproject; one code repository per deliverable deployed
separately.

- **A single batches repository for the whole suite** (`<Project>-Batches`, private), even when there are several code
  repositories, public or private: each batch carries **a module prefix** there — branch `batch/<prefix>-<batch>`, folder
  `batches/<prefix>-<batch>/` — and its code starts from the module's code repository, on `batch/<batch>`. The modules'
  dev prompts live there too, at the root. A private code repository gains from it: it then holds only the code and
  the test bench.
- **Why a single one**: one `-Batches` per code repository multiplies the attachments, the clones and the circuit rules;
  a single one keeps one rule for all, and the PL has only one place to file briefs and reports.
- **Forming it after the fact**: start from the history of an existing `-Batches` (fast-forward onto the new, empty
  repository), copy the other batch folders in one commit, check every tree hash (`git rev-parse <ref>:batches/<x>`),
  and remove `batches/` from the code repository while checking that the list (path, mode, sha256) of `git archive`
  does not change. Folders already closed keep their name; only the upcoming batches take the prefix.

---

## 7 · What never goes into a repository

*And in a public repository, in addition: the dev prompt and `batches/` (§6 B).*

- secrets, tokens, passwords, real `.env` files;
- production data (logs, dumps, exports): they are uploaded into the session that needs them;
- images for you to validate: they go through the conversation (or into `batches/<version>/mock-up/` when the
  brief orders them).
