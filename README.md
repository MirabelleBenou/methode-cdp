# PL method — package

*Version française : [fr/](fr/README.md).*

A development method with Claude: a **project lead** (PL, Opus) who decides with you, writes the briefs, launches the
dev as a sub-agent and accepts; a **dev**, whose model and effort mode the PL chooses for each batch, who builds one
batch at a time; you, who decide and validate on screen. Everything flows through GitHub.

**Start with [`CORE.md`](CORE.md)**: it is enough for an owner alone with a PL to start, with the table of
extensions to add when a sign you have lived through calls for it. Then [`GUIDE.md`](GUIDE.md); one PL, several
independent modules, or linked modules with a coordinator: `GUIDE.md` §2a. The terms are in
[`GLOSSARY.md`](GLOSSARY.md); what the method assumes of the Claude product, in
[`CLAUDE_DEPENDENCIES.md`](CLAUDE_DEPENDENCIES.md). **The method has been proven on three projects, one of them
complex** (several PLs in parallel on several products, a production server).

| path | holds |
|---|---|
| `CORE.md` | to read first: the method of a single PL, enough to start, and the table of extensions |
| `GLOSSARY.md` | every term of the method and the document where it lives |
| `CLAUDE_DEPENDENCIES.md` | the functions of the Claude product the method depends on, what breaks if one changes, the fallback |
| `GUIDE.md` | the instructions for use, the three-layer architecture, the actions to start a project |
| [`1_PROJECT_INSTRUCTIONS.md`](1_PROJECT_INSTRUCTIONS.md) | the text of a claude.ai project's instructions |
| [`2_PL_BOOTSTRAP_PROMPT.md`](2_PL_BOOTSTRAP_PROMPT.md) | the first message of the first PL session |
| [`3_GITHUB.md`](3_GITHUB.md) | the repositories, the circuit of a batch by branch, the session pitfalls |
| `templates/` | method, dev prompt, brief, dev command, local runner (the fallback), living docs and their scripts (board, checker, workstream archiving and search), repository skeletons; optional: the server runner ([`SERVER_RUNNER.md`](templates/SERVER_RUNNER.md)) and its reference implementation (`server-runner/`, in French), the living-docs arbiter ([`ARBITER.md`](templates/ARBITER.md), a daily GitHub Action), the document controller ([`CONTROLLER.md`](templates/CONTROLLER.md), a weekly session) and the domain table they read (`domains.yaml`); the tests of the scripts, of the links and of the parity (`tests/`) |
| [`skill/SKILL.md`](skill/SKILL.md) | the personal skill `methode-cdp`, to customize (§1 and §8) then install |

*Package v22 (skill v21), 1 November 2026 — history in `GUIDE.md` §7. MIT License.*
