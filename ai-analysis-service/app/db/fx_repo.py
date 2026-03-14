import asyncpg


async def fetch_latest_rates(
    conn: asyncpg.Connection,
    currency_codes: list[str],
) -> dict[str, dict[str, float]]:
    """
    Returns {
      currency_code: { buy_price, sell_price, transfer_price }
    }
    Uses the most recent rate per currency against VND.
    """
    rows = await conn.fetch(
        """
        SELECT DISTINCT ON (currency_code)
            currency_code,
            buy_price,
            sell_price,
            transfer_price
        FROM exchange_rates
        WHERE currency_code = ANY($1)
          AND base_currency_code = 'VND'
        ORDER BY currency_code, timestamp DESC
        """,
        currency_codes,
    )
    return {
        row["currency_code"]: {
            "buy_price":      float(row["buy_price"])      if row["buy_price"]      else None,
            "sell_price":     float(row["sell_price"])     if row["sell_price"]     else None,
            "transfer_price": float(row["transfer_price"]) if row["transfer_price"] else None,
        }
        for row in rows
    }