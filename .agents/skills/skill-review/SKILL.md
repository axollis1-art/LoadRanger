---
name: skill-review
description: >
  Audit your own skills and working rules — score each one for a clear trigger,
  stale paths or commands, overlap with another skill, and the capability you
  keep needing but don't have. Emits a table with a verdict and one concrete fix
  per weak item. Use when the user says "skill review", "/skill-review", "audit
  our skills", "are our skills any good", "review the skills", or "what skill is
  missing".
---

# skill-review

Skills rot the same way code does — the path moves, the command changes, two
skills grow into each other, and the trigger phrasing stops matching how you
actually talk. A rotten skill is worse than an absent one: it gets invoked and
then does the wrong thing confidently.

Run this every few weeks once you have more than three or four skills.

## 1. Inventory

List every `SKILL.md` under `.agents/skills/` (and `~/.claude/skills/` if you
keep personal ones), plus `AGENTS.md`. For each, read the frontmatter
`description` and the body.

## 2. Score each one

Five checks, and the fifth is the one that matters most:

| Check | Failing looks like |
|---|---|
| **Trigger clarity** | The `description` doesn't list the phrases you'd actually type. The agent won't reach for it unprompted, so it may as well not exist. |
| **Freshness** | Referenced paths, commands or files no longer exist. **Verify by running them**, not by reading them. |
| **Overlap** | Two skills that fire on the same request. Either merge them, or sharpen both descriptions so it's clear which is which. |
| **Actionability** | The body says what to think about rather than what to do. A skill is a procedure; a philosophy belongs in `AGENTS.md`. |
| **Evidence of use** | Search your history: has it ever actually been invoked? A skill nobody uses is either badly triggered or unnecessary — decide which and act. |

## 3. Find what's missing

The most valuable output of this skill is usually a **new** skill, not a fix to
an old one. Sources:

- Any multi-step procedure you have explained to the agent more than once.
- Any recurring friction `/retro` surfaced but nothing was written for.
- Any task where you always start by pasting the same context.

## 4. Output

```
| Skill | Verdict | Fix |
|---|---|---|
| grill | keep | — |
| deploy | stale | `scripts/push.sh` was renamed; update step 3 |
| lint / format | overlapping | merge into one; delete `format` |
| — | MISSING | "run the numerical test suite + compare against reference output" |
```

Verdicts: **keep** · **sharpen** (fix the description) · **stale** (fix the
body) · **overlapping** (merge) · **delete** (unused and unnecessary) ·
**MISSING** (write it).

**Every non-`keep` row needs a concrete fix**, not an observation. "The
description could be better" is not a finding; "add the phrases 'run the
benchmarks' and 'time it' to the description" is.

## 5. Apply

Make the edits in the same session — they're all reversible and all small. Then
say in one line what changed. Deleting a skill counts as a good outcome; a
smaller set that always fires correctly beats a large set you can't trust.

## Cross-references

- `/retro` — finds the friction; this skill turns it into the right artefact.
- `AGENTS.md` Part 2, "Improve the setup as you go".
