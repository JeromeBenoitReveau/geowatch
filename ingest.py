"""
python ingest.py             # signaux + marchés (cron toutes les 6 h)
python ingest.py --profiles  # profils pays (cron hebdo — données annuelles)
"""
from dotenv import load_dotenv; load_dotenv()
import argparse, os
import db, network, tension
from config import DYADS, LOOKBACK_DAYS, UCDP_LOOKBACK_DAYS
from sources import ucdp, gdelt, markets, profiles

def run_signals(c):
    if not os.getenv("UCDP_TOKEN"):
        print("[ucdp] UCDP_TOKEN absent → violence non collectée (voir README)")
    for name, d in DYADS.items():
        print(f"→ {name}")
        if os.getenv("UCDP_TOKEN"):
            try:
                for kind, payload in ucdp.fetch(d["ucdp_gw"], d["keywords"], UCDP_LOOKBACK_DAYS):
                    db.save_signal(c, name, "ucdp", kind, payload)
            except Exception as e:
                print(f"  [ucdp] → {e}")
        try:
            for kind, payload in gdelt.fetch(d["gdelt_query"], LOOKBACK_DAYS):
                db.save_signal(c, name, "gdelt", kind, payload)
        except Exception as e:
            print(f"  [gdelt] → {e}")
        found = markets.fetch(d["keywords"])
        for m in found:
            db.save_market(c, name, m)
        c.commit()
        print(f"  {len(found)} marché(s) · tension : {tension.compute(c, name)['level'] or 'n/d'}")

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
