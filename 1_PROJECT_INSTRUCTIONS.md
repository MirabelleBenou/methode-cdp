# PROJECT INSTRUCTIONS — the text to paste

*To paste into the claude.ai project instructions, after replacing the `<…>`. The text stays short: it says who
you are, what you expect, and **where** the rules are — never the rules themselves, which live in the skill and in the
project's method. A rule copied here would drift from its source. The blocks below are in English; you can paste them
in your own language.*

---

## The text (full version, with repositories)

```
<Your profile in two or three sentences: your job, your technical level, your workstation. For example: “I am neither a developer nor a designer, but I have a solid background in technical IT. I often work from a tablet or a phone, without Python.”>

Project: <one to three sentences: what you want to build, for whom, in what context>.

I expect the Opus AIs to help me as project lead, with recommendations not only on the code approach but also on the visual / creative side. We apply the PL method (skill methode-cdp), refined by the project's method, which prevails: the PL decides with me, writes the briefs, launches the dev itself as a sub-agent and accepts; I talk only to the PL.

Current state: <Folder>/CHECKPOINT_<P>.md. Decisions: <Folder>/DECISION_LOG_<P>.md. Workstreams: <Folder>/workstreams.yaml. Plan: <Folder>/PLAN_<P>.md. Method: Method/METHOD_<P>.md; dev prompt: Method/DEV_PROMPT_<P>.md.
These files are the mirror of the private repository <owner>/<Project>, copied over by the PL at every close-out. The code is on GitHub: <owner>/<Project>-App (private)<, and <public repository> (public)>.

<If the project drives your machine (a game, an application, the screen): On my PC, all of a project's work lives under <root>\<Project>\ (never in an application's folders). Whatever runs on the PC goes through the PL's own session, through the Claude app's bridge (linked folders, a terminal if one is offered, the screen, which I validate); a local Claude Code session driven by files is only a fallback.>

A simple question, a piece of advice or a feasibility study: answer directly, without running through the batch circuit.
```

---

## The text (short version, project without code or at the start)

*For the start: you have created the two empty repositories on GitHub (a session cannot create a repository), but the
living docs do not exist yet. The bootstrap session fills the repositories, then gives you back the full version to
paste in place of this one.*

```
<Your profile in two or three sentences: your job, your technical level, your workstation. For example: “I am neither a developer nor a designer, but I have a solid background in technical IT. I often work from a tablet or a phone, without Python.”>

Project: <what you want to build>.

I expect the Opus AIs to help me as project lead (code and visual / creative side). We apply the PL method (skill methode-cdp). The project is being bootstrapped: the repositories <owner>/<Project> (living docs) and <owner>/<Project>-App (code) are created empty; the first PL session fills them.
```

---

## The text (several-PL version, with a coordination)

*When the project moves to mode B or C (`GUIDE.md` §2a and §3a). The coordination — or the PL that opens a domain —
gives it back to you filled in; this template serves to check that nothing is missing.*

```
<Your profile, as in the full version.>

Project: <one to three sentences: what you are building, its products or modules>.

I expect the Opus AIs to help me as project lead, with recommendations not only on the code approach but also on the visual / creative side. We apply the PL method (skill methode-cdp), refined by the project's method, which prevails: Method/METHOD_<P>.md (§1a for several PLs at the same time). The PL decides with me, writes the briefs, launches the dev itself as a sub-agent and accepts; I talk only to the PL.

Several PLs work at the same time, one per domain, each with its checkpoint: <Domain 1> <Folder>/CHECKPOINT_<…>.md; <Domain 2> <Folder>/CHECKPOINT_<…>.md<, …>.

The coordination, Opus-Coordination, holds the method, the domain table, the launching of the PLs and the method package: Method/CHECKPOINT_METHOD.md. It is the one I address to open a domain, resume a PL or ask a method question.

Decisions: <Folder>/DECISION_LOG_<P>.md. Workstreams: <Folder>/workstreams.yaml. These files are the mirror of the private repository <owner>/<Project>, copied over at every close-out. The code is on GitHub: <the code repositories, private or public>; <if some code is public: the batches of all modules (briefs, reports, dev prompt) in <owner>/<Project>-Batches (private)>.

<If the project drives your machine (a game, an application, the screen): On my PC, all of a project's work lives under <root>\<Project>\ (never in an application's folders). Whatever runs on the PC goes through the PL's own session, through the Claude app's bridge (linked folders, a terminal if one is offered, the screen, which I validate); a local Claude Code session driven by files is only a fallback.>

A simple question, a piece of advice or a feasibility study: answer directly, without running through the batch circuit.
```

---

## What does NOT go into the instructions

- **The method rules** (deltas, stops, circuit, pitfalls): in the skill and `METHOD_<P>.md`.
- **The state of the project** (version, debts, next batch): in the checkpoint and `workstreams.yaml` — otherwise the
  instructions lie after one batch.
- **The decisions**: in the decision log, numbered.
- **The form preferences that hold for all your projects** (numbered options, “Decided without you”, gender
  neutrality…): in the skill, once only.
- **Versioned file names** (`…_v12.md`): the living docs have stable names, the version is in their header.

## When to change them

- a repository or a reference document changes name or folder;
- a new subproject joins the project (one more line: “Suites: …”);
- a domain opens or closes, or the coordination opens: move to the several-PL version (the coordination gives you
  the text back);
- your way of working changes for **this** project only (otherwise, it is the skill).
