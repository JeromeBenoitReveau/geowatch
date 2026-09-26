"""UCDP GED Candidate — violence organisée géoréférencée (Uppsala). Gratuit, jeton sur demande.
Publication mensuelle avec ~1 mois de retard : signal de fond, pas du temps réel.
Doc : https://ucdp.uu.se/apidocs/ — quota 5 000 requêtes/jour, erreurs comprises."""
import os, httpx
from collections import Counter
from datetime import date, timedelta
from sources import UA

BASE = "https://ucdpapi.pcr.uu.se/api/gedevents"
_releases = None  # mis en cache pour la durée d'un run

def _get(version, **params):
    r = httpx.get(f"{BASE}/{version}", params=params, timeout=60,
                  headers={**UA, "x-ucdp-access-token": os.environ["UCDP_TOKEN"]})
    r.raise_for_status()
    return r.json()

def releases(n=3):
    """Les n dernières releases mensuelles Candidate (format AA.0.M), la plus récente d'abord.
    UCDP_VERSION (ex. 26.0.8) force une release unique."""
    global _releases
    if os.getenv("UCDP_VERSION"):
        return [os.environ["UCDP_VERSION"]]
    if _releases is None:
        _releases, y, m = [], date.today().year, date.today().month
        for _ in range(n + 4):
            v = f"{y % 100}.0.{m}"
            try:
                if _get(v, pagesize=1).get("TotalCount"):
                    _releases.append(v)
            except httpx.HTTPStatusError as e:
                if e.response.status_code in (401, 403):
                    raise  # jeton invalide : inutile de continuer
            if len(_releases) == n:
                break
            y, m = (y, m - 1) if m > 1 else (y - 1, 12)
        if not _releases:
            raise RuntimeError("aucune release UCDP Candidate trouvée — fixer UCDP_VERSION")
    return _releases

def _events(version, gw, start, max_pages=20):
    out, page = [], 1
    while page <= max_pages:
        d = _get(version, pagesize=1000, page=page, StartDate=start,
                 Country=",".join(map(str, gw)))
        out += d.get("Result", [])
        if page >= d.get("TotalPages", 0):
            break
        page += 1
    return out

def _summary(events):
    by_month = Counter()
    for e in events:
        by_month[e["date_start"][:7]] += e.get("best") or 0
    return {"events": len(events), "deaths_best": sum(e.get("best") or 0 for e in events),
            "deaths_by_month": dict(sorted(by_month.items()))}

def fetch(gw, keywords, days=90):
    """Événements situés dans les pays de la dyade. « direct » = les deux pays figurent
    parmi les belligérants (side_a / side_b) ; le reste est de la violence interne ou autre."""
    start = (date.today() - timedelta(days=days)).isoformat()
    vs, by_id = releases(), {}
    for v in vs:
        for e in _events(v, gw, start):
            by_id[e["id"]] = e
    evs = list(by_id.values())
    kw = [k.lower() for k in keywords]
    direct = [e for e in evs
              if all(k in f"{e.get('side_a') or ''} {e.get('side_b') or ''}".lower() for k in kw)]
    top = sorted(direct, key=lambda e: e.get("best") or 0, reverse=True)[:5]
    return [("ucdp/violence", {
        "releases": vs, "window_start": start, "window_days": days,
        "latest_event": max((e["date_start"] for e in evs), default=None),
        "direct": {**_summary(direct), "top_events": [
            {"date": e["date_start"], "dyad": e.get("dyad_name"), "where": e.get("where_description"),
             "deaths_best": e.get("best")} for e in top]},
        "in_countries": {c: _summary([e for e in evs if e["country"] == c])
                         for c in sorted({e["country"] for e in evs})},
    })]
