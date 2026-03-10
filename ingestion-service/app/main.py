from fastapi import FastAPI, HTTPException, Path
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from fastapi.openapi.utils import get_openapi
from app.collectors.gold import (
    ingest_gold_vn_historical, ingest_gold_vn_latest,
    ASSET_ID_GOLD, SOURCE_ID_CAFEF)
from app.collectors.silver import (
    ingest_silver_vn_historical,
    ingest_silver_vn_latest,
    ASSET_ID_SILVER
)
from app.collectors.forex import (
    ingest_forex_historical,
    ingest_forex_latest
)
from app.utils.db_check import (has_sufficient_history, is_data_stale,
    has_sufficient_forex_history, is_forex_data_stale) 
from app.scheduler import start_scheduler
from app.utils.job_status import ingestion_status, update_status

# ---------- CONFIG ----------
GOLD_VN_STALE_THRESHOLD_DAYS = 2
SILVER_VN_STALE_THRESHOLD_DAYS = 2
FOREX_STALE_THRESHOLD_DAYS = 2
CURRENCIES = [
    "AUD","CAD","CHF","CNY","DKK",
    "EUR","GBP","HKD","INR","JPY",
    "KRW","KWD","MYR","NOK","RUB",
    "SEK","SGD","THB","USD"
]
# ---------- LIFESPAN HANDLER ----------

@asynccontextmanager
async def lifespan(app: FastAPI):

    print("🚀 Ingestion service starting...")

    # ---------- GOLD HISTORICAL ----------
    if not has_sufficient_history(ASSET_ID_GOLD, SOURCE_ID_CAFEF):

        print("📜 No historical gold data found. Ingesting...")

        try:
            ingest_gold_vn_historical()
            update_status("gold_vn_historical", "success")
            print("✅ Historical gold ingestion completed")

        except Exception as e:
            update_status("gold_vn_historical", "failed")
            print(f"❌ Historical ingestion failed: {e}")

    else:
        print("✔ Historical gold data already exists. Skipping.")
        update_status("gold_vn_historical", "skipped")


    # ---------- SILVER HISTORICAL ----------

    if not has_sufficient_history(ASSET_ID_SILVER, SOURCE_ID_CAFEF):

        print("📜 No historical silver data found. Ingesting...")

        try:
            ingest_silver_vn_historical()
            update_status("silver_vn_historical", "success")
            print("✅ Historical silver ingestion completed")

        except Exception as e:
            update_status("silver_vn_historical", "failed")
            print(f"❌ Silver historical ingestion failed: {e}")

    else:
        print("✔ Historical silver data already exists. Skipping.")
        update_status("silver_vn_historical", "skipped")

    # ---------- FOREX HISTORICAL ----------

    for currency in CURRENCIES:

        if not has_sufficient_forex_history(currency):

            print(f"📜 No historical forex data for {currency}. Ingesting...")

            try:

                ingest_forex_historical(currency)

                update_status(f"forex_{currency}_historical", "success")

                print(f"✅ Historical forex ingestion completed for {currency}")

            except Exception as e:

                update_status(f"forex_{currency}_historical", "failed")

                print(f"❌ Historical forex ingestion failed for {currency}: {e}")

        else:

            print(f"✔ Historical forex data exists for {currency}. Skipping.")

            update_status(f"forex_{currency}_historical", "skipped")
        
    # ---------- START SCHEDULER ----------
    start_scheduler()

    yield   # ← application runs here

    # Optional shutdown logic
    print("🛑 Ingestion service shutting down...")


# ---------- APP ----------

app = FastAPI(
    title="Market Data Ingestion Service",
    lifespan=lifespan,
    root_path="/ingest"
)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Market Data Ingestion Service",
        version="1.0.0",
        routes=app.routes,
    )

    if "components" not in openapi_schema:
        openapi_schema["components"] = {}

    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }

    openapi_schema["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# ---------- API ENDPOINTS ----------
@app.get("/health")
def health():
    gold_stale= is_data_stale(ASSET_ID_GOLD, SOURCE_ID_CAFEF, GOLD_VN_STALE_THRESHOLD_DAYS)
    silver_stale = is_data_stale(
        ASSET_ID_SILVER, SOURCE_ID_CAFEF, SILVER_VN_STALE_THRESHOLD_DAYS
    )
    forex_stale = {
    currency: is_forex_data_stale(currency, FOREX_STALE_THRESHOLD_DAYS)
    for currency in CURRENCIES
}
    return {
        "status": "running",
        "jobs": ingestion_status,
        "stale_data": {
            "gold_vn": gold_stale,
            "silver_vn": silver_stale,
            "forex": forex_stale
        }
    }

@app.post("/trigger/gold-vn-historical")
def trigger_gold_vn_historical():
    try:
        ingest_gold_vn_historical()
        update_status("gold_vn_historical", "success")
        return {"status": "success"}
    except Exception as e:
        update_status("gold_vn_historical", "failed")
        return {"status": "failed", "error": str(e)}
    

@app.post("/trigger/gold-vn-latest")
def trigger_gold_vn_latest():
    try:
        ingest_gold_vn_latest()
        update_status("gold_vn_latest", "success")
        return {"status": "success"}
    except Exception as e:
        update_status("gold_vn_latest", "failed")
        return {"status": "failed", "error": str(e)}    
    
@app.post("/trigger/silver-vn-historical")
def trigger_silver_historical():
    try:
        ingest_silver_vn_historical()
        update_status("silver_vn_historical", "success")
        return {"status": "success"}
    except Exception as e:
        update_status("silver_vn_historical", "failed")
        return {"status": "failed", "error": str(e)}

@app.post("/trigger/silver-vn-latest")
def trigger_silver_latest():
    try:
        ingest_silver_vn_latest()
        update_status("silver_vn_latest", "success")
        return {"status": "success"}
    except Exception as e:
        update_status("silver_vn_latest", "failed")
        return {"status": "failed", "error": str(e)}

@app.post("/trigger/forex/{currency}/latest")
def trigger_forex_latest(
    currency: str = Path(..., description=f"Accepted currencies: {', '.join(CURRENCIES)}"
    )):

    currency = currency.upper()

    if currency not in CURRENCIES:
        raise HTTPException(status_code=400, detail="Unsupported currency")

    try:

        ingest_forex_latest(currency)

        update_status(f"forex_{currency}_latest", "success")

        return {"status": "success"}

    except Exception as e:

        update_status(f"forex_{currency}_latest", "failed")

        return {"status": "failed", "error": str(e)}

@app.post("/trigger/forex/{currency}/historical")
def trigger_forex_historical(currency: str
    = Path(..., description=f"Accepted currencies: {', '.join(CURRENCIES)}")
    ):

    currency = currency.upper()

    if currency not in CURRENCIES:
        raise HTTPException(status_code=400, detail="Unsupported currency")

    try:

        ingest_forex_historical(currency)

        update_status(f"forex_{currency}_historical", "success")

        return {"status": "success"}

    except Exception as e:

        update_status(f"forex_{currency}_historical", "failed")

        return {"status": "failed", "error": str(e)}                