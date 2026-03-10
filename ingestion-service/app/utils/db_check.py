from datetime import timedelta, timezone, datetime
from app.db import get_conn


def has_sufficient_history(asset_id: int, source_id: int, min_days: int = 7):

    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT MIN(timestamp), MAX(timestamp)
        FROM market_price_raw
        WHERE asset_id = %s
        AND source_id = %s
        """,
        (asset_id, source_id)
    )

    min_ts, max_ts = cur.fetchone()

    cur.close()
    conn.close()

    if not min_ts or not max_ts:
        return False

    return (max_ts - min_ts) >= timedelta(days=min_days)

def get_latest_timestamp(asset_id: int, source_id: int):

    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT MAX(timestamp)
        FROM market_price_raw
        WHERE asset_id = %s
        AND source_id = %s
        """,
        (asset_id, source_id)
    )

    result = cur.fetchone()[0]

    cur.close()
    conn.close()

    return result


def is_data_stale(asset_id: int, source_id: int, threshold_days: int = 2):

    latest = get_latest_timestamp(asset_id, source_id)

    if latest is None:
        return True

    now = datetime.now(timezone.utc)

    age = now - latest.replace(tzinfo=timezone.utc)

    return age > timedelta(days=threshold_days)

def has_sufficient_forex_history(currency: str, min_days: int = 7):

    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT MIN(timestamp), MAX(timestamp)
        FROM exchange_rates
        WHERE currency_code = %s
        """,
        (currency,)
    )

    min_ts, max_ts = cur.fetchone()

    cur.close()
    conn.close()

    if not min_ts or not max_ts:
        return False

    return (max_ts - min_ts) >= timedelta(days=min_days)


def get_latest_forex_timestamp(currency: str):

    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT MAX(timestamp)
        FROM exchange_rates
        WHERE currency_code = %s
        """,
        (currency,)
    )

    result = cur.fetchone()[0]

    cur.close()
    conn.close()

    return result


def is_forex_data_stale(currency: str, threshold_days: int = 2):

    latest = get_latest_forex_timestamp(currency)

    if latest is None:
        return True

    now = datetime.now(timezone.utc)

    age = now - latest.replace(tzinfo=timezone.utc)

    return age > timedelta(days=threshold_days)