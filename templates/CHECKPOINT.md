# CHECKPOINT — <Project> · `v<X.Y>`
### <date, time> · <PL session> · entry point of the next session · replaces the checkpoint of <date>

> *Source: private repository `<owner>/<Project>`, `<Folder>/CHECKPOINT_<P>.md`. The claude.ai project holds a mirror of
> it under the same name, copied over by the PL.*
>
> *The checkpoint states the **real** state, measured — not the hoped-for state. It is rewritten in full at each handover.*

---

## §0 · Where we are

- **<Project> is at `v<X.Y>`.** Code fingerprint `<…>`; ritual replayed on <date>: compliant, `<n> passed`.
- **The code repository**: `main` at `<sha>`; the deployment archive is `git archive` of `main`.
- **Since the previous checkpoint**: <the batches delivered, one line each, with their version and their D>.
- **The method** is at v<n> (<what changed>).
- **The decision log** runs up to **D<n>** (next: **D<n+1>**). “Execution is right” at <n>, the reverse at <n>.
- **Open debts**: <id — half a line each>.
- **To do by the owner**:
  - <tag and release to set, on which commit, with which text>;
  - <deliverable to upload, exact name and sha256>;
  - <merged branches to delete on GitHub: …>.
- **In flight**: <what is waiting for a test or an outside answer>.

---

## §1 · The first move — clone, ritual

**1. The repositories** (one `add_repo` each, owner `<owner>`, `push` access, one clone at a time):
- `<Project>` → `git clone --depth 1 https://github.com/<owner>/<project> /home/claude/<project>`;
- `<Project>-App` → `git clone --depth 1 https://github.com/<owner>/<project>-app /home/claude/<project>-app`.

Read this checkpoint, then `Method/METHOD_<P>.md` (v<n>).

**2. The base ritual**: <the commands, one per line> — expected, line for line:

```
<expected output of the ritual on the base>
```

Any divergence stops there and is told to the owner.

---

## §2 · The circuit of a batch

<The circuit as it plays out in THIS project, in six short steps — refer to the method for the detail. What has
changed since last time in bold.>

---

## §3 · The queue — to decide with the owner

- **Decided, to brief first** (D<n>): <…>.
- **Next**: <…>.
- **Upcoming**: <…>.

---

## §4 · The traps seen since the last checkpoint

- <trap — countermeasure>.
- The other traps are in §7 of the method and still hold.

---

## §5 · The PL's cost for this session

- **Opened** on <date time>, **closed** on <date time>.
- **Work done**: <…>.
- **Context**: about <n> tokens at the last turn (target: under 700,000).
- **Main items**: <…>.

---

## §6 · The documents

**In the `<Project>` repository** (source): <list, with their version>.
**The workstreams board**: `workstreams.html`, published as an artifact at <link> — to republish at the same link.
**In the `<Project>-App` repository**: the code, `bench/` (v<n>), `DEV_PROMPT_<P>.md` (v<n>), `batches/…`.
**In the project, as a mirror**: <list>.
**In the project, written once**: <list>.
**Outside the project, to upload in the next session**: `PL_HANDOVER_PROMPT_<P>_v<n>.md`, **and nothing else**.
