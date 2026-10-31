# The local runner, the fallback — Claude Code on the PC, driven by files · v2
### 25 October 2026 · proven on a real project (screenshots of a game installed on the PC)

> **The bridge first.** Since the Claude app offers a **bridge** when the owner's machine is linked — linked folders
> (read, write), a terminal if one is offered, the screen through computer use, the owner validating the access in the
> PL's conversation —, **the PL's session works on the machine itself** (method §1, skill §5a). **This document now
> describes the fallback**, for when the bridge is not offered. Reason for this rank: driven by files, the runner got stuck
> when the owner was away from their machine — screen-access requests refused, endless waiting.

*For work that must run **on the owner's PC** (a game, an installed application, the screen, a piece of hardware) and
that the PL, in the cloud, cannot execute. The rest of the method does not change: the PL briefs and accepts, the runner
executes, the owner decides.*

---

## 1. When to use it

- **When the bridge is offered**, the PL works on the machine itself: this document is not needed.
- **When the bridge is not offered** (the machine is not linked, or its terminal is not offered), the PL sees at best the
  PC's folders (folders connected to the conversation: list, read, write files), but **has no terminal there**: they
  launch nothing on the machine.
- The PL's control of the screen does not replace a shell: terminals and editors there are click-only (no
  typing).
- As soon as something must be **executed** on the PC (a Python script, a program, a full-resolution screenshot) and the
  bridge does not allow it, it goes through a **local Claude Code session**: Desktop app, Code tab, **Local** environment. That is the runner.
- A batch that only touches code in a repository stays with the dev as a sub-agent, in the cloud (method §5).

## 2. The roles

| | does | does not |
|---|---|---|
| **PL** (cloud) | writes briefs and addenda in the project space; reads the outputs; gives the green light; answers the questions; re-measures cold; files into the repository | executes nothing on the PC, at the fallback |
| **Runner** (local Claude Code, Sonnet) | reads the brief, executes, writes its state and its questions as files, writes the report | decides nothing outside the brief; does not talk to the owner in its chat once the sync is started |
| **The owner** | pastes **one line** per brief or addendum; accepts the permissions; makes the physical moves asked for (launch the game, a setting on screen) | does not relay messages between the two |

## 3. The project space on the PC

**Never in an application's folders** (game, software): everything lives under `<root>\<Project>\`, created by the PL —
`<root>` is a folder of yours, the same for all your projects (for example `D:\Claude_AI`).

```
<root>\<Project>\
  README.md    this layout
  briefs\      briefs and addenda — written by the PL, the runner does not write there
  reports\     the runner's reports
  tools\       the runner's scripts (+ local config.json, never published)
  out\         data produced (stays on the PC: it is data, not code)
  sync\        the dialogue through files (§4)
```

Only exception: what an application requires to be placed in its own folders (a hook, a configuration line), with a
backup of the modified file and one added line at most.

## 4. The synchronization protocol

Everything goes through `sync\`. The runner polls these files **every 5 s, with no time limit**.

| file | written by | meaning |
|---|---|---|
| `STATUS.txt` | runner | one timestamped line rewritten at each step: `2026-10-25 13:30:02 \| WAITING_GO \| hook OK, check.png ready`. States: `WAITING_GO`, `<STEP> <n>/<total>`, `QUESTION`, `STOP`, `DONE` |
| `check.png` (or any check file) | runner | a sample of the result **before** the bulk of the work, which the PL looks at |
| `GO.txt` | PL | green light; the runner deletes it after reading it |
| `QUESTION.txt` | runner | a question or a stop from the brief; `STATUS` switches to `QUESTION` |
| `ANSWER.txt` | PL | the answer; the runner deletes it after reading it |

Rules:
1. **No question in the runner's chat** once the sync is started: its chat is not displayed on the web and
   the owner is not in front of it.
2. **The PL looks at the check before giving the green light** — that is where you see a window in front of the game, a
   wrong display mode, a wrong scale.
3. If the runner needs the **foreground** (screenshot), it brings the application to the front itself and checks the
   focus before each action; three failures in a row → `QUESTION`.
4. What depends on the owner (a move, a decision): the PL asks them in their conversation, then answers through
   `ANSWER.txt`.

## 5. The typical sequence

1. The PL drops `briefs\BRIEF_<batch>.md` (form of `templates/BRIEF.md`, plus §4 above or a reference to a
   synchronization addendum).
2. The owner opens a local Claude Code session **on `<root>\<Project>`**, Sonnet, effort of the brief, new session,
   and pastes:
   `Read briefs\BRIEF_<batch>.md and execute it strictly. You are the runner: at the slightest point that is ambiguous or outside the brief, stop and say so. Dialogue through files in sync\.`
3. The runner prepares, writes `check.png`, switches to `WAITING_GO`.
4. The PL looks, writes `GO.txt`, follows `STATUS` (one check about every minute, through background waits).
5. The runner finishes, writes `reports\REPORT_<batch>.md` (which starts with “What I'm not sure about”), switches to
   `DONE`.
6. The PL **re-measures cold** on the outputs, looks at the renders, then files briefs and reports into the `-Batches`
   repository and the delivered code into the code repository (review of the diff before any public repository).
7. An addendum: the PL drops it in `briefs\`, the owner pastes one line (`Read briefs\ADDENDUM_<n>_<batch>.md and
   apply it. Dialogue still through files.`).

## 6. Traps seen

- **The runner stops on a permission request** (run a command, write outside its folder, delete):
  it is displayed only in the Desktop app. Symptom: `STATUS` frozen. The PL warns the owner, who accepts it.
- **A window in front of the application** (the conversation, a notification) spoils a screenshot: hence the check and the
  focus verification.
- **A working folder opened somewhere other than the project space** forces access permissions at every
  step: open the local session directly on `<root>\<Project>`.
- **The runner's shell can block a deletion** when it has the target folder as its current directory.
- **PC-specific paths** (working folder, application install, screen size) go in a local
  `config.json` ignored by git, never hard-coded in the published code.
