"""SQLite local : profils pays (l'historique des cotes est dans history.py / data/)."""
import json, os, sqlite3
from datetime import datetime, timezone

DB_PATH = os.getenv("DB_PATH", "geowatch.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS profiles (
    iso TEXT PRIMARY KEY, fetched_at TEXT, payload TEXT
);
"""

def conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    c.executescript(SCHEMA)
    return c

def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def save_profile(c, iso, payload):
    c.execute("INSERT OR REPLACE INTO profiles(iso,fetched_at,payload) VALUES (?,?,?)",
              (iso, now(), json.dumps(payload, ensure_ascii=False)))

def get_profile(c, iso):
    r = c.execute("SELECT payload, fetched_at FROM profiles WHERE iso=?", (iso,)).fetchone()
    return (json.loads(r["payload"]), r["fetched_at"]) if r else (None, None)
