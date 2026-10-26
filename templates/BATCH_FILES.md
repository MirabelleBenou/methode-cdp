# THE FILES OF A BATCH — addendum, stop, dev report

*Three short templates. All of them live in `batches/v<X.Y>/` of the code repository, on the batch branch, outside the
deployment archive.*

---

## A · `ADDENDUM_<n>.md` — written by the PL

```markdown
# ADDENDUM <n> — <batch title> · `v<X.Y>`
### <date> · <PL session> · answers `STOP_<n>.md` | the owner's test feedback of <date>

**Dev: Sonnet · Medium · same session if it is open, otherwise a new one (which also reads the previous reports)**

## What the addendum replaces
- §<x> of the brief, rule <y>: **replaced by** … (full text, not a diff).
- Criterion C<z>: **replaced by** …

## What it adds
- Rule / criterion / authorized file: …

## Where to resume
At step <k> of the sequence. The work already committed stays (or: resumes from commit `<sha>`).

## What does not change
All the rest of the brief.
```

*A test-feedback addendum carries, word for word, the owner's requests, then the rules that follow from them.*

---

## B · `STOP_<n>.md` — written by the dev

```markdown
# STOP <n> — <batch title> · `v<X.Y>`
### <date time> · last pushed commit `<sha>`

## What stops me
<The rule, the criterion or the gate, cited by number; what they say; what I found — with the measurement.>

## Why I do not decide
<What each of the possible readings would change.>

## What I propose (without having done it)
1. <option> — <consequence>
2. <option> — <consequence>

## Where I am
<Steps done, what is committed, what is not.>
```

---

## C · `DEV_REPORT.md` — written by the dev

```markdown
# DEV REPORT — <batch title> · `v<X.Y>`
### <date> · <model, effort> · delivery commit `<full sha>`

## 1 · What I'm not sure about
<Always first. “Nothing” if there is nothing. Any existing code that seems to do what the brief asks to create.>

## 2 · The gates (measured on the archive of the delivery commit)
| gate | expected | measured | |
|---|---|---|---|
| P0 | … | … | OK / DEVIATION |

**My counts**: tests added <n>, keys added <n>, CSS rules added <n>, …

## 3 · The brief's criteria
- **C1** — met / not met — <measurement>.

## 4 · The mock-up (if there is one)
Images shown; the owner's words of validation; each request word for word and what I did with it; rounds; fingerprint
noted at validation.

## 5 · The raw outputs
<ritual, tests, lint, syntax, migration, fingerprint — as is>

## 6 · The deviations from the brief
<Even minor ones, with their reason.>

## 7 · The method
Start <time>, end <time>; interventions <n>; what slowed me down.
```
