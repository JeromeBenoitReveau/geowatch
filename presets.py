"""Vues préréglées de l'explorateur (presets.yaml). Un preset qui renvoie à un dossier en tire ses acteurs
(camps du dossier, eux-mêmes lus dans network.yaml) : il ne peut pas contredire les données."""
from pathlib import Path
import yaml
import dossier

FILE = Path(__file__).with_name("presets.yaml")
VIEWS = {"graphe", "carte", "organisations"}
KINDS = {"core", "non_state", "party", "person"}

def load():
    ps = yaml.safe_load(FILE.read_text(encoding="utf-8"))["presets"]
    dos = {x["id"]: x for x in dossier.load()}
    out = []
    for p in ps:
        p = dict(p)
        if p.get("dossier") in dos:
            p["around"] = sorted({a for s in dos[p["dossier"]]["sides"] for a in s["actors"]})
        out.append(p)
    return out
