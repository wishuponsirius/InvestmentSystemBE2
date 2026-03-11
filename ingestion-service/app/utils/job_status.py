from datetime import datetime, timezone

CURRENCIES = [
    "AUD","CAD","CHF","CNY","DKK",
    "EUR","GBP","HKD","INR","JPY",
    "KRW","KWD","MYR","NOK","RUB",
    "SEK","SGD","THB","USD"
]

ingestion_status = {
    "gold_vn_latest": {"status": None, "timestamp": None},
    "gold_vn_historical": {"status": None, "timestamp": None},
    "gold_global_latest": {"status": None, "timestamp": None},
    "gold_global_historical": {"status": None, "timestamp": None},
    "silver_vn_latest": {"status": None, "timestamp": None},
    "silver_vn_historical": {"status": None, "timestamp": None},
    "silver_global_latest": {"status": None, "timestamp": None},
    "silver_global_historical": {"status": None, "timestamp": None},
}

# auto-register forex jobs
for currency in CURRENCIES:
    ingestion_status[f"forex_{currency}_latest"] = {"status": None, "timestamp": None}
    ingestion_status[f"forex_{currency}_historical"] = {"status": None, "timestamp": None}


def update_status(job_name: str, status: str):

    ingestion_status[job_name] = {
        "status": status,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }