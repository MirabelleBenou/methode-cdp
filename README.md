# PL method — package

*Version française : [fr/](fr/README.md).*

A development method with Claude: a **project lead** (PL, Opus) who decides with you, writes the briefs, launches the
dev as a sub-agent and accepts; a **dev**, whose model and effort mode the PL chooses for each batch, who builds one
batch at a time; you, who decide and validate on screen. Everything flows through GitHub.

**Start with [`GUIDE.md`](GUIDE.md).** One PL, several independent modules, or linked modules with a coordinator:
`GUIDE.md` §2a.

| path | holds |
|---|---|
| `GUIDE.md` | the instructions for use, the three-layer architecture, the actions to start a project |
| `1_PROJECT_INSTRUCTIONS.md` | the text of a claude.ai project's instructions |
| `2_PL_BOOTSTRAP_PROMPT.md` | the first message of the first PL session |
| `3_GITHUB.md` | the repositories, the circuit of a batch by branch, the session pitfalls |
| `templates/` | method, dev prompt, brief, dev command, local runner, living docs, repository skeletons; optional: the server runner (`SERVER_RUNNER.md`) and its reference implementation (`server-runner/`, in French), the living-docs arbiter (`ARBITER.md`, mode C) |
| `skill/SKILL.md` | the personal skill `methode-cdp`, to customize (§1 and §8) then install |

*Package v11, 29 October 2026 — history in `GUIDE.md` §7. MIT License.*
