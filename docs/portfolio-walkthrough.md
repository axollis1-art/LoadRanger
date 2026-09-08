# Portfolio walkthrough

LoadRanger is a deterministic commercial-credit demonstrator. It records
borrower reporting periods, calculates financial metrics, applies a versioned
underwriting policy, evaluates covenants, and retains the evidence behind each
assessment and alert.

## Run it

```bash
uv sync --locked
./scripts/test-integration.sh
```

Start the API in a second terminal:

```bash
export LOADRANGER_DATABASE_URL='postgresql+psycopg://loadranger:loadranger@localhost:5432/loadranger'
uv run uvicorn loadranger.main:app --reload
```

The API contract is available at `http://127.0.0.1:8000/docs`. Verify the
complete local quality gate with:

```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy src/loadranger
uv run pytest
./scripts/test-integration.sh
```

## API workflow

Create a borrower, record a reporting period, then request its metric snapshot
and credit assessment. The generated identifiers are returned by each API call.

```bash
curl -X POST http://127.0.0.1:8000/borrowers -H 'content-type: application/json' \
  -d '{"legal_name":"Example Borrower Ltd"}'

curl -X POST http://127.0.0.1:8000/borrowers/<borrower_id>/financial-periods \
  -H 'content-type: application/json' \
  -d '{"period_end":"2027-12-31","total_debt":"400","cash":"100","ebitda":"100","interest_expense":"20"}'

curl -X POST http://127.0.0.1:8000/borrowers/<borrower_id>/financial-periods/<period_id>/credit-assessments
curl http://127.0.0.1:8000/borrowers/<borrower_id>/credit-summary
```

## Demonstration walkthrough

Seed the deterministic three-borrower portfolio:

```bash
uv run python -m loadranger.demo
```

The command is safe to repeat once the full named portfolio exists. Meridian
Components Ltd is the walkthrough borrower: its annual maximum-leverage covenant
progresses from pass (3.0000x), to warning (3.5000x), to breach (4.2000x).

Find its ID, then open:

```bash
docker compose exec -T db psql -U loadranger -d loadranger -tAc \
  "SELECT id FROM borrowers WHERE legal_name = 'Meridian Components Ltd'"
```

```text
http://127.0.0.1:8000/dashboard/{borrower_id}
```

The server-rendered page uses HTMX to load its summary fragment. It shows latest
financial metrics and assessment, plus the immutable covenant history and open
warning/breach alerts. The exact seed values and expected outcomes are in
[demo scenarios](demo-scenarios.md).

## Assumptions and limitations

- Amounts are GBP major units; input money is rounded to two decimal places.
- Metrics and policy decisions are deterministic demonstrator logic, not a
  production lending policy or financial advice.
- Reporting periods, metric snapshots, assessments, covenant tests, and alerts
  are immutable evidence records.
- The dashboard is a direct borrower URL, not a portfolio navigation product.
- The seed command expects a migrated database and refuses partially present
  named demo data rather than merging it silently.

## Future AI boundary

AI may later extract proposed covenant terms from loan documents, but it is not a credit decision-maker. Any AI output must preserve document provenance and
remain subject to human verification before it becomes a configured covenant or
affects a lending workflow. Deterministic calculations, policy evaluation, and
covenant monitoring remain the authoritative decision path.
