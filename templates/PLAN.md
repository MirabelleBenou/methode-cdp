# IMPLEMENTATION PLAN — <Project> · v1
### <date> · <PL session>

> *The roadmap by phases, and the version log. The detail of the workstreams lives in `workstreams.yaml`, the
> decisions in the decision log: the plan does not copy them, it cites them.*

---

## §1 · The product

<What it is, for whom, in a few lines. Its modules or sub-projects. Where it is deployed.>

## §2 · The architecture

<The stack, the main pieces, the data flows. What is an invariant (moves only on authorization).>

## §3 · The screens / the modules

| letter | screen or module | state | refs |
|---|---|---|---|
| A | <…> | upcoming / delivered `v<X.Y>` | D<n> |

## §4 · The visual direction

<The principles decided (D<n>), the style guide if there is one (reference written once to the project).>

## §5 · The phases

| phase | content | state |
|---|---|---|
| 0 | the test bench (tooling batch) | upcoming |
| 1 | <…> | |

## §6 · What is out of scope

<What we decided not to do, with the D reference.>

---

## §11 · The version log

*Append only. One line per closed batch, at its close. **It is the only source of a batch's facts**: the decision log,
`workstreams.yaml` and the checkpoint cite it (the version or the batch's name), they do not repeat it (method §6). This
log does not say that a version was handed over then refused — the number rule reads the batch branches and
`workstreams.yaml` (the method, §2, step 6; open and archived).*

*The form of a line: the version (a deliverable deployed per batch) or the batch's name (released, with no version);
the date; the title; the dev (model, effort); the duration; the stops (their number, “none”); the acceptance
(compliant, addendum); the fingerprint of the delivered code; the validation (in production, by the owner, the date — or
“merged after acceptance” for a released deliverable); the D numbers.*

| version or batch | date | batch | dev | duration | stops | acceptance | fingerprint | validation | refs |
|---|---|---|---|---|---|---|---|---|---|
| `v<X.Y>` | <date> | <title> | <model, effort> | <duration> | <n, or none> | <compliant / addendum <n>> | `<fingerprint>` | <in production, <date>> | D<n> |
