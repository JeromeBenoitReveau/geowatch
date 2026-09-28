"""python track.py [paire]  → cotes actuelles, variation sur 7 j, mouvements notables.
Les cotes sont les seules probabilités affichées par geowatch : elles viennent des marchés, pas de nous."""
from dotenv import load_dotenv; load_dotenv()
import sys
from datetime import datetime, timedelta, timezone
import history
from config import DYADS, MOVE_ALERT_PTS

def _ago(days):
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat(timespec="seconds")

def summary(dyad, days=7, history_days=90):
    """Un marché par entrée, du plus liquide au moins liquide. delta_pts = None si pas encore
    de relevé vieux de `days` jours. stale = absent du dernier relevé (clos ou plus trouvé)."""
    by = {}
    for r in history.rows(dyad):
        m = by.setdefault(r["market_id"], {"id": r["market_id"], "source": r["source"], "history": []})
        m.update(question=r["question"], url=r["url"], volume=r["volume"])
        m["history"].append((r["fetched_at"], r["prob"]))
    if not by:
        return []
    last_run = max(m["history"][-1][0] for m in by.values())
    cutoff, since = _ago(days), _ago(history_days)
    out = []
    for m in by.values():
        h = m.pop("history")
        past = [p for t, p in h if t <= cutoff]
        daily = {t[:10]: p for t, p in h if t >= since}  # dernier relevé de chaque jour
        out.append({**m, "prob": h[-1][1], "last_seen": h[-1][0],
                    "delta_pts": round((h[-1][1] - past[-1]) * 100, 1) if past else None,
                    "stale": h[-1][0][:10] < last_run[:10],
                    "daily": sorted(daily.items())})
    return sorted(out, key=lambda m: (m["stale"], -(m["volume"] or 0)))

HORIZONS = {"1 j": 1, "7 j": 7, "30 j": 30}

def calibration():
    """Marchés résolus : cote relevée 1, 7 et 30 jours avant l'issue, et score de Brier par horizon
    (moyenne de (cote − issue)², 0 = parfait, 0,25 = cote constante de 50 %). Indicatif tant que
    peu de marchés sont résolus. upcoming = marchés suivis encore ouverts, par date de fin."""
    names = {(r["source"], r["market_id"]): r for r in history.markets()}
    res_all = history.resolutions()
    out = []
    for key, res in res_all.items():
        h, end = history.odds_of(*key), res["resolved_at"]
        if not h or not end:
            continue
        at = {}
        for label, d in HORIZONS.items():
            t = (datetime.fromisoformat(end) - timedelta(days=d)).isoformat(timespec="seconds")
            before = [p for ts, p in h if ts <= t]
            at[label] = before[-1] if before else None
        m = names.get(key, {})
        out.append({"source": key[0], "id": key[1], "question": m.get("question"), "url": m.get("url"),
                    "dyad": m.get("dyad"), "resolved_at": end, "outcome": res["outcome"], "odds": at,
                    "last": h[-1][1]})
    brier = {}
    for label in HORIZONS:
        pts = [(x["odds"][label] - x["outcome"]) ** 2 for x in out if x["odds"][label] is not None]
        brier[label] = {"n": len(pts), "score": round(sum(pts) / len(pts), 3) if pts else None}
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    upcoming = sorted(({"question": r["question"], "url": r["url"], "end_date": history.iso(r["end_date"])}
                       for k, r in names.items() if k not in res_all and r.get("end_date")),
                      key=lambda x: x["end_date"])
    return {"markets": sorted(out, key=lambda x: x["resolved_at"], reverse=True), "brier": brier,
            "upcoming": [u for u in upcoming if u["end_date"] >= now][:5],
            "overdue": [u for u in upcoming if u["end_date"] < now]}

def show(dyad):
    ms = summary(dyad)
    print(f"\n══ {dyad} ══")
    if not ms:
        print("  aucun marché relevé → `python ingest.py`")
    for m in ms:
        d = m["delta_pts"]
        delta = "   n/d" if d is None else f"{d:+6.1f}"
        flag = "⚡" if d is not None and abs(d) >= MOVE_ALERT_PTS else " "
        stale = "  (absent du dernier relevé)" if m["stale"] else ""
        print(f"  {m['prob']*100:5.1f} % {delta} pts/7 j {flag} {m['question']} [{m['source']}]{stale}")

if __name__ == "__main__":
    for name in sys.argv[1:] or DYADS:
        if name not in DYADS:
            sys.exit(f"paire inconnue : {name} — parmi {', '.join(DYADS)}")
        show(name)
