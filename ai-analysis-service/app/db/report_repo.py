import json
import asyncpg
from models.report import PortfolioReport


async def get_cached_report(
    conn: asyncpg.Connection,
    user_id: str,
) -> PortfolioReport | None:
    row = await conn.fetchrow(
        """
        SELECT report_data, generated_at
        FROM portfolio_report_cache
        WHERE user_id = $1
        """,
        user_id,
    )
    if not row:
        return None
    data = json.loads(row["report_data"])
    return PortfolioReport(**data)


async def save_report(
    conn: asyncpg.Connection,
    user_id: str,
    report: PortfolioReport,
) -> None:
    await conn.execute(
        """
        INSERT INTO portfolio_report_cache (user_id, report_data)
        VALUES ($1, $2)
        ON CONFLICT (user_id)
        DO UPDATE SET
            report_data  = EXCLUDED.report_data,
            generated_at = CURRENT_TIMESTAMP
        """,
        user_id,
        report.model_dump_json(),
    )