"""Votes à l'Assemblée générale de l'ONU — jeu de données d'Erik Voeten (Harvard Dataverse, CC0).
- Taux d'accord entre pays (votes enregistrés), dernière année disponible : sert à placer chaque pays
  entre le cœur européen (France, Allemagne) et le cœur de l'axe (Russie, Chine).
- Points idéaux (un seul axe, jusqu'à l'année écoulée) : sert UNIQUEMENT à suivre l'écart de vote
  États-Unis ↔ France/Allemagne. Un axe unique ne sait pas placer un pays entre deux blocs.
Référence : Bailey, Strezhnev & Voeten (2017), Journal of Conflict Resolution 61(2)."""
import csv, io, httpx

API = "https://dataverse.harvard.edu/api"
DOI = "doi:10.7910/DVN/LEJUQZ"
REFS = {"west": ["FRA", "DEU"], "axis": ["RUS", "CHN"]}
H = {"User-Agent": "geowatch/0.1 (open-source research tool)"}

def _meta():
    r = httpx.get(f"{API}/datasets/:persistentId/", params={"persistentId": DOI}, headers=H, timeout=60)
    r.raise_for_status()
    v = r.json()["data"]["latestVersion"]
    return {"version": f'{v["versionNumber"]}.{v["versionMinorNumber"]}', "published": v.get("releaseTime"),
            "files": {f["dataFile"]["filename"]: f["dataFile"]["id"] for f in v["files"]}}

def _latest(files, prefix):
    """Fichier le plus récent (id le plus élevé) dont le nom commence par prefix, au format CSV."""
    ids = [i for name, i in files.items() if name.startswith(prefix) and name.endswith(".csv")]
    if not ids:
        raise RuntimeError(f"UNGA : aucun fichier {prefix}*.csv dans {DOI}")
    return max(ids)

def fetch(prev_version=None):
    """None si la version publiée est déjà connue. Sinon données par pays, indexées en ISO3."""
    m = _meta()
    if m["version"] == prev_version:
        return None
    ip = httpx.get(f"{API}/access/datafile/{_latest(m['files'], 'Idealpointestimates')}", headers=H,
                   timeout=120, follow_redirects=True)
    ip.raise_for_status()
    iso, ideal = {}, {}
    for r in csv.DictReader(io.StringIO(ip.text)):
        iso[r["ccode"]] = r["iso3c"]
        ideal.setdefault(r["iso3c"], {})[int(r["year"])] = float(r["IdealPointFP"])

    targets = {c for group in REFS.values() for c in group} | {"USA"}
    agree = {}  # {année: {pays: {référence: accord}}}
    url = f"{API}/access/datafile/{_latest(m['files'], 'AgreementScores')}?format=original"
    with httpx.stream("GET", url, headers=H, timeout=600, follow_redirects=True) as resp:
        resp.raise_for_status()
        for r in csv.DictReader(resp.iter_lines()):
            a, b = iso.get(r["ccode1"]), iso.get(r["ccode2"])
            if a and b in targets and r["agree"] not in ("", "NA"):
                agree.setdefault(int(r["year"]), {}).setdefault(a, {})[b] = float(r["agree"])
    year = max(agree)

    countries = {}
    for c, d in agree[year].items():
        # un pays de référence n'est comparé qu'aux AUTRES membres de son groupe
        means = {k: [d[x] for x in refs if x != c and x in d] for k, refs in REFS.items()}
        if not all(means.values()):
            continue
        w, x = (sum(v) / len(v) for v in (means["west"], means["axis"]))
        countries[c] = {"west": round(w, 3), "axis": round(x, 3), "usa": round(d["USA"], 3) if "USA" in d else None,
                        "lean": round(w - x, 3)}

    # écart de vote États-Unis ↔ moyenne France/Allemagne sur l'axe unique, pour suivre la dérive transatlantique
    last = max(ideal["USA"])
    drift = []
    for y in range(last - 10, last + 1):
        try:
            eu = (ideal["FRA"][y] + ideal["DEU"][y]) / 2
            drift.append({"year": y, "us_gap": round(abs(ideal["USA"][y] - eu), 2),
                          "fr_de_gap": round(abs(ideal["FRA"][y] - ideal["DEU"][y]), 2)})
        except KeyError:
            continue

    return {"source": {"name": "Voeten, United Nations General Assembly Ideal Points", "doi": DOI,
                       "url": "https://doi.org/10.7910/DVN/LEJUQZ", "license": "CC0 1.0",
                       "version": m["version"], "published": m["published"],
                       "cite": "Bailey, Strezhnev & Voeten (2017), Journal of Conflict Resolution 61(2)"},
            "refs": REFS, "agreement_year": year, "countries": countries, "drift": drift}
