"""Historique des cotes, en CSV versionné dans le dépôt (data/) : GitHub Actions l'alimente
toutes les 6 h et il est publiable tel quel. Deux fichiers pour éviter de répéter les questions :
  markets.csv : source, market_id, dyad, question, url   (une ligne par marché, mise à jour)
  odds.csv    : fetched_at, source, market_id, prob, volume   (une ligne par relevé, en ajout)
"""
import csv, os
from pathlib import Path

DATA = Path(os.getenv("DATA_DIR", Path(__file__).with_name("data")))
MARKET_COLS = ["source", "market_id", "dyad", "question", "url"]
ODDS_COLS = ["fetched_at", "source", "market_id", "prob", "volume"]

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
                                         "question": m["question"], "url": m["url"]}
    with open(DATA / "markets.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, MARKET_COLS)
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
