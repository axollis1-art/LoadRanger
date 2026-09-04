# AGENTS.md — how we work here

Portable working contract for any coding agent (Claude Code, Codex, OpenCode).
Claude Code additionally reads `CLAUDE.md`, which just imports this file.

This is the **one home** for the practice rules. Don't copy them into other
files — point at this one.

---

## Part 1 — The habits that stop you shipping wrong things

Each of these exists because the failure it prevents is *silent*: the code looks
fine, the test is green, and nobody finds out until much later. That is what
makes them worth writing down. A loud failure teaches you on its own.

### 1. "Done" means you re-tested the original problem

Component tests passing, a clean build, and "I verified the thing I built" are
all **evidence toward** done. None of them **is** done.

Before saying done, fixed, or shipped:

1. Write down, in one line, what the original problem was — from the point of
   view of whoever reported it, not the sub-task you just finished.
2. Drive *that* thing, at the layer the reporter sees it (the CLI output, the
   plot, the page, the returned number) — not the function you wrote.
3. **Observe, don't infer.** If the behaviour only fires in some state (an
   error path, an empty input, a value at the boundary), *produce that state and
   watch it happen*. "The code path exists and the value flows correctly" is
   inference, and it ranks below observation.
4. State a confidence, and name what you could not test and why. "High, but I
   couldn't exercise the timeout path" beats a flat "done".

If you have not done 1–4, the honest phrase is **"built, not yet verified"**,
plus what would close it.

### 2. An assertion you have not watched fail is not a test

This is the highest-value habit in this file and the one most people skip.

You write a test against working code, so it passes. That gives you evidence
that the code and the test *agree today*, and **no evidence at all** that the
test can tell them apart. A real test and a vacuous one look identical at the
moment you write them.

So: **break the thing the test guards, and watch it go red.** Change the sign,
delete the branch, revert the fix, return the wrong value. Restore afterwards.

Do this *while writing the test*, not as a tidy-up pass later — stated as a
separate step, it becomes a step you skip.

Ways a test quietly declines to discriminate, all of which look green:

- **A fixture that makes the property unobservable.** Every item sharing one
  timestamp cannot detect an ordering bug. Ask: *what would this fixture have to
  contain for my assertion to be able to fail?*
- **Asserting on a rendering instead of the value.** `assert "0.5" in output`
  passes on `"10.53"`. Compare parsed values for equality, not substrings.
- **Only mutating in one direction.** Deleting things tests staleness. Real code
  usually *grows* — new enum members, new config keys, new columns. Ask: *what
  does the next commit to this file plausibly do, and would my test notice?*
- **The mutation never actually applied.** If you script a batch of mutations,
  assert each one changed the file, and read pass/fail from the **exit code**,
  never by grepping formatted output.

### 3. Run the check that could prove you wrong, before you say "because"

Before publishing a cause — in a commit message, an issue, a report, or just to
a collaborator — answer three questions:

1. What is the leading **alternative** explanation? If you can't name one, you
   haven't looked.
2. What single observation would come out **differently** under each?
3. Have you made it?

If no, publish it as a hypothesis *with the test named*. That's a complete and
useful contribution. An asserted cause without it is not.

**The tell is a modal verb about something you could open.** "numpy *won't* do
that", "the API *doesn't* support it", "that *can't* be configured", "there's
*no way* to". Each is a claim about an artefact — a library's source, a live
response, a config file — that you can check in under a minute. The question is
never "am I confident?" but "how long would checking take?".

Two more traps worth naming:

- **When several things changed at once, "X changed and then Y broke" proves
  nothing.** Temporal coincidence is evidence only when X is the *only* change.
- **Beware the explanation you have most context on.** The hypothesis whose code
  you wrote yourself is the one you can narrate most fluently — and fluency is
  not evidence. Test it first, don't trust it first.
- **A decision to *not* do something is also a claim.** "Blocked on X", "wait
  until Y", "hold this" — each gets acted on immediately because doing nothing
  needs no approval. Ask: *did I observe the blocker, or infer it? If the thing
  I'm waiting for never arrives, what then?*

### 4. Found one ⇒ find all

The first instance of a bug is a **sample of a population**, not a one-off.

When you find or fix a bug, before calling it done:

- **Root, not symptom.** Why → why → why. Am I fixing the class or the instance?
- **Sibling sweep — actually search.** `grep`/`rg` for the same *shape* elsewhere
  and list every hit with `file:line`. If the sweep is clean, **say so and show
  the command you ran** — "swept clean via `<cmd>`" is a real result; silence is
  not.
- **Blast radius.** Who does each instance affect — one input, one user, all
  data?
