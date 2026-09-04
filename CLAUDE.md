# CLAUDE.md

The working contract lives in [`AGENTS.md`](AGENTS.md) so that Codex and
OpenCode read it too. Claude Code does not read `AGENTS.md` on its own, so the
line below is the import that pulls it into context.

@AGENTS.md

## Claude-Code-specific mechanics

- **Skills** live in `.agents/skills/<name>/SKILL.md` and are invoked as
  `/<name>`. `.claude/skills` is a symlink to that directory so both runtimes
  see one copy.
- **`/code-review`** from a *fresh* session is the independent review in
  AGENTS.md habit 8. Running it in the session that wrote the code gets you much
  less.
- **Plan mode** (`shift+tab` twice) before anything non-trivial. Read the plan
  before approving it — that is the cheapest place to catch a misunderstanding.
- **`/clear`** between unrelated tasks. Stale context makes the agent confidently
  wrong about files it read an hour ago.
