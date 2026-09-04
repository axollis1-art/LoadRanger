# Architecture and MVP plan

## Purpose and scope

LoadRanger is a portfolio demonstration of deterministic commercial-credit
underwriting and covenant monitoring. It is **not** a lending decision system:
all data is synthetic and all assessments are indicative.

The first release proves one coherent path:

1. record a borrower and a reporting period of financials;
2. calculate and persist reproducible metrics;
3. assess those metrics using a versioned, transparent policy;
4. define a loan covenant and run a test for a reporting period;
5. retain the result and show PASS, WARNING, or BREACH plus headroom.

This is intentionally a modular monolith. No microservices, background event
system, authentication, PDF ingestion, LLM integration, or separate SPA belong
in v1.

## Technology choices

| Concern | Choice | Why |
| --- | --- | --- |
| Runtime and packages | Python 3.13, `uv` | Fast, reproducible setup and a modern Python workflow. |
| HTTP application | FastAPI | Typed request/response models and generated OpenAPI documentation. |
| Validation contracts | Pydantic v2 | Explicit boundary validation and serialisation. |
| Persistence | PostgreSQL + SQLAlchemy 2.0 | Credible relational modelling and portable SQL. |
| Schema changes | Alembic | Versioned, reproducible database migrations. |
| UI | Jinja templates + HTMX (later in v1) | A small Python-led demo UI without a separate frontend build. |
| Tests | pytest, pytest-cov, HTTPX | Fast unit tests first, then API workflow tests. |
| Quality | Ruff, mypy | Consistent formatting/linting and useful type checking. |
| Local environment | Docker Compose | One-command PostgreSQL and repeatable local setup. |

SQLite may be used by unit/API tests where its behaviour is compatible, but
PostgreSQL remains the supported development database. A test that relies on a
PostgreSQL-specific behaviour must run against PostgreSQL.

## Module boundaries

```text
src/loadranger/
  api/           FastAPI routers, HTTP schemas, dependency wiring
  domain/        Pure models, enums, calculation and rule logic
  application/   Use cases that coordinate domain logic and repositories
  persistence/   SQLAlchemy mappings, repositories and migrations integration
  web/           Jinja templates and HTMX endpoints (after API workflows work)
  seed/          Explicit synthetic demo scenarios
tests/
  unit/          Pure financial/rule logic; no database or HTTP
  integration/   Repository and migration behaviour
  api/           HTTP workflows and validation/error responses
docs/            Decisions, setup instructions and domain assumptions
```

Dependencies point inward: API/web code calls application use cases;
application code depends on domain contracts; persistence implements those
contracts. Financial calculations must never depend on FastAPI, SQLAlchemy, or
an LLM.

## Core model

| Entity | Responsibility | Key relationships |
| --- | --- | --- |
| `Borrower` | Legal-name-level portfolio entity | has reporting periods, facilities, assessments and alerts |
| `FinancialPeriod` | A dated, immutable submitted financial snapshot | belongs to borrower; produces metric snapshot |
| `MetricSnapshot` | Calculated values plus calculation version and input reference | one per analysed financial period initially |
| `UnderwritingPolicy` | Named, versioned JSON rule configuration | used by assessments |
| `CreditAssessment` | Score/grade/recommendation and factor explanations | belongs to borrower and references period/policy/metrics |
| `Facility` | Loan/facility terms | belongs to borrower; has covenants |
| `Covenant` | Generic metric, operator, threshold, optional warning threshold and frequency | belongs to facility |
| `CovenantTest` | Immutable result for a covenant and reporting period | references covenant, period and metric snapshot |
| `Alert` | Actionable warning/breach record and lifecycle | references borrower and triggering covenant test where relevant |

All financial values use `Decimal`, stored at an explicitly documented scale.
Ratios use a separate precision policy. Missing values are represented as
`None`; zero is a valid value only where domain validation permits it.

## Domain decisions that protect correctness

- A calculation returns a value **or an explicit unavailable/invalid reason**.
  It must not invent a ratio for zero or negative EBITDA, zero interest expense,
  or incomplete inputs.
- Each metric calculation, assessment, and covenant test records its inputs,
  engine/policy version, timestamp, and human-readable explanation.
- Financial periods are immutable after analysis in v1. Corrections are new
  periods; this keeps history reproducible without a complex audit subsystem.
- Only a small fixed metric catalogue is supported initially: net debt,
  debt/EBITDA, net-debt/EBITDA, interest coverage, current ratio, EBITDA margin,
  and documented simplified free cash flow.
- Covenant operators start with `<=` and `>=`. Headroom is direction-aware and
  stated in both raw units and, where meaningful, percentage of limit.
- Policy configuration is validated Pydantic data, not arbitrary executable
  expressions. A policy can be changed by adding a versioned configuration,
  rather than editing calculation code.

## MVP boundary

### Included

- Borrowers, financial periods, facilities and generic covenants.
- Deterministic metrics with edge-case handling and explanations.
- Rules-based, explainable underwriting assessment.
- Covenant PASS/WARNING/BREACH evaluation, headroom and immutable history.
- Alerts for warning/breach, a synthetic seed dataset, OpenAPI and a thin
  borrower-summary UI.
- Database migrations, automated tests, linting/type checks and developer docs.

### Explicitly deferred

- Login, permissions, multi-tenancy and production compliance controls.
- Trend scoring beyond a clearly documented basic rule.
- PDF upload/OCR/LLM extraction. This becomes a human-reviewed proposal flow,
  never an automatic covenant activation.
- External financial data, credit-bureau integrations, notifications, queues,
  microservices and ML models.

## Test-first workflow

For every implementation issue, begin by adding a failing unit or API test that states
the business rule. Implement the smallest behaviour to make it pass; then
refactor. A pull request is ready only when `uv run ruff format --check .`,
`uv run ruff check .`, `uv run mypy src/loadranger`, and `uv run pytest` pass.

The most important test table is financial boundary behaviour: normal values,
zero, negative values, missing values, exact threshold, warning threshold, and
just-inside/just-outside values.

## Later extension: AI extraction

An LLM adapter may turn a document into a `ProposedCovenant` record containing
structured fields, source page/section, raw excerpt, model metadata and review
status. A person must approve it to create an active `Covenant`. The existing
deterministic covenant engine remains the only source of compliance results.
