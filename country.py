"""python country.py IR   → fiche pays + réseau de soutiens"""
from dotenv import load_dotenv; load_dotenv()
import sys
import db, network

def fmt(v, unit="", digits=1):
    if not v:
        return "n/d"
    x = v["value"]
    if abs(x) >= 1e9:  s = f"{x/1e9:.{digits}f} Md"
    elif abs(x) >= 1e6: s = f"{x/1e6:.{digits}f} M"
    else: s = f"{x:,.{digits}f}".replace(",", " ")
    return f"{s}{unit} ({v['year']})"

def show(iso):
    actors, edges = network.load()
    c = db.conn()
    p, fetched = db.get_profile(c, iso)
    title = network.name(actors, iso)
    print(f"\n══ {title} ({iso}) ══")

    if p:
        g = p.get("government") or {}
        t = p.get("population_trend") or {}
        print(f"\nRégime       {', '.join(g.get('forms', [])) or 'n/d'}")
        print(f"Chef d'État  {', '.join(g.get('head_of_state', [])) or 'n/d'}")
        if not p["population"]:
            print("\nAucune donnée Banque mondiale pour ce territoire (Taïwan n'y figure pas).")
            print(f"\n(profil du {fetched[:10]} — Wikidata)")
            p = None
    if p:
        print(f"\nPopulation   {fmt(p['population'])}")
        if t:
            flag = " · fécondité sous le seuil de renouvellement" if t["below_replacement"] else ""
            print(f"Tendance     {t['label']} ({t['annual_rate_pct']:+} %/an, {t['period']}){flag}")
        print(f"Fécondité    {fmt(p['fertility'], digits=2)}   65 ans+ {fmt(p['age65_pct'], ' %')}")
        print(f"\nPIB          {fmt(p['gdp_usd'], ' $')}   /hab {fmt(p['gdp_per_capita_usd'], ' $', 0)}")
        print(f"Rentes ress. {fmt(p['resource_rents_pct_gdp'], ' % PIB')}  "
              f"(pétrole {fmt(p['oil_rents_pct_gdp'], ' %')}, gaz {fmt(p['gas_rents_pct_gdp'], ' %')}, "
              f"minerais {fmt(p['mineral_rents_pct_gdp'], ' %')})")
        print(f"Terres arables {fmt(p['arable_land_pct'], ' %')}   Eau douce {fmt(p['freshwater_m3_per_capita'], ' m³/hab', 0)}")
        print(f"\nR&D          {fmt(p['rd_pct_gdp'], ' % PIB', 2)}   Export high-tech {fmt(p['hightech_exports_pct'], ' %')}")
        print(f"Internet     {fmt(p['internet_users_pct'], ' %')}   Défense {fmt(p['military_pct_gdp'], ' % PIB')}")
        print(f"\n(profil du {fetched[:10]} — {', '.join(p['sources'])})")
    elif not fetched:
        print("\nPas de profil en base → `python ingest.py --profiles`")

    def line(e, other):
        extra = f" — {e['note']}" if e.get("note") else ""
        return (f"  {network.name(actors, other):<28} {', '.join(e['types']):<30} "
                f"[{e['status']}, {e['confidence']}]{extra}")

    sup_by = network.supported_by(iso, edges)
    sup_of = network.supporters_of(iso, edges)
    proxies = network.proxies_in(iso, actors)
    if sup_by:
        print("\n▶ Soutient"); [print(line(e, e["to"])) for e in sup_by]
    if sup_of:
        print("\n◀ Soutenu par"); [print(line(e, e["from"])) for e in sup_of]
    if proxies:
        print("\n◆ Acteurs non étatiques basés ici")
        for a in proxies:
            print(f"  {network.name(actors, a)} ← " + ", ".join(
                network.name(actors, e["from"]) for e in network.supporters_of(a, edges)))
    if not (sup_by or sup_of or proxies):
        print("\n(aucune relation dans network.yaml)")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage : python country.py <ISO2 ou id acteur>, ex. IR, houthis")
    show(sys.argv[1] if sys.argv[1].islower() else sys.argv[1].upper())
