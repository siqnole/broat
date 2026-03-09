"""MySQL connection pool helper for Bronx."""
from __future__ import annotations

import os
import logging

import aiomysql

log = logging.getLogger("bronx.db")

_pool: aiomysql.Pool | None = None


async def get_pool() -> aiomysql.Pool:
    """Return the shared connection pool, creating it on first call."""
    global _pool
    if _pool is None:
        _pool = await aiomysql.create_pool(
            host=os.environ.get("DB_HOST", "localhost"),
            port=int(os.environ.get("DB_PORT", 3306)),
            user=os.environ.get("DB_USER", "bronx"),
            password=os.environ.get("DB_PASS", "bronx"),
            db=os.environ.get("DB_NAME", "bronxstout"),
            minsize=1,
            maxsize=5,
            autocommit=True,
        )
        log.info("database pool created (%s@%s/%s)",
                 os.environ.get("DB_USER", "bronx"),
                 os.environ.get("DB_HOST", "localhost"),
                 os.environ.get("DB_NAME", "bronxstout"))
    return _pool


async def ensure_tables() -> None:
    """Create tables if they don't already exist."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("""
                CREATE TABLE IF NOT EXISTS economy (
                    user_id     VARCHAR(64) PRIMARY KEY,
                    balance     BIGINT      NOT NULL DEFAULT 0,
                    last_daily  DATETIME    NULL,
                    last_work   DATETIME    NULL,
                    last_beg    DATETIME    NULL,
                    last_crime  DATETIME    NULL,
                    last_fish   DATETIME    NULL,
                    last_search DATETIME    NULL
                )
            """)
            # migrate existing tables that may be missing new columns
            for col in ("last_work", "last_beg", "last_crime", "last_fish", "last_search"):
                try:
                    await cur.execute(
                        f"ALTER TABLE economy ADD COLUMN IF NOT EXISTS {col} DATETIME NULL"
                    )
                except Exception:
                    pass
    log.info("database tables verified")


async def close() -> None:
    """Close the connection pool."""
    global _pool
    if _pool is not None:
        _pool.close()
        await _pool.wait_closed()
        _pool = None
        log.info("database pool closed")
