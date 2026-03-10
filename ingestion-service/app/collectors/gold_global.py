import requests
import time
from datetime import datetime, timezone
from app.db import get_conn

KITCO_GQL_URL = "https://kdb-gw.prod.kitco.com/graphql"

# ---------- STATIC IDS ----------
ASSET_ID_GOLD = 1
SOURCE_ID_KITCO = 2
REGION_ID_GLOBAL = 8
UNIT_OUNCE = 4
CURRENCY_USD = "USD"

START_2025 = int(datetime(2025, 1, 1, tzinfo=timezone.utc).timestamp())

HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0"
}

QUERY = """
query GoldHistory($start: Int!, $end: Int!) {
  goldHistory: GetMetalHistory(
    symbol: "AU"
    currency: "USD"
    startTime: $start
    endTime: $end
    groupBy: "1d"
    limit: 365
  ) {
    results {
      timestamp
      bid
      ask
    }
  }
}
"""
QUERY_LATEST = """
query GoldLatest($start: Int!, $end: Int!) {
  goldHistory: GetMetalHistory(
    symbol: "AU"
    currency: "USD"
    startTime: $start
    endTime: $end
    groupBy: "1h"
    limit: 24
  ) {
    results {
      timestamp
      bid
      ask
    }
  }
}
"""

# ---------- FETCH ----------
def fetch_global_historical():

    payload = {
        "query": QUERY,
        "variables": {
            "start": START_2025,
            "end": int(time.time())
        }
    }

    r = requests.post(KITCO_GQL_URL, headers=HEADERS, json=payload, timeout=10)
    r.raise_for_status()

    data = r.json()

    return data["data"]["goldHistory"]["results"]


def fetch_global_latest():

    now = int(time.time())

    payload = {
        "query": QUERY_LATEST,
        "variables": {
            "start": now - 86400,
            "end": now
        }
    }

    r = requests.post(KITCO_GQL_URL, headers=HEADERS, json=payload, timeout=10)
    r.raise_for_status()

    data = r.json()

    return data["data"]["goldHistory"]["results"]


# ---------- NORMALIZE ----------
def normalize_global_historical(histories: list[dict]):

    rows = []

    for row in histories:

        ts = datetime.fromtimestamp(row["timestamp"], tz=timezone.utc)

        rows.append((
            ASSET_ID_GOLD,
            SOURCE_ID_KITCO,
            REGION_ID_GLOBAL,
            UNIT_OUNCE,
            CURRENCY_USD,
            row["bid"],
            row["ask"],
            ts
        ))

    return rows


def normalize_global_latest(rows: list[dict]):

    normalized = []

    for row in rows:

        ts = datetime.fromtimestamp(row["timestamp"], tz=timezone.utc)

        normalized.append((
            ASSET_ID_GOLD,
            SOURCE_ID_KITCO,
            REGION_ID_GLOBAL,
            UNIT_OUNCE,
            CURRENCY_USD,
            row["bid"],
            row["ask"],
            ts
        ))

    return normalized


# ---------- INSERT ----------
def insert_prices(rows):

    if not rows:
        print("⚠️ No global gold rows")
        return

    conn = get_conn()
    cur = conn.cursor()

    cur.executemany(
        """
        INSERT INTO market_price_raw
        (asset_id, source_id, region_id, unit_id, currency_code, buy_price, sell_price, timestamp)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT DO NOTHING
        """,
        rows
    )

    conn.commit()

    if cur.rowcount == 0:
        print("⚠️ No new Global Gold rows inserted (all duplicates)")
    else:
        print(f"✅ Inserted {cur.rowcount} Global Gold rows")

    cur.close()
    conn.close()


# ---------- INGEST ----------
def ingest_gold_global_historical():

    histories = fetch_global_historical()

    rows = normalize_global_historical(histories)

    insert_prices(rows)


def ingest_gold_global_latest():

    rows = fetch_global_latest()

    normalized = normalize_global_latest(rows)

    insert_prices(normalized)