from psycopg_pool import ConnectionPool
from .settings import settings

pool = ConnectionPool(
    conninfo=settings.PG_DSN,
    min_size=settings.PG_POOL_MIN,
    max_size=settings.PG_POOL_MAX,
    open=True,
)

def fetch_all(sql: str, params: dict | None = None):
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or {})
            return cur.fetchall()

def fetch_one(sql: str, params: dict | None = None):
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or {})
            return cur.fetchone()
