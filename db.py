import json, os, sqlite3
from datetime import datetime, timezone

DB_PATH = os.getenv("DB_PATH", "geowatch.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS signals (
    id INTEGER PRIMARY KEY,
    dyad TEXT, source TEXT, kind TEXT, fetched_at TEXT, payload TEXT
);
CREATE TABLE IF NOT EXISTS markets (
    id INTEGER PRIMARY KEY,
    dyad TEXT, source TEXT, market_id TEXT, question TEXT,
    prob REAL, volume REAL, url TEXT, fetched_at TEXT
);
CREATE TABLE IF NOT EXISTS profiles (
    iso TEXT PRIMARY KEY, fetched_at TEXT, payload TEXT
);
CREATE INDEX IF NOT EXISTS ix_sig ON signals(dyad, fetched_at);
CREATE INDEX IF NOT EXISTS ix_mkt ON markets(dyad, fetched_at);
"""

def conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    c.executescript(SCHEMA)
    return c

def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def save_signal(c, dyad, source, kind, payload):
    c.execute("INSERT INTO signals(dyad,source,kind,fetched_at,payload) VALUES (?,?,?,?,?)",
              (dyad, source, kind, now(), json.dumps(payload, ensure_ascii=False)))

def save_market(c, dyad, m):
    c.execute("INSERT INTO markets(dyad,source,market_id,question,prob,volume,url,fetched_at) "
              "VALUES (?,?,?,?,?,?,?,?)",
              (dyad, m["source"], m["id"], m["question"], m["prob"], m.get("volume"), m["url"], now()))

def recent_signals(c, dyad, days):
    return c.execute("SELECT * FROM signals WHERE dyad=? AND fetched_at >= datetime('now', ?) "
                     "ORDER BY fetched_at DESC", (dyad, f"-{days} days")).fetchall()

def latest_markets(c, dyad):
    # dernière cote connue par marché
    return c.execute("""SELECT m.* FROM markets m
        JOIN (SELECT market_id, MAX(fetched_at) f FROM markets WHERE dyad=? GROUP BY market_id) x
        ON m.market_id=x.market_id AND m.fetched_at=x.f WHERE m.dyad=?
        ORDER BY m.volume DESC""", (dyad, dyad)).fetchall()

def save_profile(c, iso, payload):
    c.execute("INSERT OR REPLACE INTO profiles(iso,fetched_at,payload) VALUES (?,?,?)",
              (iso, now(), json.dumps(payload, ensure_ascii=False)))

def get_profile(c, iso):
    r = c.execute("SELECT payload, fetched_at FROM profiles WHERE iso=?", (iso,)).fetchone()
    return (json.loads(r["payload"]), r["fetched_at"]) if r else (None, None)
