---
name: plan-work
description: >
  Turn a settled design into a GitHub tracking issue that a session with no
  memory of this conversation can execute — goal, done-when, non-goals, and an
  ordered checklist of steps each carrying its own acceptance check. Labels it
  and prints the issue number. Use when the user says "plan this out",
  "/plan-work", "write the plan", "break this down", "file this", "make an issue
  for this", or when work is about to span more than one sitting.
---

# plan-work

Chat history does not survive. A plan that lives only in the conversation gets
re-explained every time you come back, drifting a little each time. Writing it
into an issue once is the cheapest thing you will ever do — and it gives you a
thing to close, which is most of the motivation.

This is the small version of the "epic" pattern used on larger teams: **the issue
is the source of truth, not the conversation.**

## 1. Don't plan an unsettled design

If the shape is still ambiguous, run `/grill` first. Planning an ambiguous design
just moves the ambiguity into an issue, where it looks decided.

If it's a "new" feature, run `/prior-art` first — and search the **existing
issues** as part of that. The cheapest step is the one already built, and the
second cheapest is the one already written up.

```bash
gh issue list --search "<the user's own words, not your mechanism name>" --state all
```

## 2. Write one tracking issue

Default shape: **one issue, with the steps as a checklist in the body.** For a
handful of steps this is far lighter than an issue per step, and it still gives
you labels, a close, and a permalink.

```bash
gh issue create --title "<title>" --label "plan" --body-file <(cat <<'EOF'
**Goal:** <2-3 sentences. What we're building and why, written for someone who
was not in the room.>

**Done when:** <the observable thing that is true at the end — a command that
passes, an output that's correct, a page that renders>

**Not doing:** <explicit non-goals, so scope doesn't creep mid-build>

**Watch out:** <the step most likely to be wrong; the assumption you couldn't
verify>

## Steps

- [ ] **1. <name>** — <what to do>
      Files: `<paths>` · Check: `<the command that proves it>`
- [ ] **2. <name>** — <what to do> (needs: 1)
      Files: `<paths>` · Check: `<command>`
EOF
)
```

**Write the body to a file or a heredoc — never inline it in a double-quoted
argument.** A shell will run every `` `backtick span` `` in your prose as a
command and silently delete it from the issue.

**Escalate to sub-issues only when a step deserves its own discussion or its own
PR** — something you'd want to review separately, or hand to someone else. Then
reference them from the checklist (`- [ ] #12`) and GitHub tracks the progress
bar for you. Don't do this by default; six issues for a day's work is friction.

## 3. What makes a step a good step

- **Self-contained.** Executable by someone with no memory of this conversation.
  If it needs the chat to make sense, rewrite it. Apply this to every step before
  you create the issue — it is the whole test.
- **Ordered by dependency**, and say the dependency (`needs: 1`). If steps are
  independent, say that too; it's useful.
- **Independently finishable.** A step should end somewhere you could stop for the
  day with the repo still working. If it can't, it's two steps.
- **Carries its own acceptance check** — the literal command, not "verify it
  works". Per `AGENTS.md` habit 1, a step with no check isn't a step, it's a hope.
- **Small.** Five to ten steps is healthy. Twenty means the design isn't settled;
  go back to `/grill`.

## 4. Label it

Labels are what make the issue list navigable once there are more than ten. Use
the small set (see the pack's `setup-labels.sh`): `plan` for this tracking issue,
plus one type label — `bug`, `feature`, `chore`, `docs`.

One type label per issue. A label nobody filters on is noise; if you never type
`--label X`, delete X.

## 5. Stop

**Create the issue; do not start building.** Print the issue number and wait. The
whole value is that the misunderstanding gets caught now, when it costs one
message, rather than after four steps are built on it.

## Fallback: no GitHub remote

If the repo has no GitHub remote (`gh repo view` fails), write the same content
to `docs/plans/<NN>-<slug>.md` and commit it, then say clearly that you used the
file because there was no remote.

**One or the other, never both.** Two copies of a plan drift, and the stale one is
always the copy nobody is looking at (`AGENTS.md` habit 7).

## Cross-references

- `/grill` — settle the design first; this records a settled one.
- `/prior-art` — check it isn't already built or already filed.
- `/run-plan` — what executes what this produces.
- `/triage` — what to do once several of these exist.
