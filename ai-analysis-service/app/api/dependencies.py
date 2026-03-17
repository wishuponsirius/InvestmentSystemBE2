from fastapi import Request
from db.connection import get_connection


async def get_db_conn(request: Request):
    async with get_connection() as conn:
        yield conn