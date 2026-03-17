from contextlib import asynccontextmanager
from fastapi import FastAPI
from db.connection import init_pool, close_pool
from api.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_pool()
    yield
    await close_pool()


app = FastAPI(
    title="Portfolio Analysis Service",
    lifespan=lifespan,
)

app.include_router(router)