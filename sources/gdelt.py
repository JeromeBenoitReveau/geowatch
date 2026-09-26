"""GDELT DOC 2.0 — gratuit, sans clé. Limite ~1 requête / 5 s."""
import time, httpx
from sources import UA

URL = "https://api.gdeltproject.org/api/v2/doc/doc"

def _get(query, mode, days, **extra):
    for wait in (5, 30, 60):
        time.sleep(wait)
        r = httpx.get(URL, timeout=60, headers=UA, params={
            "query": query, "mode": mode, "timespan": f"{days}d", "format": "json", **extra})
        r.raise_for_status()
        if r.text.lstrip().startswith("Please limit requests"):  # limite de débit, en texte brut
            continue
        return r.json() if r.text.strip() else {}
    raise RuntimeError(f"GDELT {mode} : limite de débit toujours atteinte")

def fetch(query, days=7):
    tone = _get(query, "timelinetone", days)       # tonalité moyenne (négatif = hostile)
    volume = _get(query, "timelinevolraw", days)   # nb d'articles / jour
    arts = _get(query, "artlist", days, maxrecords=25, sort="datedesc")
    return [
        ("gdelt/tone", tone.get("timeline", [])),
        ("gdelt/volume", volume.get("timeline", [])),
        ("gdelt/articles", [
            {"title": a.get("title"), "url": a.get("url"), "domain": a.get("domain"),
             "date": a.get("seendate"), "lang": a.get("language")}
            for a in arts.get("articles", [])]),
    ]