- **What would have caught it.** Name the missing test. "A mock hid it" ⇒ the
  fix is a real-dependency test, not a better mock.
- **Structural fix vs patch.** Can you make the shape *impossible*, rather than
  fixing this one? Prefer that. State both.

The `/dig` skill in this pack does exactly this.

### 5. Look the API up; don't recall it

Before writing against a library you're not certain of — a new dependency, a
version you haven't used, or any signature you'd be recalling rather than
copying from a working call site nearby — **read its current docs**.

Model recall of library APIs is exactly where confident hallucination lives, and
it costs you a full test-run cycle to discover. Check `pyproject.toml` /
`package.json` for the version you actually pin: if the docs describe a newer
API than you have, **the pin wins**.

This does *not* fire for the standard library, your own code, or an API already
used in the file you're editing — there, the existing call site is ground truth
and matching it is correct.

### 6. Never conclude an absence from a search you truncated

`| head -20` is a display convenience that silently changes what a command
*means*: the output stops looking like a sample and starts looking like the
whole list. The counter-example may have been on the next line.

**When emptiness is the finding, count — don't look.** Pipe to `wc -l` or use
`grep -c`, and quote the number. A count can't be truncated.

Stronger still: run the search against a case you **know** it must match first,
and only trust a zero once you've watched it return non-zero.

Two shell traps in the same family, both of which produce an empty result and a
plausible exit code:

- **A pipeline's exit code is its *last* command's.** `pytest | tail -5 && git
  commit` commits on a failing test suite. Run anything whose exit code is a
  decision **bare**; format its output afterwards.
- **Quote globs meant for the program, not the shell** — `--include="*.py"`,
  `-name "*.csv"`. Unquoted, `zsh` aborts the command before it runs.

### 7. One home per fact

Every fact has exactly **one stored home**. Every other form — a display string,
a formatted date, a rounded value, a cached total — is **derived at the point of
use**, not stored alongside it.

Two stored copies of one fact, with nothing forcing them to agree, is the seed of
every drift bug you will ever write. The one that changes is always the copy
nobody is looking at.

The same rule for generated files: **edit the source, regenerate the derivative,
never hand-edit the derivative.**

The tell that you're about to break this: *"but the consumer needs it in another
form"*. That's evidence of a **missing derivation**, not a storage requirement.
Build the conversion.

### 8. Get a review from something that didn't write the code

The weakest review you can run is the author re-reading their own work: it has
already rationalised every choice and reads the code toward confirming intent.

For anything that can produce a *wrong answer* — not typos and copy — get a
**fresh-context, adversarial** review: a new session, told to *find the failure
case*, not to *review*. In Claude Code that's `/code-review` from a clean
session. It costs one command and catches what you structurally cannot.

Docs and config-only changes are exempt. When in doubt, review.

### 9. Automation never blocks on stdin

Anything an agent, a cron job, or CI might run must never wait for a `[y/N]`,
a password prompt, a pager, or an editor. There is nobody at the keyboard, so a
blocking prompt is not "safe by default" — it's a **silent hang** that holds the
machine until something kills it.

Pass the non-interactive flag at the call site (`--yes`, `--no-input`,
`PAGER=cat`, `GIT_TERMINAL_PROMPT=0`), and put a **timeout** on anything that
talks to the network. A hang is worse than an error: an error tells you.

### 10. If you're deciding what a human *meant*, use the model — not a regex

Only relevant if you're building something with an LLM in it, but it's the
mistake everyone makes once.

Ask: **is the set of valid inputs closed or open?**

- **Closed** — finite and defined by you: slash commands, menu items, enum
  values, a date from a picker. **Regex and plain code are correct here**, and a
  model would be worse: slower, costlier, non-deterministic over a space you
  already know completely.
- **Open** — natural language somebody else wrote: what they *meant*, whether
  they *refused*, what they were *referring to*. A pattern list here is a sample
  of an infinite space. **Use the model's structured output** — and if you're
  already making a model call that turn, just add a field to its schema.

When a pattern misses a phrasing, the reflex is to add one more pattern. That
reflex is the trap: each patch is cheap and makes the next look cheaper, and the
list quietly becomes the decision boundary it was never meant to be.

---

## Part 2 — Working with the agent

### Settle the design before you build

The most common failure in agentic coding is not bad code. It's that **you
thought the agent understood you**, and only found out when you saw what it
built.

For anything bigger than a single edit, make the agent interview you first — the
`/grill` skill in this pack does it in batched rounds, with a recommended answer
attached to every question, so a one-line reply settles a whole round. Ten
questions in one message is one interruption; ten drip-fed is ten.

