"""python validate.py  → vérifie network.yaml. Code de sortie 1 s'il y a des erreurs.
Tourne aussi en CI (.github/workflows/validate.yml) sur chaque changement du graphe."""
import re, sys
from datetime import date
import network
from config import DYADS

KINDS = {"state", "non_state", "bloc"}
TYPES = {"arms", "financial", "training", "troops", "intelligence", "political", "economic", "dual_use"}
STATUSES = {"active", "reduced", "ended", "alleged"}
CONFIDENCES = {"high", "medium", "low"}
STALE_MONTHS = 6

def months_since(ym, today=None):
    t = today or date.today()
    y, m = map(int, ym.split("-"))
    return (t.year - y) * 12 + t.month - m

def check(actors, edges, today=None):
    errors, warnings = [], []
    for aid, a in actors.items():
        if not a.get("name"):
            errors.append(f"acteur {aid} : name manquant")
        if a.get("kind") not in KINDS:
            errors.append(f"acteur {aid} : kind « {a.get('kind')} » invalide ({', '.join(sorted(KINDS))})")
        if a.get("kind") == "state" and not re.fullmatch(r"[A-Z]{2}", aid):
            errors.append(f"acteur {aid} : un État doit avoir un id ISO2 en majuscules")
        if a.get("kind") == "non_state" and not re.fullmatch(r"[A-Z]{2}", str(a.get("base", ""))):
            warnings.append(f"acteur {aid} : non étatique sans base ISO2 (pas de fiche pays hôte)")

    seen = set()
    for i, e in enumerate(edges, 1):
        where = f"arête {i} ({e.get('from')} → {e.get('to')})"
        for end in ("from", "to"):
            if e.get(end) not in actors:
                errors.append(f"{where} : {end} « {e.get(end)} » absent de actors")
        if e.get("from") == e.get("to"):
            errors.append(f"{where} : un acteur ne peut pas se soutenir lui-même")
        if (e.get("from"), e.get("to")) in seen:
            errors.append(f"{where} : doublon — fusionner les types dans une seule arête")
        seen.add((e.get("from"), e.get("to")))
        types = e.get("types") or []
        if not types or not set(types) <= TYPES:
            errors.append(f"{where} : types {types} invalides ({', '.join(sorted(TYPES))})")
        if e.get("status") not in STATUSES:
            errors.append(f"{where} : status « {e.get('status')} » invalide")
        if e.get("confidence") not in CONFIDENCES:
            errors.append(f"{where} : confidence « {e.get('confidence')} » invalide")
        sources = e.get("sources") or []
        if not sources or not all(isinstance(s, str) and s.strip() for s in sources):
            errors.append(f"{where} : au moins une source requise")
        elif not any("http" in s for s in sources):
            warnings.append(f"{where} : aucune source avec URL")
        v = str(e.get("verified", ""))
        if not re.fullmatch(r"\d{4}-\d{2}", v):
            errors.append(f"{where} : verified « {v} » doit être au format AAAA-MM")
        elif months_since(v, today) > STALE_MONTHS:
            warnings.append(f"{where} : vérifiée en {v}, à revoir (> {STALE_MONTHS} mois)")

    for name, d in DYADS.items():
        for aid in d["countries"]:
            if aid not in actors:
                errors.append(f"config.DYADS[{name}] : {aid} absent de actors")
    return errors, warnings

if __name__ == "__main__":
    actors, edges = network.load()
    errors, warnings = check(actors, edges)
    for w in warnings:
        print(f"⚠️  {w}")
    for e in errors:
        print(f"❌ {e}")
    print(f"\n{len(actors)} acteurs, {len(edges)} arêtes — {len(errors)} erreur(s), {len(warnings)} avertissement(s)")
    sys.exit(1 if errors else 0)
