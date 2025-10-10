#!/usr/bin/env python3
import os
import time
import hashlib
import json
from typing import Dict, Any, List

import psycopg
import feedparser

DSN = os.getenv("FANTASY_DATABASE_URL")
POLL_SEC = int(os.getenv("RSS_POLL_SECONDS", "300"))
BATCH = int(os.getenv("RSS_BATCH", "50"))


def _hash_item(url: str, title: str) -> str:
    h = hashlib.sha256()
    h.update((url or "").encode("utf-8"))
    h.update((title or "").encode("utf-8"))
    return h.hexdigest()


def _ingest_feed(conn, source_id: int, url: str) -> int:
    parsed = feedparser.parse(url)
    inserted = 0
    with conn.cursor() as cur:
        for e in parsed.entries:
            link = getattr(e, "link", None) or ""
            title = getattr(e, "title", None) or ""
            published = getattr(e, "published_parsed", None)
            published_at = None
            if published:
                try:
                    import datetime as dt
                    published_at = dt.datetime.fromtimestamp(time.mktime(published))
                except Exception:
                    published_at = None
            summary = getattr(e, "summary", None) or getattr(e, "description", None) or ""
            h = _hash_item(link, title)
            try:
                cur.execute(
                    """
                    INSERT INTO content_items(source_id, title, url, published_at, text, entities, hash)
                    VALUES (%s, %s, %s, %s, %s, '{}'::jsonb, %s)
                    ON CONFLICT (hash) DO NOTHING
                    """,
                    (source_id, title, link, published_at, summary, h),
                )
                inserted += cur.rowcount
            except Exception:
                continue
    return inserted


def main() -> None:
    if not DSN:
        print("FANTASY_DATABASE_URL not set")
        raise SystemExit(1)
    while True:
        try:
            with psycopg.connect(DSN) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT id, url_or_handle FROM content_sources WHERE kind='rss' AND active = TRUE ORDER BY created_at DESC LIMIT %s",
                        (BATCH,),
                    )
                    sources = cur.fetchall()
                for sid, feed_url in sources:
                    try:
                        _ingest_feed(conn, int(sid), str(feed_url))
                    except Exception as e:
                        print(f"rss ingest error {feed_url}: {e}")
        except Exception as e:
            print(f"rss loop error: {e}")
        time.sleep(POLL_SEC)

if __name__ == "__main__":
    main()
