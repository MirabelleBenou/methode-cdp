# BRIEF — <batch title> · `v<X.Y>`
### <date> · <PL session> · branch `batch/v<X.Y>` of `<owner>/<Project>-App` · base `<short sha of main>`

> **Template for the PL — a brief never cites it.** The brief is self-contained: together with the dev prompt, it is
> enough. It carries rules, criteria and the texts the user will read — **never ready-written code**.
> **The version**: `v<X.Y>` exists only for a deliverable **deployed per batch** (it is computed when the batch takes the
> deliverable, `main` plus one). For a deliverable **published by release**, the batch carries no version: remove `v<X.Y>`
> from the title, name the branch and the folder after the batch (`batch/<name>`), and §6 completes the “Unreleased”
> section of the `CHANGELOG` (method §1a, “The deliverable and its version”).
> Delete this box.

**Dev: Sonnet · Medium · new session** *(Opus for ⟨…⟩; High for a migration, several screens, an engine, cascading
steps)*

---

## §0 · The pieces

- **The base**: `main` at `<full sha>`. If the head of `main` is not this commit: stop.
- **On this branch**: this brief; ⟨`mock-up/…`; fixtures; images to open, by name — the only ones⟩.
- **To read before building**: ⟨the functions, by name, in the large files⟩.

## §1 · What the batch does, and why

*Two to five sentences: the owner's request (in their own words when the words decide), what the measurement showed,
what the user sees at the end.*

## §2 · The decisions and the rules

*Numbered, testable. What the owner decided (with the D reference from the decision log), then what the PL decided.*

1. **⟨Rule⟩** — ⟨detail, edge cases, what happens when the data is missing⟩.
2. …

**The displayed texts, to the character** (FR / EN):

| key | FR | EN |
|---|---|---|
| ⟨…⟩ | ⟨…⟩ | ⟨…⟩ |

## §3 · What does not move

- ⟨The modules, routes, contracts, screens, fingerprints that must stay identical — and how that is proven.⟩
- ⟨The project's invariant: unchanged.⟩

## §4 · The files

**The exact list** of what the batch modifies, adds or removes — nothing else (gate P9):

| file | change | what changes in it |
|---|---|---|
| ⟨…⟩ | modified / added / removed | ⟨functions, areas⟩ |

## §5 · The criteria and the prediction

**The “base” block** (output of the ritual on the base, line for line):

```
⟨…⟩
```

**The gates, as deltas against the base**:

| gate | base | expected | delta |
|---|---|---|---|
| ⟨tests⟩ | ⟨n⟩ | ⟨n + k⟩ | +k |
| ⟨…⟩ | | | |

**The batch criteria** (each one first run on the existing code, each one measurable on the archive):

- **C1** — ⟨what is measured, how, expected value⟩.
- **C2** — …

⟨**The prediction**: replay, fingerprint, expected output and its sha256, conditions (locale, width, theme).⟩

## §6 · The `CHANGELOG`

Text of the entry, word for word — *a `v<X.Y>` entry for a deliverable deployed per batch; for a deliverable published
by release, it completes the “Unreleased” section, with no version*:

```
⟨…⟩
```

## §7 · The batch's own stops

In addition to those of the dev prompt:
- ⟨…⟩

## §8 · The evidence

- ⟨Tests added (how many and what they cover); screen check through the DOM; end to end; mock-up or not.⟩
- ⟨Images: none / the three to six to show, by name, as crops at scale 1 for a placed piece.⟩

## §9 · The delivery

- The delivery commit, then `batches/v<X.Y>/DEV_REPORT.md` in a separate commit, pushed to `batch/v<X.Y>`.
- The deliverable: ⟨`git archive` of the delivery commit / the file `<name>` outside the zip⟩.

---

### PL checklist before pushing (remove from the brief)

- [ ] The base measured cold today, not assumed.
- [ ] The tests and the test bench searched for **the values** the batch changes, not only the symbols.
- [ ] Nothing the batch creates duplicates something that exists.
- [ ] The debts with a trigger run against the list in §4.
- [ ] Each criterion tried on the existing code; each text criterion says whether it counts comments.
- [ ] The prediction computed under the brief's rules; the expected results written to the living-docs repository, not here.
- [ ] The APIs, files and functions the rule requires, all named.
- [ ] A color rule measured on every theme; a label at the narrowest width.
- [ ] No ready-written code.
- [ ] The version computed when the batch takes the deliverable (`main` plus one) — or no version, for a deliverable
  published by release.
- [ ] Model, effort, session at the top.
