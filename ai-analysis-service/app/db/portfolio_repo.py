import asyncpg


async def fetch_portfolio(
    conn: asyncpg.Connection,
    user_id: str,
) -> dict[str, dict]:
    rows = await conn.fetch(
        """
        SELECT
            ac.asset_id,
            ac.name                 AS asset,
            ap.quantity,
            ap.entry_price,
            ap.currency_code,
            u.symbol                AS unit_symbol,
            ap.unit_id,
            COALESCE(uc.factor, 1)  AS to_gram_factor
        FROM asset_portfolio ap
        JOIN asset_class ac  ON ac.asset_id = ap.asset_id
        JOIN units u         ON u.unit_id   = ap.unit_id
        LEFT JOIN unit_conversion uc
            ON uc.from_unit_id = ap.unit_id
            AND uc.to_unit_id  = 3          -- 3 = Gram
        WHERE ap.user_id = $1
        """,
        user_id,
    )
    return {
        row["asset"]: {
            "asset_id":       row["asset_id"],
            "quantity":       float(row["quantity"]),
            "entry_price":    float(row["entry_price"]) if row["entry_price"] else None,
            "currency_code":  row["currency_code"],
            "unit_symbol":    row["unit_symbol"],
            "unit_id":        row["unit_id"],
            "to_gram_factor": float(row["to_gram_factor"]),
        }
        for row in rows
    }

async def fetch_asset_ids(
    conn: asyncpg.Connection,
    user_id: str,
) -> list[int]:
    rows = await conn.fetch(
        """
        SELECT ap.asset_id
        FROM asset_portfolio ap
        WHERE ap.user_id = $1
        """,
        user_id,
    )
    return [row["asset_id"] for row in rows]