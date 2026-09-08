"""Minimal server-rendered borrower dashboard."""

from pathlib import Path
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from loadranger.api.dependencies import get_session
from loadranger.application.credit_summary import CreditSummary, get_credit_summary
from loadranger.persistence.repository import BorrowerRepository

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
SessionDependency = Annotated[Session, Depends(get_session)]


def _summary_or_404(session: Session, borrower_id: UUID) -> CreditSummary:
    try:
        return get_credit_summary(BorrowerRepository(session), borrower_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail="Borrower not found") from error


@router.get("/{borrower_id}", response_class=HTMLResponse)
def dashboard(
    request: Request, borrower_id: UUID, session: SessionDependency
) -> HTMLResponse:
    summary = _summary_or_404(session, borrower_id)
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={"summary": summary},
    )


@router.get("/{borrower_id}/summary", response_class=HTMLResponse)
def dashboard_summary(
    request: Request, borrower_id: UUID, session: SessionDependency
) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="summary.html",
        context={"summary": _summary_or_404(session, borrower_id)},
    )
