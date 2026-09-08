# Demonstration portfolio

Seed a database that has already been migrated with:

```bash
export LOADRANGER_DATABASE_URL='postgresql+psycopg://loadranger:loadranger@localhost:5432/loadranger'
uv run python -m loadranger.demo
```

The command is idempotent: a second run returns the three named demo borrowers
without adding periods, snapshots, assessments, covenant tests, or alerts. It
fails rather than silently changing a partially present demo portfolio.

All values are GBP. Each borrower has a `Demo maximum net debt to EBITDA`
covenant: maximum `4.0000x`, with warning at `3.5000x`.

| Borrower | Period end | Debt | Cash | EBITDA | Net debt / EBITDA | Expected covenant result |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Harbour Engineering Ltd | 2027-12-31 | 300 | 100 | 100 | 2.0000x | pass |
| Meridian Components Ltd | 2025-12-31 | 400 | 100 | 100 | 3.0000x | pass |
| Meridian Components Ltd | 2026-12-31 | 450 | 100 | 100 | 3.5000x | warning |
| Meridian Components Ltd | 2027-12-31 | 520 | 100 | 100 | 4.2000x | breach |
| Northstar Distribution Ltd | 2027-12-31 | 550 | 100 | 100 | 4.5000x | breach |

The Meridian scenario is the time-series walkthrough: its credit summary shows
the covenant history in most-recent-first order (`breach`, `warning`, `pass`)
and open breach and warning alerts. The integration smoke test verifies this
user-visible summary as well as the command's idempotent three-borrower result.
