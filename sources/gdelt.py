"""GDELT DOC 2.0 — gratuit, sans clé. Limite ~1 requête / 5 s."""
import time, httpx

URL = "https://api.gdeltproject.org/api/v2/doc/doc"

def _get(query, mode, days, **extra):
    time.sleep(5)
    r = httpx.get(URL, timeout=60, params={
        "query": query, "mode": mode, "timespan": f"{days}d", "format": "json", **extra})
    r.raise_for_status()
    return r.json() if r.text.strip() else {}

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
