"""Profil pays : Banque mondiale (démographie, ressources, techno, défense) + Wikidata (régime)."""
import httpx

WB = "https://api.worldbank.org/v2/country/{isos}/indicator/{code}"

INDICATORS = {
    # démographie
    "population": "SP.POP.TOTL",
    "pop_growth_pct": "SP.POP.GROW",
    "fertility": "SP.DYN.TFRT.IN",
    "age65_pct": "SP.POP.65UP.TO.ZS",
    # économie
    "gdp_usd": "NY.GDP.MKTP.CD",
    "gdp_per_capita_usd": "NY.GDP.PCAP.CD",
    # ressources (rentes en % du PIB = dépendance aux ressources)
    "resource_rents_pct_gdp": "NY.GDP.TOTL.RT.ZS",
    "oil_rents_pct_gdp": "NY.GDP.PETR.RT.ZS",
    "gas_rents_pct_gdp": "NY.GDP.NGAS.RT.ZS",
    "mineral_rents_pct_gdp": "NY.GDP.MINR.RT.ZS",
    "arable_land_pct": "AG.LND.ARBL.ZS",
    "freshwater_m3_per_capita": "ER.H2O.INTR.PC",
    # technologie
    "rd_pct_gdp": "GB.XPD.RSDV.GD.ZS",
    "hightech_exports_pct": "TX.VAL.TECH.MF.ZS",
    "internet_users_pct": "IT.NET.USER.ZS",
    # défense
    "military_pct_gdp": "MS.MIL.XPND.GD.ZS",
}

def _wb_series(isos, code):
    r = httpx.get(WB.format(isos=";".join(isos), code=code), timeout=60,
                  params={"format": "json", "date": "2005:2026", "per_page": 5000})
    r.raise_for_status()
    body = r.json()
    rows = body[1] if len(body) > 1 and body[1] else []
    out = {}
    for row in rows:
        if row["value"] is None:
            continue
        iso = row["country"]["id"]  # ISO2
        out.setdefault(iso, {})[int(row["date"])] = row["value"]
    return out  # {iso: {year: value}}

def _latest(series):
    if not series:
        return None
    y = max(series)
    return {"value": series[y], "year": y}

def _pop_trend(pop, fert):
    """Tendance factuelle : taux annuel moyen sur 10 ans + fécondité vs seuil de remplacement."""
    if not pop or len(pop) < 2:
        return None
    y1 = max(pop); y0 = max(min(pop), y1 - 10)
    if y0 not in pop:
        y0 = min(k for k in pop if k >= y0)
    cagr = (pop[y1] / pop[y0]) ** (1 / max(y1 - y0, 1)) - 1
    label = "croissance" if cagr > 0.005 else "déclin" if cagr < -0.001 else "stagnation"
    f = _latest(fert)
    return {
        "annual_rate_pct": round(cagr * 100, 2), "period": f"{y0}-{y1}", "label": label,
        "below_replacement": bool(f and f["value"] < 2.1),  # 2,1 = seuil de renouvellement
    }

def _government(iso):
    q = f"""SELECT ?govLabel ?headLabel WHERE {{
      ?c wdt:P297 "{iso}" .
      OPTIONAL {{ ?c wdt:P122 ?gov }}
      OPTIONAL {{ ?c wdt:P35 ?head }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "fr,en". }} }}"""
    r = httpx.get("https://query.wikidata.org/sparql", params={"query": q, "format": "json"},
                  headers={"User-Agent": "geowatch/0.1 (open-source research tool)"}, timeout=60)
    r.raise_for_status()
    b = r.json()["results"]["bindings"]
    return {
        "forms": sorted({x["govLabel"]["value"] for x in b if "govLabel" in x}),
        "head_of_state": sorted({x["headLabel"]["value"] for x in b if "headLabel" in x}),
    }

def fetch(isos):
    """{iso: profil}. Un appel Banque mondiale par indicateur, tous pays groupés."""
    series = {}
    for key, code in INDICATORS.items():
        try:
            series[key] = _wb_series(isos, code)
        except httpx.HTTPError as e:
            print(f"  [worldbank] {code} → {e}")
            series[key] = {}

    profiles = {}
    for iso in isos:
        p = {k: _latest(series[k].get(iso)) for k in INDICATORS}
        p["population_trend"] = _pop_trend(series["population"].get(iso),
                                           series["fertility"].get(iso))
        try:
            p["government"] = _government(iso)
        except httpx.HTTPError as e:
            print(f"  [wikidata] {iso} → {e}")
            p["government"] = None
        p["sources"] = ["Banque mondiale WDI", "Wikidata (P122 forme de gouvernement, P35 chef d'État)"]
        profiles[iso] = p
    return profiles
