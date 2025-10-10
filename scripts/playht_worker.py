#!/usr/bin/env python3
import os
import time
import json
from typing import Dict, Any

import psycopg
import requests

DSN = os.getenv("FANTASY_DATABASE_URL")
PLAYHT_USER_ID = os.getenv("PLAYHT_USER_ID")
PLAYHT_API_KEY = os.getenv("PLAYHT_API_KEY")
VOICE_ENGINE = os.getenv("PLAYHT_VOICE_ENGINE", "PlayDialog")
VOICE = os.getenv("PLAYHT_VOICE", "")  # optional manifest url or named voice
OUTPUT_FORMAT = os.getenv("PLAYHT_FORMAT", "mp3")
POLL_SEC = int(os.getenv("PLAYHT_POLL_SECONDS", "30"))

PLAYHT_STREAM_URL = "https://api.play.ht/api/v2/tts/stream"


def _playht_stream(text: str) -> bytes:
    headers = {
        "X-USER-ID": PLAYHT_USER_ID or "",
        "AUTHORIZATION": PLAYHT_API_KEY or "",
        "accept": "audio/mpeg",
        "content-type": "application/json",
    }
    body = {
        "text": text,
        "voice_engine": VOICE_ENGINE,
        "output_format": OUTPUT_FORMAT,
    }
    if VOICE:
        body["voice"] = VOICE
    resp = requests.post(PLAYHT_STREAM_URL, headers=headers, data=json.dumps(body), timeout=120)
    if not resp.ok:
        raise RuntimeError(f"playht error {resp.status_code}: {resp.text[:200]}")
    return resp.content


def _store_asset(conn, job_id: int, kind: str, data: bytes) -> None:
    # For now, store as data: URL in content_assets.url; in prod use GCS and store signed URL
    import base64
    b64 = base64.b64encode(data).decode("ascii")
    url = f"data:audio/mpeg;base64,{b64}"
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO content_assets(job_id, kind, url, size) VALUES (%s, %s, %s, %s)",
            (job_id, kind, url, len(data)),
        )


def main() -> None:
    if not DSN:
        print("FANTASY_DATABASE_URL not set")
        raise SystemExit(1)
    if not (PLAYHT_USER_ID and PLAYHT_API_KEY):
        print("PLAYHT credentials not set; worker idle")
        while True:
            time.sleep(POLL_SEC)
    while True:
        try:
            with psycopg.connect(DSN) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT id, inputs_ref FROM content_jobs WHERE kind='podcast' AND (status IS NULL OR status='queued') ORDER BY requested_at ASC LIMIT 1 FOR UPDATE SKIP LOCKED"
                    )
                    row = cur.fetchone()
                if not row:
                    time.sleep(POLL_SEC)
                    continue
                job_id, inputs_ref = row
                script_text = ""
                try:
                    if isinstance(inputs_ref, str):
                        inputs = json.loads(inputs_ref)
                    else:
                        inputs = inputs_ref or {}
                    script_text = str(inputs.get("script") or "")
                except Exception:
                    script_text = ""
                with conn.transaction():
                    with conn.cursor() as cur:
                        cur.execute("UPDATE content_jobs SET status='running' WHERE id=%s", (job_id,))
                    if not script_text:
                        with conn.cursor() as cur:
                            cur.execute("UPDATE content_jobs SET status='failed', completed_at=now() WHERE id=%s", (job_id,))
                    else:
                        audio = _playht_stream(script_text)
                        _store_asset(conn, int(job_id), "audio", audio)
                        with conn.cursor() as cur:
                            cur.execute("UPDATE content_jobs SET status='completed', completed_at=now() WHERE id=%s", (job_id,))
        except Exception as e:
            print(f"playht loop error: {e}")
            time.sleep(POLL_SEC)

if __name__ == "__main__":
    main()
