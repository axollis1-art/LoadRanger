---
name: retro
description: >
  "What can we learn?" — turn a session, a finished piece of work, or the last N
  days into ranked lessons plus the concrete skill/rule/tooling change that would
  remove each friction, and coaching on how the user prompts. Use when the user
  says "retro", "/retro", "what can we learn", "what did we learn", "how can we
  work better", "post-mortem", "lessons learned", or "review the last N days".
---

# retro

The improvement loop. Without it, the same friction is paid for every week and
nobody notices, because each individual instance is small.

## 1. Pick the scope

- **Scoped** (default) — the session that just happened, or one finished piece
  of work.
- **Broad** — the last N days across many sessions. Use this when the user asks
  "how am I working", or when the same annoyance keeps recurring.

If they didn't say, do scoped and offer broad as a follow-up.

## 2. Gather evidence, don't reminisce

For a scoped retro: what shipped, what stalled, where the time actually went,
and **every point at which the user corrected you**. That last one is the richest
signal in the whole exercise — a correction is a place where the setup let you
guess wrong.

For a broad retro, count the recurring signatures rather than eyeballing:

- **Re-explaining the task** — "as I said", "like I mentioned", a long brief
  pasted twice ⇒ reach for `/handoff` or a tracked issue.
- **Status polling** — "status?", "done yet?", "any update" ⇒ the agent should be
  reporting proactively.
- **Environment blocks** — "permission denied", "not found", "reauth", "install"
  ⇒ these are one-off fixes that pay back forever.
- **The same explanation twice** — any multi-step procedure explained more than
  once ⇒ that is a **skill** waiting to be written.
- **Rework** — code written, then thrown away. Usually means the design wasn't
  settled: `/grill` earlier next time.

Rank by **frequency × cost**, and quote the actual examples. A ranked list with
counts is worth more than three paragraphs of impression.

## 3. Output

```
Worked:   <what to keep doing — be specific, this is not filler>
Friction: <ranked, with counts and a real example each>
Lessons:  <what's now known that wasn't before>
Change:   <THE one process/skill/tooling change that pays off most>
```

**One change, not seven.** A retro that produces a list of seven improvements
produces zero improvements. Pick the one with the best ratio of pain removed to
effort, and say why it beat the others.

## 4. Apply it, don't just report it

A retro whose output is a paragraph nobody acts on has cost time and returned
nothing. In the same session:

- If the lesson is a **habit** ⇒ add it to `AGENTS.md`, with the *why* and what
  it looked like when it bit. A rule with its story attached survives; a bare
  instruction gets ignored.
- If the lesson is a **procedure** ⇒ write it as a skill in `.agents/skills/`.
  Spend most of the effort on the `description` — that's what makes the agent
  reach for it unprompted.
- If the lesson is a **tooling gap** ⇒ fix the tooling. A script, a Makefile
  target, a CI check, a pre-commit hook.
- If the lesson is about **how the user prompts** ⇒ say so directly and give the
  better phrasing side by side with what they wrote. This is the most useful and
  most-avoided part of a retro. Be concrete and be kind, but do say it.

Make reversible changes without asking; surface only genuine conflicts.

## 5. The bar

Before writing a lesson down, apply one test:

> **Would a fresh session act differently after reading this — and is that
> difference not already obvious from the code or the git history?**

If it fails either half, it's a diary entry, not a lesson. Diary entries
("finished the parser today") are noise: `git log` already has them, and they
push the real lessons out of sight.

## Cross-references

- `/skill-review` — audits the skills you already have; this skill finds the
  ones you're missing.
- `/wrap-session` — its Phase 6 is a one-line retro; escalate to this when the
  friction recurs.
- `AGENTS.md` Part 2, "Improve the setup as you go".
