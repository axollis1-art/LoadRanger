---
name: grill
description: >
  Interview the user about a plan, design, or decision until every branch of the
  design tree is resolved — asked in batched rounds, each question carrying a
  recommended answer, so a one-line reply settles a whole round. Use when the
  user says "grill me", "/grill", "grill this", "interview me", "stress-test
  this plan", "ask me what you need", "what do you need to know", or when a
  design discussion is about to become a build and the shape is still ambiguous.
---

# grill

Interview the user until you reach shared understanding. The failure this
prevents is the most common one in agentic coding: **they thought you understood
them, and only found out you didn't when they saw what you built.**

Model the work as a **design tree** — every decision branches into the decisions
that hang off it — and work it in **rounds**.

## 1. Compute the frontier

The **frontier** is every decision whose prerequisites are already settled: the
questions you can ask *now* without guessing at answers you haven't heard yet.

A question whose answer depends on another question still open in this round
belongs to a **later round**. Asking it now forces the user to answer
hypothetically, and hypothetical answers are the ones that turn out wrong.

## 2. Find the facts yourself

**Facts are your job. Decisions are theirs.**

Never ask the user for anything you could look up — a file path, what a function
currently does, what a library returns, whether a test passes. Go and read it.

Don't block on it: a running search is an unsettled prerequisite, so only the
questions *downstream* of it wait. Ask the rest of the frontier now.

This step is what keeps a grill cheap. A round of ten questions only the user can
answer costs one reply. A round padded with five you could have grepped costs
their patience — and trains them to skim the next one.

## 3. Ask the whole frontier in one round

One message, every frontier question numbered, each with your recommended
answer. Then **stop and wait**.

```
Q1 — <short title>: <the question; lettered options where the choice is discrete>
   Rec: <your recommended answer, and the one-line why>

Q2 — ...
```

Lettered options wherever they exist, so a terse reply works: *"1a, 2b, 3: your
rec"*. **Always give a recommendation.** A question with no position attached is
work handed back, not a decision put cleanly.

**Batching is what makes this cheap.** Ten questions in one round is one
interruption; ten drip-fed is ten. If the frontier is genuinely enormous, cut it
to the decisions that actually change the work — a padded round costs as much as
a buried one.

## 4. Recompute and repeat

Each round of answers reshapes the tree: settled decisions push the frontier
outward and unblock what depended on them. Recompute, ask the next round.

**Never answer your own questions.** An agent that grills itself has broken the
skill — the entire value is the information that exists only in the user's head.
If they go quiet mid-grill, say what is still open and stop. Do not proceed on
assumed answers.

## 5. Done

The session ends when the frontier is empty: every branch visited, nothing left
silently assumed. Say so explicitly, summarise the settled design in a few lines,
and **wait for confirmation** before building.

## When NOT to grill

This skill asks the user questions, which is friction. It earns its cost at a
**design boundary** and nowhere else.

- **Grill when** the user invokes it; when a discussion is about to become a
  build spanning more than one sitting; or when an ask is ambiguous in a way that
  would produce *materially different work* under different readings.
- **Do not grill** for reversible work with an obvious default — decide, note the
  assumption, proceed (see `AGENTS.md` Part 2). Nor for anything you can settle
  by looking (step 2). Nor to re-open a decision already made.

The test: *would different answers lead to materially different work?* If not,
there is no question — only a default you should take.

## Provenance

Adapted from [`grilling`](https://github.com/mattpocock/skills) by Matt Pocock
(MIT). The design-tree/frontier model and the round structure are his; the
fact-finding, batching and calibration clauses are additions.
