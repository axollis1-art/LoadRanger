---
name: prior-art
description: >
  Work out whether a proposed feature already exists, is half-built, or
  substantively overlaps something already in the codebase — before any design or
  code is written. Returns one verdict: REUSE, EXTEND, NEW, SUPERSEDED or HOLD.
  Use when asked "does this already exist?", "are we duplicating something?",
  "check prior art", or before designing any new feature.
---

# prior-art

Read-only. Produces an integration verdict before design begins.

The cheapest feature is the one that is already there. The second cheapest is a
small addition to something that already works. Building a parallel system
because you didn't know about the first one is the most expensive outcome, and
it is easy to reach by accident — especially in a codebase you didn't write all
of, or wrote three months ago.

## 1. Establish the search surface

Work out what the user actually sees — the command they'd type, the page they'd
look at, the output they'd read — and **search their words before your words**.

You will instinctively search for the mechanism you're planning to build
(`RateLimiter`, `cache`, `normaliser`). The existing implementation was named by
somebody solving the problem from the user's side, and will be called something
else. Search the symptom vocabulary first.

## 2. Investigate

Look at enough of each of these to reach a defensible verdict:

1. **Open issues and TODOs** — including ones phrased in the user's symptom
   words, not your mechanism words.
2. **Open and recently merged branches/PRs** — including their comments.
   Somebody may be building it right now.
3. **The code itself** — modules, classes, functions, commands, routes, config
   keys, tests. `grep` for the *behaviour*, not just the name.
4. **The consumers** — imports, call sites, stored fields, entrypoints. A thing
   with no consumers may be dead; a thing with many is expensive to duplicate.
5. **Docs, READMEs and comments** — often the only record of a deliberate
   decision not to build something.

**Do not stop at a title match.** Read the implementation and one consumer far
enough to distinguish *shared vocabulary* from *shared behaviour* — two things
called `validate` are usually unrelated.

**Conversely, do not call work new because the existing thing has a different
name**, or was written for a test harness, a prototype, or an older use case. A
90%-right implementation behind an awkward name is still prior art.

## 3. Return one verdict

Lead with exactly one:

- **REUSE** — it already exists. Explain how to invoke it. Stop here.
- **EXTEND** — an existing component should gain a narrow addition or mode.
  Name the component and the seam.
- **NEW** — nothing owns this capability. Say **why the existing seams can't**,
  and name the clean integration point.
- **SUPERSEDED** — the proposal targets something retired or replaced. Name the
  current owner.
- **HOLD** — the evidence is insufficient. Say what you'd need. This is a real
  answer; inventing a verdict is not.

Then state, briefly:

- the existing owner and what's worth reusing;
- the precise missing piece;
- the consumers and integration points;
- the smallest thing you could build and test quickly to prove the approach;
- explicit **non-goals** — what this is deliberately not doing, so the scope
  doesn't creep during the build.

## 4. Record it

A verdict that lives only in the chat gets re-derived from scratch next month.
Put it in the issue, the PR description, or a short note in `docs/` — with the
links and file paths you actually looked at, and the date. Skip this only for a
trivial REUSE you settled in one lookup.

## Scope

This skill **investigates only**. It does not design, write code, open or close
issues, or change anything. Feed an approved verdict into the build.

## Cross-references

- `/grill` — the next step once the verdict is EXTEND or NEW: settle the design
  before building it.
- `AGENTS.md` habit 3 — "NEW" is a claim that something doesn't exist, and is
  exactly the kind of claim that needs a check rather than a recollection.