Then check it isn't already built: `/prior-art`. The cheapest feature is the one
already there.

### Write the issue, not the chat message

For anything spanning more than one sitting, the **GitHub issue is the source of
truth — not the conversation.** Chat history doesn't survive a new session, and
reconstructing it is the single biggest tax in agentic coding.

Three skills cover this, and the difference is *when*:

- **Before you start** — `/plan-work` files a GitHub tracking issue: goal,
  `Done when:`, non-goals, and an ordered checklist of steps each carrying its own
  acceptance check. `/run-plan` then executes it cold, one commit per step,
  ticking boxes as it goes and closing the issue from the PR. Use the pair
  whenever the work won't finish today.
- **When the list gets away from you** — `/triage` groups the open issues, flags
  what's rotting, and names the two or three worth picking up.
- **When you stop mid-task** — `/handoff` produces a self-contained block a fresh
  session can act on right now.

All three have the same test: **if it needs the chat history to make sense, it
isn't finished.**

### Decide and proceed on reversible work

Tell the agent this explicitly, because the default is to over-ask. On anything
reversible — a local commit, a branch, a refactor, a test — it should make the
call, **note the assumption**, and keep going. Stop only at genuine one-way
doors: a deploy, a force-push, an irreversible delete, spending real money.

A stream of "shall I proceed?" prompts is friction, not safety.

### Report proactively; don't make yourself poll

If the agent starts something long, it should say what it started and report
when it lands. You should not have to type "status?".

### Ask for the proof, not the conclusion

"All tests pass" is a claim. `47 passed in 3.2s` is evidence. Ask for the
command and its output — especially for *positive* results, which nobody
instinctively double-checks.

### Keep the loop fast — iterate offline

Never debug a behaviour by pushing → waiting for CI → looking at the result.
That's minutes per iteration for something a local test does in seconds. Build
the smallest thing that reproduces the failure locally, iterate against that,
and run the slow path **once at the end as confirmation, not discovery**.

### Improve the setup as you go

When something is annoying for the second time, that's the signal to fix the
setup, not to tolerate it a third time. Explaining a multi-step procedure to the
agent is a **skill candidate** — write it into `.agents/skills/`. `/retro` finds
these for you; `/skill-review` keeps the ones you have sharp.

---

## Part 3 — Repo conventions

Adjust these to taste; the point is that they're written down somewhere the
agent reads.

- **Conventional commits** — `feat:`, `fix:`, `docs:`, `test:`, `chore:`.
- **Fail fast** — no silent fallbacks. Missing config should error loudly at
  startup, not produce a quietly wrong default at 3am.
- **Full type annotations** — Python type hints, TypeScript strict. They are the
  cheapest test you will ever write.
- **Keep the repo root clean** — scripts in `scripts/`, docs in `docs/`, notebooks
  in `notebooks/`.
- **One logical change per branch and PR.** A PR you can review in ten minutes
  gets reviewed; one that takes an hour gets rubber-stamped.
- **Branch from a freshly-fetched default branch**, not from whatever happens to
  be checked out:
  `git fetch origin main && git checkout -b fix/thing origin/main`.

### Issues and labels

Use GitHub issues as the project's memory. It costs almost nothing and it is the
only record that survives you forgetting.

- **Anything bigger than one sitting gets an issue** before it gets code — see
  `/plan-work`. Anything smaller doesn't need one; don't file ceremony.
- **Keep planning in GitHub, not a mirrored document.** The issue/epic is the
  source of truth for scope, sequencing, status, and acceptance checks. Keep
  `docs/` for durable product and architecture decisions only. A local backlog
  drifts as soon as an issue changes, which happened when this project first
  created both.
- **One type label per issue** — `bug`, `feature`, `chore`, `docs` — plus `plan`
  on tracking issues and `blocked` where it applies. Run the pack's
  `setup-labels.sh` once to create them.
- **Keep the label set small.** A label nobody filters on is noise. If you never
  type `--label X`, delete X. Six is plenty; twenty means none of them mean
  anything.
- **Link every PR to its issue** with `Closes #12` in the PR body (or `Refs #12`
  if it only advances it). GitHub closes the issue on merge and permanently links
  the code to the reasoning. Six months later this is how you find out *why* a
  change was made — and you will need to.
- **Close issues you're not going to do**, with one line saying why. A backlog
  you trust is worth more than one that's complete, and a stale issue is a
  deferred decision rather than a failure.
- **Write issue and PR bodies from a file or a heredoc**, never inline in a
  double-quoted shell argument — the shell executes every `` `backtick span` ``
  in your prose and silently deletes it.
