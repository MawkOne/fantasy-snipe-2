import contextlib
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Iterator

from .config import get_database_url


def _connect():
    return psycopg2.connect(get_database_url(), cursor_factory=RealDictCursor)


@contextlib.contextmanager
def get_cursor() -> Iterator[RealDictCursor]:
    conn = _connect()
    try:
        conn.autocommit = False
        cur = conn.cursor()
        try:
            yield cur
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
    finally:
        conn.close()


