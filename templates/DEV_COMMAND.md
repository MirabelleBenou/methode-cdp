# THE DEV COMMAND — the sub-agent launch, and the fallback line

*The PL launches the dev themselves (`Agent` tool, in the background), with the model and effort mode of the brief. The dev
starts **without the PL's context**: this command is all they know beyond the repository. It comes in four parts.
**The standing conditions are in the dev prompt** (`templates/DEV_PROMPT.md`, §1, §2 and §6): **the command only repeats
what changes from one batch to the next** — the document to execute, the working folder, the branches, the commit lines.
The dev talks only to the PL: through what it pushes and through its final reply.*

---

## A · The command, in four parts

```
1 · WHO YOU ARE AND WHAT YOU DO
You are the dev of batch `v<X.Y>` of <Project>. You work alone, with no one to talk to: you read, you execute, you deliver, you report.
Document to execute: batches/v<X.Y>/<BRIEF.md | ADDENDUM_<n>.md>, on branch batch/v<X.Y> of repository <owner>/<Project>-App <public code: <owner>/<Project>-Batches; the code starts from commit <sha> of the public repository <owner>/<Project>-App, where you push the code alone>, starting commit <sha>.
Read first, in this order: DEV_PROMPT_<P>.md (root of the branch), the brief, its addenda <and your previous reports: …>. The only images to open: <none | names>.
Expected report: batches/v<X.Y>/<DEV_REPORT.md | DEV_REPORT_<n>.md>.

2 · THE PRACTICAL CONDITIONS — they take precedence over the brief and the prompt
- Your working folder: /home/claude/dev_<batch>/; never <the paths of the PL's copies>, which it occupies itself.
- You push only to batch/v<X.Y> <public code: and to batch/<batch> of the public repository, where you push the code alone>.
- End of every commit message, these lines: <the attribution lines imposed by the PL's session, copied as they are>.
- <The tools already present: browser at such path, do not reinstall it; interpreter version.>
<The attached repositories, the separate clones, the batch branches only, no background process: in the dev prompt, which carries them. A project with no dev prompt repeats them here.>

3 · THE STOPS
A point that is ambiguous, impossible, or contradicts the real state of the code: write batches/v<X.Y>/STOP_<n>.md, commit, push the branch, then stop and say so in your reply. Do not decide. A mock-up commanded: MOCKUP_<n>.md, and stop in the same way (dev prompt, §3 step 6).

4 · YOUR FINAL REPLY, FOR THE PL
- the full hashes: delivery commit, report commit;
- each criterion with OK or DEVIATION;
- what you are not sure about.
```

**After a stop or a mock-up**: the PL pushes the addendum (or, for a mock-up, looks at the images, shows them to the owner
and collects their verdict) and relaunches **the same sub-agent by message** (`SendMessage`) if it can still be reached;
otherwise a new one, whose part 1 also names the previous stops and reports to read. **The owner's verdict is passed on
word for word**, without rephrasing it; a requested change makes a new round, `MOCKUP_<n+1>.md`.

**In the meantime**: the PL does not touch the paths the dev occupies — its working folder, and those the test bench
writes in hard; they are notified at the end, wait on nothing actively and never predict the result of a sub-agent that
is running.

---

## B · The fallback — the line the owner pastes

*When the PL cannot launch a sub-agent. The PL gives the line word for word, with, above it in bold, the model, the
effort and the session: the owner does not necessarily read the brief. The dev prompt then tells the dev to tell the
owner only one sentence, when it stops or delivers.*

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
