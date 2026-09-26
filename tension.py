"""Indice de tension qualitatif (faible / modéré / élevé / critique), calculé par règles fixes
à partir de signaux mesurables. Jamais converti en pourcentage.
Méthode et seuils : README § « Indice de tension ». Seuils = heuristiques initiales, à calibrer.

python tension.py            # niveau de chaque dyade à partir de la base
"""
import json
from datetime import datetime, timedelta
import db
from config import DYADS, LOOKBACK_DAYS

LEVELS = ["faible", "modéré", "élevé", "critique"]

# Chaque composante est notée 0-3 : nombre de seuils franchis.
TONE_THRESHOLDS = [2, 4, 6]        # tonalité GDELT 24 h, en valeur absolue négative
SURGE_THRESHOLDS = [1.5, 2.5, 4]   # volume 24 h / moyenne journalière du reste de la fenêtre
DEATHS_THRESHOLDS = [1, 25, 1000]  # morts directs entre les deux pays sur la fenêtre UCDP

def _score(x, thresholds):
    return sum(x >= t for t in thresholds)

def _points(timeline):
    """Timeline GDELT → [(datetime, valeur)], points horaires."""
    data = timeline[0].get("data", []) if timeline else []
    return [(datetime.strptime(p["date"], "%Y%m%dT%H%M%SZ"), float(p["value"])) for p in data]

def media_tone(timeline):
    pts = _points(timeline)
    if not pts:
        return None
    cut = pts[-1][0] - timedelta(hours=24)
    last = [v for d, v in pts if d > cut]
    tone = sum(last) / len(last)
    return {"value": round(tone, 2), "score": _score(-tone, TONE_THRESHOLDS),
            "what": "tonalité médiatique moyenne sur 24 h (GDELT, négatif = hostile)"}

def media_surge(timeline):
    pts = _points(timeline)
    if not pts:
        return None
    cut = pts[-1][0] - timedelta(hours=24)
    last = sum(v for d, v in pts if d > cut)
    before = [v for d, v in pts if d <= cut]
    span_days = (cut - pts[0][0]).total_seconds() / 86400
    if span_days < 2 or not sum(before):
        return None  # pas assez d'historique pour une base de comparaison
    ratio = last / (sum(before) / span_days)
    return {"value": round(ratio, 2), "score": _score(ratio, SURGE_THRESHOLDS),
            "what": "volume d'articles sur 24 h ÷ moyenne journalière des jours précédents (GDELT)"}

def violence(ucdp):
    if not ucdp:
        return None
    deaths = ucdp["direct"]["deaths_best"]
    return {"value": deaths, "score": _score(deaths, DEATHS_THRESHOLDS),
            "what": f"morts dans les affrontements directs entre les deux pays, {ucdp['window_days']} j "
                    f"(UCDP Candidate, dernier événement {ucdp['latest_event'] or 'aucun'})"}

def level(components):
    """Part des points obtenus sur les composantes disponibles, avec plancher sur la violence :
    des morts directs ne peuvent pas coexister avec un niveau « faible »."""
    avail = {k: c for k, c in components.items() if c}
    if not avail:
        return None
    share = sum(c["score"] for c in avail.values()) / (3 * len(avail))
    idx = min(int(share * 4), 3)
    if avail.get("violence"):
        idx = max(idx, {0: 0, 1: 1, 2: 2, 3: 2}[avail["violence"]["score"]])
    return LEVELS[idx]

def compute(c, dyad):
    latest = {}
    for r in db.recent_signals(c, dyad, LOOKBACK_DAYS):
        latest.setdefault(r["kind"], json.loads(r["payload"]))
    components = {
        "media_tone": media_tone(latest.get("gdelt/tone")),
        "media_surge": media_surge(latest.get("gdelt/volume")),
        "violence": violence(latest.get("ucdp/violence")),
    }
    return {"level": level(components), "components": components,
            "missing": [k for k, v in components.items() if not v],
            "method": "règles fixes, voir README § Indice de tension"}

if __name__ == "__main__":
    c = db.conn()
    for name in DYADS:
        t = compute(c, name)
        parts = ", ".join(f"{k}={v['value']}→{v['score']}" for k, v in t["components"].items() if v)
        print(f"{name:<18} {t['level'] or 'n/d':<9} {parts}")
