# DECISION LOG — <Project> · **living**
<!-- v1 -->

*Kept by the PL. Updated at each closed batch. Last update: **<date>, by <session>**: **D1**.*

> **This log carries only what is still alive.** **An entry fits in ~800 characters.** **The log is cut into slices of
> fifty numbers when it exceeds ~150 KB**: what is no longer alive moves to a frozen archive, one per slice
> (`Archives/DECISION_LOG_ARCHIVE_D<a>_to_D<b>.md`), which is never rewritten. The numbers stay stable from one
> document to the other. **An archived decision that changes is replayed here, under a new number that cites the old one.**

---

## §0 — What this document is for

Every decision that commits the project — product, visual, technical, method — carries a stable **D** number.
A brief, a workstream, a method cite their D numbers. A decision once made is not reopened; it is replaced by a new one.

**An entry states** — in ~800 characters; the detail goes to the batch folder or into a domain note, the entry only keeps
the summary and the path:
- **what is decided**, in one sentence in bold;
- **by whom**: “Decided by the owner” (in their own words when the words decide, the option chosen, the time if useful) /
  “Decided by the PL” (delegated technical decision);
- **on what basis**: the measurement the decision rested on;
- **the batch** and its result (dev, duration, stops, acceptance, fingerprint, validation in production).

**A “What the batch teaches” entry** follows a batch when there is a lesson: numbered ①, ②…; each correct stop or
report by the dev counts there (“execution is right”), each PL defect seen in production opens the reverse
count.

---

## §1 — Decisions made

| # | decision | made by | batch |
|---|---|---|---|
| **D1** | **The project adopts the PL method** (PL method package v<n>). The owner, <date>: <answers to the bootstrap — deliverable, deployment, versioning, stack>. Decided by the PL: <the rest>. Repositories: `<owner>/<Project>` (living docs), `<owner>/<Project>-App` (code). | The owner, PL | bootstrap |

---

## §1a — The “execution is right” count

> **As of <date>: <n> for execution, <n> for the reverse count.**
> *It is the reason for the “what I'm not sure about” section required at each delivery.*
> **At every cut of the log**, the count of the entries that leave for the archive is carried over here as a base
> (“base D1–D<b>: <n> for execution, <n> for the reverse count”), and the entries that remain are added to it: the count
> is not lost with the archive.

---

## §2 — Awaiting a decision

*What the owner will decide — each entry with its options and the PL's recommendation.*

---

## §3 — What is not up for decision

- **AA contrast** is a safeguard, not a matter of taste. An unreadable text is fixed without a decision.
- **Every clickable element must be reachable by keyboard.**
- **The texts produced stay gender-neutral.**
- <the project's permanent rules>
