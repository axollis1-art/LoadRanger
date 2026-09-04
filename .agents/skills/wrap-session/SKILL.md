---
name: wrap-session
description: >
  Wrap up a working session — survey the repo, surface anything dirty, stale or
  pending, then propose targeted cleanup so tomorrow starts clean. Use when the
  user signals they're done ("wrap up", "end session", "we're done here",
  "/wrap-session"), or any time you'd otherwise leave the repo in a state
  somebody has to reconstruct.
---

# wrap-session

The goal is a tidy hand-off: no orphaned branches, no lost edits, no dangling
PRs. Tomorrow-you should be able to pick up without forensics.

## Principles

- **Survey first, act second.** Surface state before proposing anything
  destructive.
- **Never delete unconfirmed work.** Uncommitted edits and unpushed branches may
  be deliberate. Ask.
- **Match the response to the repo.** A clean tree needs one sentence. Don't pad.
- **Be silent when there's nothing to do.** "Everything's clean, nothing pending"
  is a complete and correct output.

## Phase 1 — Survey

```bash
git status -s                                   # uncommitted work
git branch --show-current                       # sitting on a feature branch?
git fetch --prune --quiet
git branch -vv | grep '\[gone\]'                # remotes merged and deleted
git stash list                                  # forgotten stashes
git log --oneline origin/main..HEAD             # unpushed commits
gh pr list --search "is:open author:@me"        # open PRs and their CI state
```

## Phase 2 — Categorise what you found

- **Live work** — open PRs, branches deliberately pending review.
- **Forgotten work** — uncommitted edits in files touched this session; branches
  pushed with no PR opened; commits made but never pushed.
- **Cleanup candidates** — branches whose remote is gone, a repo sitting on an
  already-merged feature branch, stale stashes.
- **Stale notes** — anything in the README or docs the session proved wrong.

## Phase 3 — Surface, then propose

Report tightly, then **propose** before acting:

- *"5 branches whose remotes are gone. Delete them?"*
- *"You're on `feat/parser` but PR #12 merged 20 minutes ago. Switch back to
  `main`?"*
- *"2 uncommitted files in `src/` — commit, stash, or leave?"*
- *"`stash@{0}` is from 3 weeks ago. Still needed?"*

Read-only surveys are fine to run unprompted. **Never run a destructive command
without confirmation** — and bundle the confirmations into one question rather
than asking four times in a row.

## Phase 4 — Cleanup (once confirmed)

- **Branch deletion:** only for branches whose work has actually landed. Careful:
  if the project **squash-merges**, `git merge-base --is-ancestor` reports
  UNMERGED for every merged branch, because a squash creates a *new* commit. Use
  the PR state as the oracle instead:
  ```bash
  gh pr list --head "$BRANCH" --state merged --json number --jq 'length'
  ```
  Non-zero ⇒ landed ⇒ safe to delete. Treat the ancestor test's *positive* as
  conclusive and its *negative* as meaningless.
- **Switch to the default branch** only when the tree is clean.
- **Leave anything dirty or unmerged in place, and list it.** It holds real work
  or needs a decision.

## Phase 5 — Hand-off summary

Ten seconds to read:

```
Session wrap-up — <one-line scope>

Shipped:   <PRs / commits / releases>
Open:      <PR numbers + status>
Deferred:  <items + why>
Next step: <one sentence>
```

## Phase 6 — One line of introspection

Name the single biggest friction this session and the one change that would
remove it next time. **One line — name it, don't explain it.** If it's the second
time you've hit the same friction, that's the signal to actually fix the setup:
offer `/retro`.

## Anti-patterns

- **Don't write a `SESSION_LOG.md`.** Activity logs aren't documentation, they're
  forensic detritus — `git log` already has it.
- **Don't force a wrap when work is genuinely mid-flight.** If tests are running
  or a PR is mid-review, say so and offer to wait.
- **Don't invent cleanup.** If the repo is clean, say so and stop.

## Cross-references

- `/handoff` — use instead when stopping **mid-task**; this skill is for
  finishing.
- `/retro` — the deeper "what can we learn" when Phase 6 finds something real.
