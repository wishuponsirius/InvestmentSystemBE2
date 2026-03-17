import pandas as pd
import asyncpg


LOCAL_SOURCE_ID = 1
GLOBAL_SOURCE_ID = 2


async def fetch_metal_spread_history(
    conn: asyncpg.Connection,
    asset_id: int,
    days: int = 365,
    local_source_id: int = LOCAL_SOURCE_ID,
    global_source_id: int = GLOBAL_SOURCE_ID,
) -> pd.DataFrame:
    """
    Returns a daily time series comparing local vs global metal prices.

    Output columns:
        - date
        - local_price
        - global_price
        - abs_spread
        - spread_pct

    Notes:
        - Uses normalized_market_price because we need source_id
        - Assumes prices are already normalized to VND/gram
        - Uses AVG(sell_price_vnd) per day/source
        - Forward-fills missing values to align both series
    """
    rows = await conn.fetch(
        """
        SELECT
            nmp.timestamp::date AS date,
            nmp.source_id,
            AVG(nmp.sell_price_vnd) AS price
        FROM normalized_market_price nmp
        WHERE nmp.asset_id = $1
          AND nmp.source_id = ANY($2::int[])
          AND nmp.timestamp >= NOW() - ($3 || ' days')::INTERVAL
          AND nmp.sell_price_vnd IS NOT NULL
        GROUP BY nmp.timestamp::date, nmp.source_id
        ORDER BY date ASC
        """,
        asset_id,
        [local_source_id, global_source_id],
        str(days),
    )

    if not rows:
        return pd.DataFrame(
            columns=[
                "date",
                "local_price",
                "global_price",
                "abs_spread",
                "spread_pct",
            ]
        )

    df = pd.DataFrame(rows, columns=["date", "source_id", "price"])
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df["date"] = pd.to_datetime(df["date"])

    pivot = (
        df.pivot(index="date", columns="source_id", values="price")
        .sort_index()
        .ffill()
        .bfill()
    )

    # Rename source columns safely
    pivot = pivot.rename(
        columns={
            local_source_id: "local_price",
            global_source_id: "global_price",
        }
    )

    # Ensure both columns exist
    if "local_price" not in pivot.columns:
        pivot["local_price"] = pd.NA
    if "global_price" not in pivot.columns:
        pivot["global_price"] = pd.NA

    result = pivot[["local_price", "global_price"]].copy()
    result["abs_spread"] = result["local_price"] - result["global_price"]
    result["spread_pct"] = (
        result["abs_spread"] / result["global_price"]
    ) * 100.0

    result = result.reset_index()
    return result


async def fetch_latest_metal_spread(
    conn: asyncpg.Connection,
    asset_id: int,
    local_source_id: int = LOCAL_SOURCE_ID,
    global_source_id: int = GLOBAL_SOURCE_ID,
) -> dict:
    """
    Returns the latest local/global price pair and spread info for one metal asset.

    Example output:
    {
        "asset_id": 1,
        "local_price": 9200000.0,
        "global_price": 8800000.0,
        "abs_spread": 400000.0,
        "spread_pct": 4.54
    }
    """
    rows = await conn.fetch(
        """
        WITH latest_per_source AS (
            SELECT DISTINCT ON (nmp.source_id)
                nmp.source_id,
                nmp.sell_price_vnd
            FROM normalized_market_price nmp
            WHERE nmp.asset_id = $1
              AND nmp.source_id = ANY($2::int[])
              AND nmp.sell_price_vnd IS NOT NULL
            ORDER BY nmp.source_id, nmp.timestamp DESC
        )
        SELECT source_id, sell_price_vnd
        FROM latest_per_source
        """,
        asset_id,
        [local_source_id, global_source_id],
    )

    price_map = {row["source_id"]: float(row["sell_price_vnd"]) for row in rows}

    local_price = price_map.get(local_source_id)
    global_price = price_map.get(global_source_id)

    if local_price is None or global_price is None or global_price == 0:
        return {
            "asset_id": asset_id,
            "local_price": local_price,
            "global_price": global_price,
            "abs_spread": None,
            "spread_pct": None,
        }

    abs_spread = local_price - global_price
    spread_pct = (abs_spread / global_price) * 100.0

    return {
        "asset_id": asset_id,
        "local_price": local_price,
        "global_price": global_price,
        "abs_spread": abs_spread,
        "spread_pct": spread_pct,
    }