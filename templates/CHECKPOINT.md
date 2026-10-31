# CHECKPOINT — <Project> · <domain> · `v<X.Y>`

**Session active: none — free since <date, time>.** *(or: `<short id>`, since <time> — the last eight characters of the
session's identifier, the one in the session attribution line of its commits)*

> **Resume** — the owner pastes into a new conversation of the project, with Opus: “You are Opus-PL-<Domain>.
> Resume: attach with push access the repositories <owner> <Project>, <Project>-App⟨, <Project>-Batches, the domain's
> other repositories⟩ (one clone at a time), git pull in <Project>, read `<Folder>/CHECKPOINT_<DOMAIN>.md` in full
> (§0 first) and follow it.” First move: set the baton above by a push.
> *The line names **all the domain's repositories**: a session's safeguard refuses an attachment the owner has not
> asked for in so many words, and the pasted line stands for that request.*
### <date, time> · <PL session> · entry point of the next session · replaces the checkpoint of <date>

> *Source: private repository `<owner>/<Project>`, `<Folder>/CHECKPOINT_<P>.md`. The claude.ai project holds a mirror of
> it under the same name, copied over by the PL.*
>
> *The checkpoint states the **real** state, measured — not the hoped-for state. It is rewritten in full at each handover.
> **It fits in 10 KB** (10,240 bytes): the fixed line, the baton, the state, the queue, what is needed to resume; the
> history goes to a domain archive (`<Folder>/Archives/CHECKPOINT_<DOMAIN>_ARCHIVE_<date>.md`). Check 10 of the checker
> flags it.*

---

## §0 · Where we are

- **<Project> is at `v<X.Y>`.** Code fingerprint `<…>`; ritual replayed on <date>: compliant, `<n> passed`.
- **The code repository**: `main` at `<sha>`; the deployment archive is `git archive` of `main`.
- **Since the previous checkpoint**: <the batches delivered, one line each, with their version and their D>.
- **The method** is at v<n> (<what changed>).
- **The decision log**: numbers are reserved by a push at the moment of writing (method §1a) — never from this file.
- **Open debts**: `<id>` — half a line each (every debt has its workstream, cited by its id).
- **To do by the owner**:
  - <tag and release to set, on which commit, with which text>;
  - <deliverable to upload, exact name and sha256>;
  - <merged branches to delete on GitHub: …>.
- **In flight**: `<id>` — <what is waiting for a test or an outside answer>.

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

*This section — `## §<n> · The queue`, §3 here — **carries the list itself**, never a pointer (“everything is in §0”).
The queue carries only **registered workstreams** (method §6): each subject is cited by its `workstreams.yaml` id,
between backticks. A subject that has no workstream yet is registered **first** (upcoming, to brief or debt), then
cited; a closed workstream (accepted or archived) leaves the queue. At every resume and every handover, re-read this
queue against `workstreams.yaml`. The start of this title is the one `queue:` carries in the domain table
(`Method/domains.yaml`): if it is renamed, the `queue:` line of its domain changes in the same commit — the only line of
the table a PL touches.*

- **Decided, to brief first** (D<n>): `<id>` — <…>.
- **Next**: `<id>` — <…>.
- **Upcoming**: `<id>` — <…>.

---

## §4 · The traps seen since the last checkpoint

- <trap — countermeasure>.
- The other traps are in §7 of the method and still hold.

---

## §5 · The PL's cost for this session

- **Opened** on <date time>, **closed** on <date time>.
- **Work done**: <…>.
- **Context**: about <n> tokens at the last turn (target: under 450,000; handover at 550,000 at the latest).
- **Saturation signs seen**: <losing the thread, contradictions, a forgotten decision — or “none”> (they serve to
  recalibrate the threshold on measurements).
- **Main items**: <…>.

---

## §6 · The documents

**In the `<Project>` repository** (source): <list, with their version>.
**The workstreams board**: `workstreams.html` (the fixed page) and `workstreams.json` (its data), published together as
an artifact at <link> — to republish at the same link, both together (method §6).
**In the `<Project>-App` repository**: the code, `bench/` (v<n>), `DEV_PROMPT_<P>.md` (v<n>), `batches/…`.
**In the project, as a mirror**: <list>.
**In the project, written once**: <list>.
**Nothing to upload to the next session**: it resumes with the fixed line at the top of this file.
