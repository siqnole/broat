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

            await cur.execute("""
                CREATE TABLE IF NOT EXISTS server_prefixes (
                    server_id  VARCHAR(64) NOT NULL,
                    prefix     VARCHAR(32) NOT NULL,
                    PRIMARY KEY (server_id, prefix)
                )
            """)

            # user_prefixes: migrate from old single-prefix schema if needed
            # Old schema had (user_id PRIMARY KEY, prefix) — new schema uses
            # composite key (user_id, prefix) to allow multiple prefixes per user.
            try:
                await cur.execute("""
                    SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS
                    WHERE TABLE_SCHEMA = DATABASE()
                      AND TABLE_NAME   = 'user_prefixes'
                      AND CONSTRAINT_TYPE = 'PRIMARY KEY'
                """)
                row = await cur.fetchone()
                if row and row[0]:
                    # table exists — check column count in PK
                    await cur.execute("""
                        SELECT COUNT(*) FROM information_schema.KEY_COLUMN_USAGE
                        WHERE TABLE_SCHEMA = DATABASE()
                          AND TABLE_NAME   = 'user_prefixes'
                          AND CONSTRAINT_NAME = 'PRIMARY'
                    """)
                    pk_cols = (await cur.fetchone())[0]
                    if pk_cols == 1:
                        # old single-column PK — migrate
                        await cur.execute("ALTER TABLE user_prefixes DROP PRIMARY KEY")
                        await cur.execute(
                            "ALTER TABLE user_prefixes ADD PRIMARY KEY (user_id, prefix)"
                        )
                        await cur.execute(
                            "ALTER TABLE user_prefixes MODIFY user_id VARCHAR(64) NOT NULL"
                        )
                        log.info("migrated user_prefixes to composite primary key")
            except Exception:
                pass

            await cur.execute("""
                CREATE TABLE IF NOT EXISTS user_prefixes (
                    user_id  VARCHAR(64) NOT NULL,
                    prefix   VARCHAR(32) NOT NULL,
                    PRIMARY KEY (user_id, prefix)
                )
            """)
    log.info("database tables verified")


# ---------------------------------------------------------------------------
# Prefix helpers
# ---------------------------------------------------------------------------

async def get_server_prefixes(server_id: str) -> list[str]:
    """Return all custom prefixes for a server (may be empty)."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT prefix FROM server_prefixes WHERE server_id = %s",
                (server_id,),
            )
            rows = await cur.fetchall()
            return [r[0] for r in rows]


async def add_server_prefix(server_id: str, prefix: str) -> bool:
    """Add a prefix for a server. Returns False if it already exists."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            try:
                await cur.execute(
                    "INSERT INTO server_prefixes (server_id, prefix) VALUES (%s, %s)",
                    (server_id, prefix),
                )
                return True
            except Exception:
                return False


async def remove_server_prefix(server_id: str, prefix: str) -> bool:
    """Remove a prefix from a server. Returns False if it didn't exist."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "DELETE FROM server_prefixes WHERE server_id = %s AND prefix = %s",
                (server_id, prefix),
            )
            return cur.rowcount > 0


async def get_user_prefixes(user_id: str) -> list[str]:
    """Return all custom prefixes for a user (may be empty)."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT prefix FROM user_prefixes WHERE user_id = %s",
                (user_id,),
            )
            rows = await cur.fetchall()
            return [r[0] for r in rows]


async def add_user_prefix(user_id: str, prefix: str) -> bool:
    """Add a prefix for a user. Returns False if it already exists."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            try:
                await cur.execute(
                    "INSERT INTO user_prefixes (user_id, prefix) VALUES (%s, %s)",
                    (user_id, prefix),
                )
                return True
            except Exception:
                return False


async def remove_user_prefix(user_id: str, prefix: str) -> bool:
    """Remove a prefix from a user. Returns False if it didn't exist."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "DELETE FROM user_prefixes WHERE user_id = %s AND prefix = %s",
                (user_id, prefix),
            )
            return cur.rowcount > 0


async def clear_user_prefixes(user_id: str) -> bool:
    """Remove all of a user's personal prefixes. Returns False if none existed."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "DELETE FROM user_prefixes WHERE user_id = %s",
                (user_id,),
            )
            return cur.rowcount > 0


async def close() -> None:
    """Close the connection pool."""
    global _pool
    if _pool is not None:
        _pool.close()
        await _pool.wait_closed()
        _pool = None
        log.info("database pool closed")
