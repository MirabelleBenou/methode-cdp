# THE DEV COMMAND — the sub-agent launch, and the fallback line

*The PL launches the dev themselves (`Agent` tool, in the background), with the model and effort mode of the brief. The dev
starts **without the PL's context**: this command is all they know beyond the repository. It comes in four parts.*

---

## A · The command, in four parts

```
1 · WHO YOU ARE AND WHAT YOU DO
You are the dev of batch `v<X.Y>` of <Project>. You work alone, with no one to talk to: you read, you execute, you deliver, you report.
Document to execute: batches/v<X.Y>/<BRIEF.md | ADDENDUM_<n>.md>, on branch batch/v<X.Y> of repository <owner>/<Project>-App <public code: <owner>/<Project>-Batches; the code starts from commit <sha> of the public repository <owner>/<Project>-App, where you push the code alone>, starting commit <sha>.
Read first, in this order: DEV_PROMPT_<P>.md (root of the branch), the brief, its addenda <and your previous reports: …>. The only images to open: <none | names>.
Expected report: batches/v<X.Y>/<DEV_REPORT.md | DEV_REPORT_<n>.md>.

2 · THE PRACTICAL CONDITIONS — they take precedence over the brief and the prompt
- The repositories are already attached to this session: call neither add_repo nor register_repo_root.
- Your clones go in /home/claude/dev_<batch>/, never in the PL's copies. Generous command timeout for the clones.
- You push only to batch/v<X.Y>: never to main, never a tag, never --force; fast-forward, after a fetch.
- <The commit-message trailer lines imposed by the session, if any.>
- <The tools already present: browser at such path, do not reinstall it; interpreter version.>

3 · THE STOPS
A point that is ambiguous, impossible, or contradicts the real state of the code: write batches/v<X.Y>/STOP_<n>.md, commit, push the branch, then stop and say so in your reply. Do not decide.

4 · YOUR FINAL REPLY, FOR THE PL
- the full hashes: delivery commit, report commit;
- each criterion with OK or DEVIATION;
- what you are not sure about.
```

**After a stop**: the PL pushes the addendum and relaunches — the same sub-agent if it can still be reached (follow-up
message), otherwise a new one, whose command also names the previous reports and stops to read.

**What is left to the PL in the meantime**: nothing to wait on actively; they are notified at the end. They never predict the
result of a sub-agent that is running.

---

## B · The fallback — the line the owner pastes

*When the PL cannot launch a sub-agent. The PL gives the line word for word, with, above it in bold, the model, the
effort and the session: the owner does not necessarily read the brief.*

**Sonnet · Medium · new conversation in the project**

```
You are the dev of <Project>. Attach the repository <owner>/<Project>-App (add_repo tool, push access), clone branch batch/v<X.Y>, read DEV_PROMPT_<P>.md then batches/v<X.Y>/BRIEF.md, and execute.
```

**For an addendum, in the dev session that is still open:**

```
Addendum <n> is pushed to batch/v<X.Y>: git pull --rebase, read batches/v<X.Y>/ADDENDUM_<n>.md, and resume at the step it gives.
```

*Trap seen: a dev conversation opened by hand can fail to attach a private repository; the sub-agent, for its part,
inherits the repositories of the PL's session.*
