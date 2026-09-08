"""Guard the public quick-start and portfolio walkthrough contract."""

from pathlib import Path


def test_portfolio_walkthrough_documents_demo_and_ai_review_boundary() -> None:
    walkthrough = Path("docs/portfolio-walkthrough.md").read_text()
    readme = Path("README.md").read_text()

    assert "uv sync --locked" in readme
    assert "uv run python -m loadranger.demo" in walkthrough
    assert "/dashboard/{borrower_id}" in walkthrough
    assert "human verification" in walkthrough.lower()
    assert "not a credit decision-maker" in walkthrough.lower()
