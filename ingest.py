"""
python ingest.py             # cotes des marchés → data/ (GitHub Actions toutes les 6 h)
python ingest.py --profiles  # profils pays (cron hebdo — données annuelles)
"""
from dotenv import load_dotenv; load_dotenv()
import argparse
import db, history, network
from config import DYADS
from sources import markets, profiles

def run_markets():
    kalshi_evs = markets.kalshi_events()  # gère ses erreurs, garde un scan partiel
    fetched_at, batch = db.now(), []
    for name, d in DYADS.items():
        found = markets.fetch(d["keywords"], kalshi_evs)
        batch += [(name, m) for m in found]
        n_k = sum(m["source"] == "kalshi" for m in found)
        print(f"→ {name} : {len(found) - n_k} Polymarket, {n_k} Kalshi")
    history.record(fetched_at, batch)

def run_profiles(c):
    actors, _ = network.load()
    isos = {iso for d in DYADS.values() for iso in d["countries"]}
    isos |= {a for a, v in actors.items() if v["kind"] == "state"}
    isos |= {v["base"] for v in actors.values() if v.get("base")}  # pays hôtes des proxies
    isos |= {a for a, v in actors.items() if v["kind"] == "bloc" and a in profiles.WB_CODES}
    print(f"→ profils : {', '.join(sorted(isos))}")
    for iso, p in profiles.fetch(sorted(isos)).items():
        db.save_profile(c, iso, p)
    c.commit()

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--profiles", action="store_true")
    a = ap.parse_args()
    run_profiles(db.conn()) if a.profiles else run_markets()
