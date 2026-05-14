"""Shared MySQL connection helper using mysql-connector-python pool."""
import os
import time
import logging
import mysql.connector
from mysql.connector import pooling, Error
from contextlib import contextmanager

try:
    from flask import g  # optional, only available within Flask context
except Exception:  # pragma: no cover
    g = None

logger = logging.getLogger(__name__)

_pool = None

def get_pool(retries=5, delay=3):
    global _pool
    if _pool is not None:
        return _pool

    host = os.getenv("DB_HOST", "localhost")
    port = int(os.getenv("DB_PORT", "3306"))
    user = os.getenv("DB_USER", "bank")
    password = os.getenv("DB_PASSWORD", "bank123")
    database = os.getenv("DB_NAME", "banking")
    pool_size = int(os.getenv("DB_POOL_SIZE", "10"))

    last_err = None
    for attempt in range(1, retries + 1):
        try:
            _pool = pooling.MySQLConnectionPool(
                pool_name="bank_pool",
                pool_size=pool_size,
                host=host,
                port=port,
                user=user,
                password=password,
                database=database,
                allow_local_infile=True,
                charset="utf8mb4",
            )
            logger.info("MySQL connection pool created (attempt %d)", attempt)
            return _pool
        except Error as exc:
            last_err = exc
            logger.warning("MySQL pool failed (attempt %d/%d): %s", attempt, retries, exc)
            time.sleep(delay)

    raise ConnectionError(
        f"Could not connect to MySQL at {host}:{port}/{database}: {last_err}"
    )

@contextmanager
def get_conn():
    conn = get_pool().get_connection()
    try:
        yield conn
    finally:
        conn.close()

def _current_user_id():
    """Best-effort fetch of authenticated user id for audit triggers."""
    try:
        if g is not None and hasattr(g, "current_user") and g.current_user:
            return g.current_user.get("uid")
    except Exception:
        pass
    return None

@contextmanager
def get_cursor(dictionary=True, commit=False):
    with get_conn() as conn:
        cur = conn.cursor(dictionary=dictionary)
        try:
            # Inject current user id into the MySQL session so audit triggers
            # can record PerformedBy via @app_user_id.
            try:
                cur.execute("SET @app_user_id = %s", (_current_user_id(),))
            except Exception:
                pass
            yield cur
            if commit:
                conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
