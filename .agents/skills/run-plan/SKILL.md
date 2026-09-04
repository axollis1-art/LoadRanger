---
name: run-plan
description: >
  Pick up a GitHub tracking issue with no memory of the conversation that
  produced it and execute it step by step — one commit per step, each step's own
  check run before its box is ticked, the issue updated as you go, and the issue
  closed by the final PR. Use when the user says "run the plan", "/run-plan",
  "work issue #N", "continue the plan", "carry on with #N", or points at an issue.
---

# run-plan

Executes what `/plan-work` produced. Designed to work **cold** — the issue is the
only input you need, and if it isn't enough, that's a bug in the issue.

## 1. Read the issue, and only the issue

```bash
gh issue view <N> --comments
```

Read the body **and the comments** — a decision made after filing usually lives in
a comment, and it supersedes the body. If no issue was named and several are open
with the `plan` label, **list them and ask**; never guess which one.

Then check the ground truth, because plans go stale:

```bash
git log --oneline -10        # has some of this already landed?
git status -s                # half-finished work in the tree?
gh pr list --search "<N>"    # is there already a PR for this?
```

If a step is done but unticked, tick it and say so. If the repo contradicts the
issue, **stop and say so** — don't quietly re-plan. A plan that disagrees with
reality is a decision for the user, not a problem to route around.

## 2. Take the first unticked step whose dependencies are met

One step at a time, in dependency order. Don't batch several because they look
small — the ticking is what makes progress legible when you come back tomorrow.

## 3. For each step

1. **Build it** — just that step. Resist the adjacent improvement you notice; if
   it matters, add it to the checklist instead of doing it now.
2. **Run the step's own `Check:` command.** Not a proxy for it, the actual one.
3. If the check involves a test you just wrote, **break the code and watch it go
   red** before believing it (`AGENTS.md` habit 2). A test written against working
   code has not yet shown it can fail.
4. **Commit** — one commit per step, message naming the step.
5. **Tick the box on the issue:**
   ```bash
   gh issue edit <N> --body-file <(gh issue view <N> --json body -q .body | sed 's/- \[ \] \*\*1\./- [x] **1./')
   ```
   Read the body back after editing and confirm the right box moved. A `sed` that
   matched nothing exits 0 and rewrites the body unchanged — silently.

If a step fails unexpectedly, run `/dig` before patching. The bug you're looking
at is usually a sample of several.

## 4. When the plan is wrong

Plans are written before the work and are sometimes wrong. That's fine. Silently
diverging from one is not.

- **Small correction** (a path moved, a command changed) — fix the checklist as
  you go and say so in one line.
- **A step is unnecessary** — tick it as `(skipped: <why>)` rather than deleting
  it. The reason outlives the tidiness.
- **The design is wrong** — stop. Comment on the issue saying which step exposed
  it and what it implies, then raise it. Don't rebuild the plan mid-run; that's a
  `/grill` and a new issue.

Put these in an issue **comment**, not just the chat. The comment is what the
next cold session reads.

## 5. Link the work to the issue

In the PR body (or the final commit message):

```
Closes #<N>
```

GitHub then closes the issue automatically on merge, and the issue permanently
links to the code that resolved it. This costs one line and is the single most
useful habit in issue-driven work — six months later it's how you find out *why*
a change was made.

Use `Refs #<N>` for a PR that advances the issue without finishing it.

## 6. Finishing

When every box is ticked, verify the issue's **`Done when:`** line — the whole
thing, from the outside, at the layer the user sees it. That's a different
question from "every step passed", and it's the one that matters
(`AGENTS.md` habit 1).

Then report:

```
Issue #<N>: <title> — complete
Shipped:   <commits / PR / what now works>
Deviated:  <steps changed or skipped, and why>
Left over: <anything deferred — and the issue number it's now filed under>
```

Anything deferred gets **its own issue**, not a sentence in the chat. If
`Done when:` does **not** hold despite every box being ticked, say so plainly —
it's the most useful sentence in the whole run, because it means the plan was
missing something.

## Cross-references

- `/plan-work` — produces what this consumes.
- `/dig` — run on any unexpected failure rather than patching in place.
- `/handoff` — if you stop mid-plan, points a fresh session at the issue and step.
- `AGENTS.md` habits 1 and 2 — the acceptance and test discipline behind steps 3
  and 6.
