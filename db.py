"""Profils pays, en JSON versionné (data/profiles.json) : GitHub Actions les rafraîchit chaque mois
et le site est construit à partir du dépôt seul. L'historique des cotes est dans history.py."""
import json, os
from datetime import datetime, timezone
from pathlib import Path

PROFILES = Path(os.getenv("DATA_DIR", Path(__file__).with_name("data"))) / "profiles.json"

def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

class Store:
    def __init__(self):
        self.data = json.loads(PROFILES.read_text(encoding="utf-8")) if PROFILES.exists() else {}

    def commit(self):
        PROFILES.parent.mkdir(exist_ok=True)
        PROFILES.write_text(json.dumps(self.data, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
                            encoding="utf-8")

def conn():
    return Store()

def save_profile(c, iso, payload):
    c.data[iso] = {"fetched_at": now(), "profile": payload}

def get_profile(c, iso):
    r = c.data.get(iso)
    return (r["profile"], r["fetched_at"]) if r else (None, None)
