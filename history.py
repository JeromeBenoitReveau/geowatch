"""Historique des cotes, en CSV versionné dans le dépôt (data/) : GitHub Actions l'alimente
toutes les 6 h et il est publiable tel quel. Deux fichiers pour éviter de répéter les questions :
  markets.csv : source, market_id, dyad, question, url   (une ligne par marché, mise à jour)
  odds.csv    : fetched_at, source, market_id, prob, volume   (une ligne par relevé, en ajout)
  resolutions.csv : source, market_id, resolved_at, outcome   (1 = Oui, 0 = Non ; une ligne par marché résolu)
"""
import csv, os
from pathlib import Path

DATA = Path(os.getenv("DATA_DIR", Path(__file__).with_name("data")))
MARKET_COLS = ["source", "market_id", "dyad", "question", "url", "end_date"]
ODDS_COLS = ["fetched_at", "source", "market_id", "prob", "volume"]
RESOLUTION_COLS = ["source", "market_id", "resolved_at", "outcome"]

def _read(name):
    p = DATA / name
    if not p.exists():
        return []
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def record(fetched_at, found):
    """found = [(dyad, marché)] d'un même relevé."""
    DATA.mkdir(exist_ok=True)
    known = {(r["source"], r["market_id"]): r for r in _read("markets.csv")}
    for dyad, m in found:
        known[(m["source"], m["id"])] = {"source": m["source"], "market_id": m["id"], "dyad": dyad,
                                         "question": m["question"], "url": m["url"], "end_date": m.get("end_date") or ""}
    with open(DATA / "markets.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, MARKET_COLS, restval="")
        w.writeheader()
        w.writerows(sorted(known.values(), key=lambda r: (r["dyad"], r["source"], r["market_id"])))
    odds = DATA / "odds.csv"
    new = not odds.exists()
    with open(odds, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, ODDS_COLS)
        if new:
            w.writeheader()
        w.writerows({"fetched_at": fetched_at, "source": m["source"], "market_id": m["id"],
                     "prob": round(m["prob"], 4), "volume": round(m.get("volume") or 0)}
                    for _, m in found)

def rows(dyad):
    """Relevés d'une paire, du plus ancien au plus récent, questions jointes."""
    markets = {(r["source"], r["market_id"]): r for r in _read("markets.csv") if r["dyad"] == dyad}
    out = []
    for r in _read("odds.csv"):
        m = markets.get((r["source"], r["market_id"]))
        if m:
            out.append({**m, "fetched_at": r["fetched_at"], "prob": float(r["prob"]),
                        "volume": float(r["volume"] or 0)})
    return sorted(out, key=lambda r: r["fetched_at"])

def iso(ts):
    """Horodatage des API (« 2026-09-28 21:43:54.06+00 », « …Z ») → ISO 8601 UTC comparable à fetched_at."""
    from datetime import datetime, timezone
    t = ts.strip().replace(" ", "T").replace("Z", "+00:00")
    if t.endswith("+00"):
        t += ":00"
    return datetime.fromisoformat(t).astimezone(timezone.utc).isoformat(timespec="seconds")

def markets():
    return _read("markets.csv")

def resolutions():
    """{(source, market_id): {"resolved_at", "outcome"}}"""
    return {(r["source"], r["market_id"]): {"resolved_at": r["resolved_at"], "outcome": int(r["outcome"])}
            for r in _read("resolutions.csv")}

def record_resolutions(new):
    """new = [(source, market_id, resolved_at, outcome)], ajoutés à resolutions.csv."""
    if not new:
        return
    path = DATA / "resolutions.csv"
    fresh = not path.exists()
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, RESOLUTION_COLS)
        if fresh:
            w.writeheader()
        w.writerows({"source": s, "market_id": i, "resolved_at": iso(t), "outcome": o} for s, i, t, o in new)

def odds_of(source, market_id):
    """[(fetched_at, prob)] d'un marché, du plus ancien au plus récent."""
    return sorted((r["fetched_at"], float(r["prob"])) for r in _read("odds.csv")
                  if r["source"] == source and r["market_id"] == market_id)
