import json, os, sqlite3
from datetime import datetime, timezone

DB_PATH = os.getenv("DB_PATH", "geowatch.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS markets (
    id INTEGER PRIMARY KEY,
    dyad TEXT, source TEXT, market_id TEXT, question TEXT,
    prob REAL, volume REAL, url TEXT, fetched_at TEXT
);
CREATE TABLE IF NOT EXISTS profiles (
    iso TEXT PRIMARY KEY, fetched_at TEXT, payload TEXT
);
CREATE INDEX IF NOT EXISTS ix_mkt ON markets(dyad, fetched_at);
"""

def conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    c.executescript(SCHEMA)
    return c

def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def save_market(c, dyad, m):
    c.execute("INSERT INTO markets(dyad,source,market_id,question,prob,volume,url,fetched_at) "
              "VALUES (?,?,?,?,?,?,?,?)",
              (dyad, m["source"], m["id"], m["question"], m["prob"], m.get("volume"), m["url"], now()))

def market_rows(c, dyad):
    return c.execute("SELECT * FROM markets WHERE dyad=? ORDER BY fetched_at", (dyad,)).fetchall()

def save_profile(c, iso, payload):
    c.execute("INSERT OR REPLACE INTO profiles(iso,fetched_at,payload) VALUES (?,?,?)",
              (iso, now(), json.dumps(payload, ensure_ascii=False)))

def get_profile(c, iso):
    r = c.execute("SELECT payload, fetched_at FROM profiles WHERE iso=?", (iso,)).fetchone()
    return (json.loads(r["payload"]), r["fetched_at"]) if r else (None, None)
