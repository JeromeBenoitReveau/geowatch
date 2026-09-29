"""python validate.py  → vérifie network.yaml. Code de sortie 1 s'il y a des erreurs.
Tourne aussi en CI (.github/workflows/validate.yml) sur chaque changement du graphe."""
import re, sys
from datetime import date
import network
from config import DYADS

KINDS = {"state", "non_state", "bloc", "party", "person"}
TYPES = {"arms", "financial", "training", "troops", "intelligence", "political", "economic", "dual_use"}
STATUSES = {"active", "reduced", "ended", "alleged"}
CONFIDENCES = {"high", "medium", "low"}
STALE_MONTHS = 6

def months_since(ym, today=None):
    t = today or date.today()
    y, m = map(int, ym.split("-"))
    return (t.year - y) * 12 + t.month - m

def check(actors, edges, today=None, aligns=None):
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
        if a.get("kind") in ("party", "person") and not re.fullmatch(r"[A-Z]{2}", str(a.get("base", ""))):
            errors.append(f"acteur {aid} : un parti ou une personne doit avoir une base ISO2 (pays d'ancrage)")
        if a.get("wikidata") is not None and not re.fullmatch(r"Q\d+", str(a["wikidata"])):
            errors.append(f"acteur {aid} : wikidata doit être un identifiant Qxxx")
        c = a.get("coords")
        if c is not None and not (isinstance(c, list) and len(c) == 2
                                  and all(isinstance(x, (int, float)) for x in c)
                                  and -90 <= c[0] <= 90 and -180 <= c[1] <= 180):
            errors.append(f"acteur {aid} : coords doit être [lat, lon]")
        if a.get("kind") == "bloc" and c is None:
            warnings.append(f"acteur {aid} : bloc sans coords, absent de la carte")
        for bloc in a.get("member_of") or []:
            if actors.get(bloc, {}).get("kind") != "bloc":
                errors.append(f"acteur {aid} : member_of « {bloc} » n'est pas un bloc de actors")
        if a.get("note") and a.get("kind") in ("party", "person") and a["note"] and "sources" in a \
                and not all(isinstance(x, str) and "http" in x for x in a["sources"]):
            warnings.append(f"acteur {aid} : source de la note sans URL")

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
        dates = {}
        for k in ("since", "until"):
            if e.get(k) is not None:
                d = str(e[k])
                if not re.fullmatch(r"\d{4}(-\d{2})?", d):
                    errors.append(f"{where} : {k} « {d} » doit être au format AAAA ou AAAA-MM")
                dates[k] = d
        if "since" not in dates:
            warnings.append(f"{where} : pas de date de début (since)")
        if len(dates) == 2 and dates["until"] < dates["since"]:
            errors.append(f"{where} : until antérieur à since")
        if e.get("status") == "ended" and "until" not in dates:
            warnings.append(f"{where} : relation terminée sans date de fin (until)")
        v = str(e.get("verified", ""))
        if not re.fullmatch(r"\d{4}-\d{2}", v):
            errors.append(f"{where} : verified « {v} » doit être au format AAAA-MM")
        elif months_since(v, today) > STALE_MONTHS:
            warnings.append(f"{where} : vérifiée en {v}, à revoir (> {STALE_MONTHS} mois)")

    ids = set()
    for g in (aligns or {}).get("groups", []):
        k = g.get("id")
        if k in ids:
            errors.append(f"groupe {k} : id en double")
        ids.add(k)
        if g.get("kind") == "forum":
            if g.get("bloc") is not None or g.get("level") != 0:
                errors.append(f"groupe {k} : un forum n'a ni bloc ni niveau (level: 0)")
        elif g.get("bloc") not in (aligns.get("blocs") or {}):
            errors.append(f"groupe {k} : bloc « {g.get('bloc')} » absent de blocs")
        if g.get("level") not in (0, 1, 2, 3):
            errors.append(f"groupe {k} : level doit valoir 0, 1, 2 ou 3")
        if g.get("entity") and g["entity"] not in actors:
            errors.append(f"groupe {k} : entity « {g['entity']} » absente de actors")
        srcs = g.get("sources") or []
        if not srcs or not all(isinstance(x, str) and "http" in x for x in srcs):
            errors.append(f"groupe {k} : sources avec URL requises")
        members = set(g.get("members") or [])
        for m in members:
            if not re.fullmatch(r"[A-Z]{2}", str(m)):
                errors.append(f"groupe {k} : membre « {m} » n'est pas un code ISO2")
        # dates d'adhésion / de départ : AAAA-MM ; joined pour un membre actuel, left pour un ancien membre
        if g.get("since") is not None and not re.fullmatch(r"\d{4}-\d{2}", str(g["since"])):
            errors.append(f"groupe {k} : since « {g['since']} » doit être au format AAAA-MM")
        for field, must_be_member in (("joined", True), ("left", False)):
            for m, d in (g.get(field) or {}).items():
                if not re.fullmatch(r"\d{4}-\d{2}", str(d)):
                    errors.append(f"groupe {k} : {field}[{m}] « {d} » doit être au format AAAA-MM")
                if (m in members) != must_be_member:
                    errors.append(f"groupe {k} : {field}[{m}] — " + ("absent de members" if must_be_member
                                  else "un ancien membre ne doit plus figurer dans members"))
    for b, v in ((aligns or {}).get("blocs") or {}).items():
        if not re.fullmatch(r"#[0-9a-fA-F]{6}", str(v.get("color", ""))):
            errors.append(f"bloc {b} : color doit être #rrggbb")

    for name, d in DYADS.items():
        for aid in d["countries"]:
            if aid not in actors:
                errors.append(f"config.DYADS[{name}] : {aid} absent de actors")
    return errors, warnings

if __name__ == "__main__":
    actors, edges = network.load()
    errors, warnings = check(actors, edges, aligns=network.alignments())
    for w in warnings:
        print(f"⚠️  {w}")
    for e in errors:
        print(f"❌ {e}")
    print(f"\n{len(actors)} acteurs, {len(edges)} arêtes — {len(errors)} erreur(s), {len(warnings)} avertissement(s)")
    sys.exit(1 if errors else 0)
