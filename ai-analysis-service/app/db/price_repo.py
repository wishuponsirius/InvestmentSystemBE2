import pandas as pd
import asyncpg


async def fetch_price_matrix(
    conn: asyncpg.Connection,
    asset_ids: list[int],
    days: int = 365,
) -> pd.DataFrame:
    """
    Returns a wide DataFrame:
      index   = date (daily)
      columns = asset name
      values  = avg sell_price_vnd

    Gaps are forward-filled so every asset has a value for every day.
    """
    rows = await conn.fetch(
        """
        SELECT
            ac.name                     AS asset,
            nap.timestamp::date         AS date,
            AVG(nap.sell_price_vnd)     AS price
        FROM normalized_asset_price nap
        JOIN asset_class ac ON ac.asset_id = nap.asset_id
        WHERE nap.asset_id = ANY($1)
          AND nap.timestamp >= NOW() - ($2 || ' days')::INTERVAL
          AND nap.sell_price_vnd IS NOT NULL
        GROUP BY ac.name, nap.timestamp::date
        ORDER BY date ASC
        """,
        asset_ids,
        str(days),
    )

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows, columns=["asset", "date", "price"])
    df["price"] = pd.to_numeric(df["price"])

    wide = (
        df.pivot(index="date", columns="asset", values="price")
        .sort_index()
        .ffill()
        .bfill()
    )
    wide.index = pd.to_datetime(wide.index)
    wide.columns.name = None
    return wide


async def fetch_latest_prices(
    conn: asyncpg.Connection,
    asset_ids: list[int],
) -> dict[str, float]:
    """
    Returns {asset_name: latest_sell_price_vnd}.
    Used for current portfolio valuation.
    """
    rows = await conn.fetch(
        """
        SELECT DISTINCT ON (nap.asset_id)
            ac.name             AS asset,
            nap.sell_price_vnd  AS price
        FROM normalized_asset_price nap
        JOIN asset_class ac ON ac.asset_id = nap.asset_id
        WHERE nap.asset_id = ANY($1)
          AND nap.sell_price_vnd IS NOT NULL
        ORDER BY nap.asset_id, nap.timestamp DESC
        """,
        asset_ids,
    )
    return {row["asset"]: float(row["price"]) for row in rows}