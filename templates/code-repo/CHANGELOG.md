# CHANGELOG — <Project>

*One entry per version, the most recent first. The text of each entry comes from the brief, word for word; the dev
adds their file lines to it as sub-bullets indented by two spaces.*

*Two regimes (method §2, step 6). **Deployed per batch**: each batch opens its `v<X.Y>`
entry, the version it computed when taking the deliverable; then keep the “Unreleased” section empty, or delete it.
**Released**: a batch carries no version, it completes the “Unreleased” section, at the top; at the release, which the
owner asks for, the PL fixes the number by the rule below, renames “Unreleased” to `v<X.Y.Z> — <date>` and opens a new,
empty “Unreleased” section at the top. **Derived data** (a file to drop on a server, packages to rebuild) that a batch
produces is entered in “Unreleased” under “To drop after the release: <what, from where, to where>”; the release ends
with those drops, in the same gesture.*

**Numbering rule** (deliverable published by release): ⟨for example: major if a produced file changes shape, minor for a
new function, patch otherwise⟩.

## Unreleased

- <text from the brief, word for word>
  - `<file>` — what changed in it (functions, rules).
- ⟨To drop after the release: <what, from where, to where> — only if the batch produces derived data.⟩

## v<X.Y> — <date>

- <text from the brief, word for word>
  - `<file>` — what changed in it (functions, rules).
