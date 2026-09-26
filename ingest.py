"""
python ingest.py             # signaux + marchés (cron toutes les 6 h)
python ingest.py --profiles  # profils pays (cron hebdo — données annuelles)
"""
from dotenv import load_dotenv; load_dotenv()
import argparse
import db, network
from config import DYADS, WM_ENDPOINTS, LOOKBACK_DAYS
from sources import worldmonitor, gdelt, markets, profiles

def run_signals(c):
    for name, d in DYADS.items():
        print(f"→ {name}")
        for iso in d["countries"]:
            for kind, payload in worldmonitor.fetch_country(WM_ENDPOINTS, iso):
                db.save_signal(c, name, "worldmonitor", kind, payload)
        try:
            for kind, payload in gdelt.fetch(d["gdelt_query"], LOOKBACK_DAYS):
                db.save_signal(c, name, "gdelt", kind, payload)
        except Exception as e:
            print(f"  [gdelt] → {e}")
        found = markets.fetch(d["market_keywords"])
        for m in found:
            db.save_market(c, name, m)
        print(f"  {len(found)} marché(s)")
        c.commit()

def run_profiles(c):
    actors, _ = network.load()
    isos = {iso for d in DYADS.values() for iso in d["countries"]}
    isos |= {a for a, v in actors.items() if v["kind"] == "state"}
    isos |= {v["base"] for v in actors.values() if v.get("base")}  # pays hôtes des proxies
    print(f"→ profils : {', '.join(sorted(isos))}")
    for iso, p in profiles.fetch(sorted(isos)).items():
        db.save_profile(c, iso, p)
    c.commit()

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--profiles", action="store_true")
    a = ap.parse_args()
    c = db.conn()
    run_profiles(c) if a.profiles else run_signals(c)
