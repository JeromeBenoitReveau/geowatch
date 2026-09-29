"""
python ingest.py  # profils pays, votes à l'ONU, coordonnées et photos → data/ (GitHub Actions, le 1er du mois)
"""
from dotenv import load_dotenv; load_dotenv()
import db, network
from sources import profiles, unga

def run_profiles(c):
    actors, _ = network.load()
    isos = {a for a, v in actors.items() if v["kind"] == "state"}
    isos |= {v["base"] for v in actors.values() if v.get("base")}  # pays hôtes des proxies
    isos |= {a for a, v in actors.items() if v["kind"] == "bloc" and a in profiles.WB_CODES}
    print(f"→ profils : {', '.join(sorted(isos))}")
    for iso, p in profiles.fetch(sorted(isos)).items():
        db.save_profile(c, iso, p)
    c.commit()
    # votes à l'ONU (Voeten) : téléchargés seulement si une nouvelle version est publiée
    known = db.load_unga()
    u = unga.fetch(known.get("source", {}).get("version") if "by_year" in known else None)
    if u:
        db.save_unga(u)
        print(f"→ votes ONU : version {u['source']['version']}, accord {u['agreement_year']}, {len(u['countries'])} pays")
    # carte : coordonnées de tous les pays (acteurs, alignments.yaml, membres de l'ONU)
    every = {i for i in isos if i not in profiles.WB_CODES} | set(network.formal_ties(network.alignments()))
    g = profiles.geo(every)
    g.update({k: v for k, v in profiles.geo(set(db.load_unga().get("countries", {})), prop="P298").items() if k not in g})
    db.save_geo(g)
    # photos : personnes du graphe (clé = id) et dirigeants décrits dans un champ leader (clé = « leader:<id> »)
    qids = {a: v["wikidata"] for a, v in actors.items() if v.get("wikidata")}
    qids |= {f"leader:{a}": v["leader"]["wikidata"] for a, v in actors.items()
             if isinstance(v.get("leader"), dict) and v["leader"].get("wikidata")}
    db.save_people(profiles.people(qids))

if __name__ == "__main__":
    c = db.conn()
    run_profiles(c)
