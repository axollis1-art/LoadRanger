---
name: triage
description: >
  Survey every open issue, group it by label, flag the ones rotting (unlabelled,
  stale, blocked, no plan), and recommend the two or three things to actually
  pick up next — with a reason for each. Use when the user says "triage",
  "/triage", "what should I work on", "what's outstanding", "review the backlog",
  "what's next", or has opened enough issues to have lost track.
---

# triage

The failure this prevents: opening fifteen issues, then freezing because the list
is undifferentiated and every item looks equally urgent. A backlog you can't
navigate is worse than no backlog, because it also makes you feel guilty.

Run it weekly, or whenever the list stops being obvious.

## 1. Pull the real state

```bash
gh issue list --state open --limit 100 \
  --json number,title,labels,updatedAt,comments,assignees
gh pr list --state open --json number,title,isDraft,statusCheckRollup
```

Don't work from memory of what you filed. The gap between what you *think* is
open and what *is* open is the whole reason to run this.

## 2. Group and flag

Group by type label (`bug` / `feature` / `chore` / `docs`) and surface the
tracking issues (`plan`) separately — those are containers, not tasks.

Flag anything rotting:

| Flag | Means | Do |
|---|---|---|
| **unlabelled** | Won't ever be found by a filter | Label it now, in this run |
| **stale** | No update in 30+ days | Close it, or say why it's still live |
| **blocked** | Waiting on something external | Name what, and whether that's real |
| **no steps** | A `plan` issue with no checklist | Run `/plan-work` on it, or demote it |
| **open PR, no issue** | Work with no written why | Fine for a one-liner; suspicious otherwise |

**A stale issue is a decision you've been deferring, not a task you've been
failing at.** Closing it is a legitimate and usually correct outcome — say
`closing: superseded by #N` or `closing: not doing this` rather than letting it
accumulate. An issue list you trust is worth more than one that's complete.

Also check the `blocked` ones are really blocked. A blocker you inferred but never
confirmed is a claim like any other (`AGENTS.md` habit 3), and an imaginary one
costs more than a collision would have.

## 3. Recommend what's next

Pick **two or three**, no more, with a one-line reason each. Rank by:

1. **Blocking something else** — unblocking work is worth more than starting it.
2. **Cheap and done** — a small issue you can close today beats a large one you
   can start. Momentum is a real input, not a soft one.
3. **Decaying** — anything that gets harder the longer it waits: a dependency
   drifting, a half-finished refactor, a deadline.
4. Everything else is backlog. **Say so explicitly** — naming what you are *not*
   doing is most of the value of a triage.

## 4. Output

```
Open: <n> issues, <n> PRs

Pick up next:
  #12  <title>  — blocks #15, and it's a 20-minute change
  #7   <title>  — half-done already; finishing beats restarting later
  #21  <title>  — the parser refactor gets worse every week it waits

Rotting:
  #3   unlabelled — labelled `chore` in this run
  #9   stale 6 weeks — close? superseded by #12
  #18  `plan` with no checklist — run /plan-work on it

Backlog (not now): #4 #11 #14 #19 #22
```

## 5. Apply the cheap fixes now

Labelling, closing something obviously dead, and adding a missing dependency note
are reversible and take seconds — do them and say what you did. **Ask before
closing anything with real content in it.**

## Cross-references

- `/plan-work` — for any issue big enough to need a checklist.
- `/run-plan` — executes the one you picked.
- `/retro` — if the same thing keeps rotting, the problem isn't the issue.
