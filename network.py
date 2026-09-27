"""Lecture/requêtes du graphe network.yaml."""
from pathlib import Path
import yaml

PATH = Path(__file__).with_name("network.yaml")

def load():
    data = yaml.safe_load(PATH.read_text(encoding="utf-8"))
    return data["actors"], data["edges"]

def name(actors, aid):
    return actors.get(aid, {}).get("name", aid)

def supporters_of(aid, edges):
    return [e for e in edges if e["to"] == aid and e["status"] != "ended"]

def supported_by(aid, edges):
    return [e for e in edges if e["from"] == aid and e["status"] != "ended"]

def proxies_in(country_iso, actors):
    """Acteurs non étatiques basés dans un pays (ex. YE → houthis)."""
    return [a for a, v in actors.items() if v.get("base") == country_iso and v["kind"] == "non_state"]

def based_in(country_iso, actors, kinds=("party", "person")):
    """Partis et personnalités rattachés à un pays (ex. DE → afd)."""
    return [a for a, v in actors.items() if v.get("base") == country_iso and v["kind"] in kinds]

def members_of(bloc, actors):
    return [a for a, v in actors.items() if bloc in (v.get("member_of") or [])]

def subgraph(ids, edges, hops=1):
    """Arêtes autour d'un ensemble d'acteurs, sur n sauts."""
    nodes, out = set(ids), []
    for _ in range(hops):
        new = [e for e in edges if e["from"] in nodes or e["to"] in nodes]
        for e in new:
            nodes |= {e["from"], e["to"]}
        out = new
    return out
