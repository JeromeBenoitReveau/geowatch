"""
python ingest.py  # profils pays, votes à l'ONU, coordonnées et photos → data/ (GitHub Actions, le 1er du mois)
"""
from dotenv import load_dotenv; load_dotenv()
import db, network
from sources import profiles, unga

def run_profiles(c):
    actors, _ = network.load()
    isos = {a for a, v in actors.items() if v["kind"] == "state" and len(a) == 2}  # sans les territoires sans code pays
    isos |= {v["base"] for v in actors.values() if v.get("base")}  # pays hôtes des proxies
    isos |= {a for a, v in actors.items() if v["kind"] == "bloc" and a in profiles.WB_CODES}
    isos |= network.org_countries(network.alignments())  # membres des organisations (tailles de la vue Organisations)
    print(f"→ profils : {', '.join(sorted(isos))}")
    for iso, p in profiles.fetch(sorted(isos)).items():
        db.save_profile(c, iso, p)
    c.commit()
    # votes à l'ONU (Voeten) : téléchargés seulement si une nouvelle version est publiée
    known = db.load_unga()
    # accord deux à deux pour les États du graphe (page « Croiser ») : retéléchargé aussi si un État du graphe y manque
    g0 = db.load_geo()
    pair_isos = {g0[a]["iso3"] for a, v in actors.items() if v["kind"] == "state" and g0.get(a, {}).get("iso3")}
    fresh = "by_year" in known and pair_isos <= set(known.get("pair_isos", []))
    u = unga.fetch(known.get("source", {}).get("version") if fresh else None, pair_isos)
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
    # personnes citées dans les dossiers (registre people de dossiers.yaml), hors acteurs du graphe : clé « p:<id> »
    import dossier
    qids |= {f"p:{k}": v["wikidata"] for k, v in dossier.registry().items() if v.get("wikidata") and not v.get("actor")}
    db.save_people(profiles.people(qids))
    photos()

def photos():
    """Télécharge les vignettes de data/people.json dans data/photos/ (servies par le site lui-même)."""
    import json, httpx
    db.PHOTOS.mkdir(exist_ok=True)
    for k, v in json.loads(db.PEOPLE.read_text(encoding="utf-8")).items():
        f = db.photo_file(k, v.get("thumb", ""))
        if v.get("thumb") and not f.exists():
            r = httpx.get(v["thumb"], headers={"User-Agent": "geowatch/0.1 (open-source research tool)"}, timeout=60, follow_redirects=True)
            if r.status_code == 200:
                f.write_bytes(r.content)
            else:
                print(f"  [photos] {k} : HTTP {r.status_code}")

if __name__ == "__main__":
    c = db.conn()
    run_profiles(c)
