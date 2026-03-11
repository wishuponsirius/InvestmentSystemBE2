from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from app.collectors.gold import ingest_gold_vn_latest
from app.collectors.silver import ingest_silver_vn_latest
from app.collectors.forex import ingest_forex_latest
from app.collectors.gold_global import ingest_gold_global_latest
from app.utils.job_status import update_status
from app.collectors.silver_global import ingest_silver_global_latest

scheduler = BackgroundScheduler()

CURRENCIES = [
    "AUD","CAD","CHF","CNY","DKK",
    "EUR","GBP","HKD","INR","JPY",
    "KRW","KWD","MYR","NOK","RUB",
    "SEK","SGD","THB","USD"
]

# --------- GOLD VN ----------
def job_gold_vn_latest():
    print(f"[{datetime.now()}] Running scheduled job: gold_vn_latest")
    
    try:
        ingest_gold_vn_latest()
        update_status("gold_vn_latest", "success")
    except Exception:
        update_status("gold_vn_latest", "failed")

# --------- GOLD GLOBAL ----------
def job_gold_global_latest():
    print(f"[{datetime.now()}] Running scheduled job: gold_global_latest")

    try:
        ingest_gold_global_latest()
        update_status("gold_global_latest", "success")
    except Exception:
        update_status("gold_global_latest", "failed")

# --------- SILVER VN ----------
def job_silver_vn_latest():
    print(f"[{datetime.now()}] Running scheduled job: silver_vn_latest")
    
    try:
        ingest_silver_vn_latest()
        update_status("silver_vn_latest", "success")
    except Exception:
        update_status("silver_vn_latest", "failed")

# --------- SILVER GLOBAL ----------
def job_silver_global_latest():
    print(f"[{datetime.now()}] Running scheduled job: silver_global_latest")

    try:
        ingest_silver_global_latest()
        update_status("silver_global_latest", "success")
    except Exception as e:
        print(e)
        update_status("silver_global_latest", "failed")

# --------- FOREX ----------
def job_forex_latest():
    print(f"[{datetime.now()}] Running scheduled job: forex_latest")

    try:
        ingest_forex_latest(CURRENCIES)

        for currency in CURRENCIES:
            update_status(f"forex_{currency}_latest", "success")

    except Exception:
        for currency in CURRENCIES:
            update_status(f"forex_{currency}_latest", "failed")

# --------- START ----------

def start_scheduler():
    print("Starting scheduler...")

    #   Run immediately on startup
    job_gold_vn_latest()
    job_silver_vn_latest()
    job_forex_latest()
    job_gold_global_latest()    
    job_silver_global_latest()

    # Schedule recurring jobs
    scheduler.add_job(
        job_gold_vn_latest,
        "cron",
        minute=5,
        id="gold_vn_latest",
        replace_existing=True
    )

    scheduler.add_job(
        job_silver_vn_latest,
        "cron",
        minute=10,
        id="silver_vn_latest",
        replace_existing=True
    )

    scheduler.add_job(
        job_forex_latest,
        "cron",
        minute=15, 
        id="forex_latest",
        replace_existing=True
    )

    scheduler.add_job(
    job_gold_global_latest,
    "cron",
    minute=7,
    id="gold_global_latest",
    replace_existing=True
    )

    scheduler.add_job(
    job_silver_global_latest,
    "cron",
    minute=12,
    id="silver_global_latest",
    replace_existing=True
    )

    scheduler.start()
    print("Scheduler started.")
    print("Job 'gold_vn_latest' will run every hour at minute 5.")
    print("Job 'gold_global_latest' will run every hour at minute 7.")
    print("Job 'silver_vn_latest' will run every hour at minute 10.")
    print("Job 'silver_global_latest' will run every hour at minute 12.")
    print("Job 'forex_latest' will run every hour at minute 15.")