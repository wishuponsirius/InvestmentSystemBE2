import requests
from app.db import get_conn


SILVER_HISTORY_API = "https://apiweb.cafef.vn/api/v1/Silver/GetSilverHistoryChart?time=all"
SILVER_WEEK_API = "https://apiweb.cafef.vn/api/v1/Silver/GetSilverHistoryChart?time=1w"


# ---------- STATIC IDS ----------
ASSET_ID_SILVER = 2
SOURCE_ID_CAFEF = 1
UNIT_KG = 6
CURRENCY_VND = "VND"
REGION_ID_VN = 7


# ---------- FETCH ----------
def fetch_silver_vn_historical():

    r = requests.get(SILVER_HISTORY_API, timeout=10)
    r.raise_for_status()

    data = r.json()

    return data["data"]


def fetch_silver_vn_latest():

    r = requests.get(SILVER_WEEK_API, timeout=10)
    r.raise_for_status()

    data = r.json()

    return data["data"]


# ---------- NORMALIZE ----------
def normalize_silver(rows_raw: list[dict]):

    rows = []

    for row in rows_raw:

        rows.append((
            ASSET_ID_SILVER,
            SOURCE_ID_CAFEF,
            REGION_ID_VN,
            UNIT_KG,
            CURRENCY_VND,
            row["buy"],
            row["sell"],
            row["date"]
        ))

    return rows


# ---------- INSERT ----------
def insert_prices(rows):

    if not rows:
        print("⚠️ No rows to insert")
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
        print("⚠️ No new Silver Price rows inserted (all duplicates)")
    else:
        print(f"✅ Inserted {cur.rowcount} Silver Price rows")

    cur.close()
    conn.close()


# ---------- INGEST ----------
def ingest_silver_vn_historical():

    data = fetch_silver_vn_historical()

    rows = normalize_silver(data)

    insert_prices(rows)


def ingest_silver_vn_latest():

    data = fetch_silver_vn_latest()

    rows = normalize_silver(data)

    insert_prices(rows)