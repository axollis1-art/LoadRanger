"""HTTP application entry point."""

from fastapi import FastAPI

app = FastAPI(title="LoadRanger")


@app.get("/health")
def health() -> dict[str, str]:
    """Report whether the service is available."""
    return {"status": "ok"}
