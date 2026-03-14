from fastapi import APIRouter, Depends, HTTPException
import asyncpg

from analytics.builder import build_portfolio_report
from db.report_repo import get_cached_report, save_report
from api.dependencies import get_db_conn
from models.report import PortfolioReport

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.get("/report/{user_id}", response_model=PortfolioReport)
async def get_report(
    user_id: str,
    conn: asyncpg.Connection = Depends(get_db_conn),
):
    """Returns the last cached report instantly. 404 if none exists yet."""
    report = await get_cached_report(conn, user_id)
    if not report:
        raise HTTPException(
            status_code=404,
            detail="No report yet. Use POST /report/{user_id}/generate to create one."
        )
    return report


@router.post("/report/{user_id}/generate", response_model=PortfolioReport)
async def generate_report(
    user_id: str,
    conn: asyncpg.Connection = Depends(get_db_conn),
):
    """Generates a fresh report (slow — calls Gemini), then caches it."""
    try:
        report = await build_portfolio_report(user_id, conn)
        await save_report(conn, user_id, report)
        return report
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {e}")