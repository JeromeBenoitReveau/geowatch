"""
python ingest.py             # cotes des marchés (cron toutes les 6 h — c'est l'historique qui compte)
python ingest.py --profiles  # profils pays (cron hebdo — données annuelles)
"""
from dotenv import load_dotenv; load_dotenv()
import argparse
import db, network
from config import DYADS
from sources import markets, profiles

def run_markets(c):
    try:
        kalshi_evs = markets.kalshi_events()
    except markets.httpx.HTTPError as e:
        print(f"[kalshi] → {e}")
        kalshi_evs = []
    for name, d in DYADS.items():
        found = markets.fetch(d["keywords"], kalshi_evs)
        for m in found:
            db.save_market(c, name, m)
        c.commit()
        n_k = sum(m["source"] == "kalshi" for m in found)
        print(f"→ {name} : {len(found) - n_k} Polymarket, {n_k} Kalshi")

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
    run_profiles(c) if a.profiles else run_markets(c)
