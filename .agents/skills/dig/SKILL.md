---
name: dig
description: >
  Defect autopsy — turn a single bug into its whole population. Given a bug, a
  surprising result, or a suspicious area, finds the root cause (not the
  symptom), runs a SIBLING SWEEP that actually searches the codebase for every
  other place the same shape exists (found one => find all), maps the blast
  radius, names the test that would have caught it, and separates the structural
  fix from the patch. Use when the user says "dig", "/dig", "dig into this",
  "root cause", "find the siblings", "what else is broken like this", or right
  after finding or fixing any bug, a surprising result, or a dependency upgrade.
---

# dig

Turn a single defect into its whole population.

The first instance of a bug is a **sample**, not a one-off. `/dig` produces an
autopsy: the root cause, the sibling sweep, the blast radius, the missing test,
and the structural fix.

This does the work — it does not just prompt the thinking.

## When to use

- Right after finding or fixing any bug, **before calling it done**.
- When a result surprises you: a test that passes and shouldn't, a wrong number,
  a crash you can't explain, code that seems not to run.
- After upgrading a dependency — renamed and removed APIs are latent bugs sitting
  in your repo right now.

## 1. Frame the defect

One line each:

- **Symptom** — what was actually observed.
- **Mechanism** — why it happened, at the code level.
- **Suspected class** — the general shape, stated without reference to this
  particular file.

Pull the **live evidence** — the real traceback, error, log line, wrong output.
Never reason from memory about what the error "probably" was.

## 2. Sibling sweep — the load-bearing step, and you must actually search

1. Derive a search for *this defect's shape* and run it. Examples:
   - renamed/removed API → grep the old symbol across the whole repo
   - unguarded index/key access → grep the same access pattern
   - a mutable default argument → `grep -rn "def .*=\[\]" `
   - float equality → `grep -rn "== 0\.\|!= 0\." `
   - a mock that hid reality → grep for patches of the same class
2. **List the whole population with `file:line`.** For each, say whether it is a
   genuine sibling (same failure mode) or a false match.
3. If the sweep is clean, **say so and show the command you ran** — "swept clean
   via `rg 'pattern' -c` → 0" is a real result. Silence is not.

Two ways this step lies to you, both green-looking:

- **A truncated search.** `| head -20` makes a sample look like the whole list.
  When emptiness is the finding, **count** (`wc -l`, `grep -c`), don't look.
- **A search that couldn't have matched.** Before trusting a zero, run the same
  search against the instance you *know* is a hit, and watch it return non-zero.

For a high-blast-radius defect — data model, authentication, money, anything
touching production — sweep from several angles rather than one: grep the API,
trace the callers, check the data lifecycle, check what the tests mock. Then
synthesise.

## 3. Blast radius

What does each instance take down — one input, one user, the whole dataset,
production? Flag any instance on a path that aggregates over many records (one
bad record → everything breaks) as higher severity.

## 4. The test that would have caught it

Name the specific missing test, in the right layer. The mapping is usually
mechanical:

| What happened | What to add |
|---|---|
| A mock hid it | A **real-dependency** test, not a better mock |
| A type error ran anyway | A **typecheck** in CI |
| A renamed API | A test that touches the **real** object |
| Wrong only at a boundary | A test **at** the boundary, not near it |
| Only breaks with real data volume | A test with a realistic fixture |

And then, per `AGENTS.md` habit 2: **break the code and watch the new test go
red** before you believe it.

## 5. Structural fix vs patch

Distinguish the **instance fix** (close this bug) from the **class fix** (make
the shape impossible — a type, an invariant, a single shared helper, deleting the
duplication that allowed the drift).

Prefer the class fix. At minimum, write it down. A patch that leaves the siblings
live is a partial result — say so plainly rather than reporting it as done.

## Output

```
SYMPTOM:   <observed>
MECHANISM: <code-level why>
ROOT:      <the class, not the instance>
SIBLINGS:  <file:line list, real vs false — OR "swept clean via `<cmd>` -> 0">
BLAST:     <who/what each takes down>
TEST:      <the specific test that would have caught it>
FIX:       patch=<instance>  |  class=<make the shape impossible>
```

Ranked by severity. **`SIBLINGS` and `TEST` are mandatory** — an autopsy without
a sweep and without a named test is not finished.

## Cross-references

- `AGENTS.md` habit 4 — "found one ⇒ find all", the rule this skill implements.
- `AGENTS.md` habit 2 — the mutation check on the test you add in step 4.
- `AGENTS.md` habit 6 — why a truncated search can't prove an absence.
- `/retro` — the broader "what can we learn", about process rather than code.
