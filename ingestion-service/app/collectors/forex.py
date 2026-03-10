import requests
from datetime import datetime
from app.db import get_conn


# ---------- API ----------
FOREX_HISTORY_API = "https://m.cafef.vn/du-lieu/ajax/exchangerate/AjaxRateCurrencyByNameAndDate.ashx?name={}&date=1y"
FOREX_WEEK_API = "https://m.cafef.vn/du-lieu/ajax/exchangerate/AjaxRateCurrencyByNameAndDate.ashx?name={}&date=1w"


# ---------- STATIC IDS ----------
SOURCE_ID_CAFEF = 1
BASE_CURRENCY = "VND"

# ---------- FETCH ----------
def fetch_forex_history(currency):

    url = FOREX_HISTORY_API.format(currency)

    r = requests.get(url, timeout=10)
    r.raise_for_status()

    data = r.json()

    return data["Data"]


def fetch_forex_latest(currency):

    url = FOREX_WEEK_API.format(currency)

    r = requests.get(url, timeout=10)
    r.raise_for_status()

    data = r.json()

    return data["Data"]


# ---------- NORMALIZE ----------
def normalize_forex(currency, rows_raw):

    rows = []

    for row in rows_raw:

        timestamp = datetime.fromtimestamp(row["timeSpin"] / 1000)

        rows.append((
            currency,
            row["buyCash"],
            row["purchaseTransfer"],
            row["price"],
            SOURCE_ID_CAFEF,
            BASE_CURRENCY,
            timestamp
        ))

    return rows


# ---------- INSERT ----------
def insert_rates(conn, rows):

    if not rows:
        return 0

    cur = conn.cursor()

    cur.executemany(
        """
        INSERT INTO exchange_rates
        (currency_code, buy_price, transfer_price, sell_price, source_id, base_currency_code, timestamp)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT DO NOTHING
        """,
        rows
    )

    inserted = cur.rowcount

    cur.close()

    return inserted


# ---------- INGEST ----------
def ingest_forex(currencies, mode="latest"):

    if isinstance(currencies, str):
        currencies = [currencies]

    conn = get_conn()
    total = 0

    try:

        for currency in currencies:

            try:

                print(f"Fetching {mode} forex for {currency}")

                if mode == "history":
                    data = fetch_forex_history(currency)
                else:
                    data = fetch_forex_latest(currency)

                rows = normalize_forex(currency, data)

                inserted = insert_rates(conn, rows)

                total += inserted

            except Exception as e:
                print(f"❌ Failed {currency}: {e}")

        conn.commit()

    finally:
        conn.close()

    print(f"✅ Total rows inserted: {total}")

 ## ---------- WRAPPERS ----------
def ingest_forex_historical(currencies):
    ingest_forex(currencies, mode="history")


def ingest_forex_latest(currencies):
    ingest_forex(currencies, mode="latest")   