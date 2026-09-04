---
name: handoff
description: >
  Emit a self-contained resume prompt so a brand-new session can continue this
  work with zero access to the current conversation. Surveys real state (branch,
  open PRs, what's done, what's next, the exact next command, key file paths) and
  prints a paste-ready block. Use when the user says "handoff", "give me a
  copy/paste", "hand this off", "start a fresh session", "continue in a new
  session", "resume prompt", or "what do I paste to keep going".
---

# handoff

Kills the biggest recurring tax in agentic coding: re-explaining the task to a
fresh session because the last one ran out of context or got closed.

## 1. Survey the real state — don't write from memory

Gather the facts a cold session needs, using actual commands:

```bash
git branch --show-current
git status -s
git log --oneline -10
git worktree list          # if you use them
gh pr list --search "is:open author:@me"   # if you use GitHub
```

Also collect: what's already landed, what's still open, the **literal next
command** to run, and the file paths involved.

**Survey first, write second.** A handoff written from memory is exactly as
unreliable as the memory it was written from.

## 2. Emit the resume block

Paste-ready Markdown, every section self-contained. A reader with no chat
history must be able to act on it:

```
## Resume: <one-line what this is>

**Goal:** <2-3 sentences: what we're doing, where we are, why it matters>
**Repo / branch:** <repo> @ <branch> (<clean|dirty>)
**Done:** <bullets — what's landed, with PR numbers / commit shas>
**Next:** <bullets — what remains, in order>
**Run this first:** `<the exact next command>`
**Key paths:** <file:line pointers the next session will need>
**Watch out:** <gotchas, half-finished edits, anything that will bite>
```

Keep it tight. Cite commits and PRs by number/sha so they're verifiable rather
than merely asserted.

## 3. Print, and offer to save

- **Print it inline** by default — they asked for something to paste.
- **Offer to save** it to `docs/handoffs/<slug>.md` or `~/.claude/plans/` when the
  work resumes later or on another machine. Say the path.

## 4. Discipline

- **Verify before claiming.** `git rev-parse` any commit you cite; confirm a PR
  exists before naming it. A handoff that describes intended work as finished is
  worse than no handoff — the next session builds on a false floor.
  If something is drafted but uncommitted, say *"drafted in `<path>`, not
  committed"*. If it was never started, say *"not started"*.
- **Self-contained or it failed.** If any line needs the chat history to make
  sense, rewrite it. That is the entire test.
- **Prefer a tracking issue for heavyweight work.** If the remaining work spans
  several sittings, a resume prompt is the wrong container — it captures a
  *moment*, not a *structure*. Run `/plan-work` instead, then let the handoff
  block just say "continue issue #12 from step 3". That survives indefinitely;
  a pasted prompt survives until you lose the tab.

## Cross-references

- `AGENTS.md` Part 2, "Write the issue, not the chat message" — the habit this
  skill serves.
- `/wrap-session` — the fuller end-of-session tidy; use `/handoff` when you are
  stopping **mid-task** rather than finishing.
