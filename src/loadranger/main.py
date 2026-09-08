"""HTTP application entry point."""

from fastapi import FastAPI

from loadranger.api.borrowers import router as borrowers_router
from loadranger.web import router as dashboard_router

app = FastAPI(title="LoadRanger")
app.include_router(borrowers_router)
app.include_router(dashboard_router)


@app.get("/health")
def health() -> dict[str, str]:
    """Report whether the service is available."""
    return {"status": "ok"}
