# LoadRanger

LoadRanger is a portfolio demonstration of deterministic commercial-credit underwriting and covenant monitoring.

## Project documents

- [Product brief](docs/product-brief.md)
- [Architecture and MVP plan](docs/architecture.md)
- [MVP delivery epic](https://github.com/axollis1-art/LoadRanger/issues/16)

The GitHub epic and its child issues are the source of truth for delivery status and implementation sequencing.

## Local setup

Prerequisites: Python 3.13 and [uv](https://docs.astral.sh/uv/getting-started/installation/).

```bash
git clone https://github.com/axollis1-art/LoadRanger.git
cd LoadRanger
uv sync --locked
uv run pre-commit install
```

Run the complete local verification suite:

```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy src/loadranger
uv run pytest
uv run pre-commit run --all-files
```

Start the API with `uv run uvicorn loadranger.main:app --reload`; its health
endpoint is available at http://127.0.0.1:8000/health.

## Development container

Open this folder in VS Code and select **Dev Containers: Reopen in Container**. The container provides Python 3.13, Git, GitHub CLI, `uv`, and recommended Python editor extensions (Pylance and Ruff). It synchronises the locked project dependencies and installs the pre-commit hook when created.
