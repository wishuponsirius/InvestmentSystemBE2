import requests
from app.db import get_conn

CAFEEF_GOLD_HISTORY_API = "https://cafef.vn/du-lieu/Ajax/ajaxgoldpricehistory.ashx?index=all"
CAFEF_GOLD_LASTEST_API = "https://m.cafef.vn/du-lieu/Ajax/ajaxgoldprice.ashx?index=00"

# ---------- STATIC IDS ----------
ASSET_ID_GOLD = 1
SOURCE_ID_CAFEF = 1
UNIT_LUONG = 1
CURRENCY_VND = "VND"
SJC_NAME = "Vàng miếng SJC"
REGION_ID_VN = 7   # Toan Quoc-VN

CAFEF_PRICE_MULTIPLIER = 10_000
CAFEF_PRICE_MULTIPLIER_HISTORICAL = 1_000_000

# ---------- FETCH ----------
def fetch_vn_historical():

    r = requests.get(CAFEEF_GOLD_HISTORY_API, timeout=10)
    r.raise_for_status()

    data = r.json()

    return data["Data"]["goldPriceWorldHistories"]

def fetch_vn_latest():

    r = requests.get(CAFEF_GOLD_LASTEST_API, timeout=10)
    r.raise_for_status()

    data = r.json()

    return data["Data"]


# ---------- NORMALIZE ----------
def normalize_vn_historical(histories: list[dict]):

    rows = []

    for row in histories:

        rows.append((
            ASSET_ID_GOLD,
            SOURCE_ID_CAFEF,
            REGION_ID_VN,
            UNIT_LUONG,
            CURRENCY_VND,
            row["buyPrice"] * CAFEF_PRICE_MULTIPLIER_HISTORICAL,
            row["sellPrice"] * CAFEF_PRICE_MULTIPLIER_HISTORICAL,
            row["createdAt"]
        ))

    return rows

def normalize_vn_latest(data: list[dict]):

    rows = []

    for row in data:

        if row["name"] != SJC_NAME:
            continue

        rows.append((
            ASSET_ID_GOLD,
            SOURCE_ID_CAFEF,
            REGION_ID_VN,
            UNIT_LUONG,
            CURRENCY_VND,
            row["buyPrice"] * CAFEF_PRICE_MULTIPLIER,
            row["sellPrice"] * CAFEF_PRICE_MULTIPLIER,
            row["lastUpdated"]
        ))

    return rows

# ---------- INSERT ----------
def insert_prices(rows):

    if not rows:
        print("⚠️ No historical rows")
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
        print("⚠️ No new Gold price rows inserted (all duplicates)")
    else:
        print(f"✅ Inserted {cur.rowcount} Gold price rows")

    cur.close()
    conn.close()    


# ---------- INGEST ----------
def ingest_gold_vn_historical():

    histories = fetch_vn_historical()

    rows = normalize_vn_historical(histories)

    insert_prices(rows)

def ingest_gold_vn_latest():

    data = fetch_vn_latest()

    rows = normalize_vn_latest(data)

    insert_prices(rows)    