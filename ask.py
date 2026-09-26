"""python ask.py "Quelle probabilité qu'Israël attaque l'Iran ?" [--dyad israel-iran]"""
from dotenv import load_dotenv; load_dotenv()
import argparse, json, os, sys
import anthropic
import db, network
from config import DYADS, LOOKBACK_DAYS

MAX_PAYLOAD_CHARS = 6000  # par signal, pour tenir dans le contexte

SYSTEM = """Tu es un analyste géopolitique. Tu réponds en français, de façon sourcée et sobre.

Règles non négociables :
1. Un pourcentage n'apparaît QUE s'il provient d'un marché de prédiction fourni (cite source, question exacte, date). Jamais de % inventé ou "estimé".
2. Si aucun marché ne couvre la question, dis-le, et donne un niveau de tension qualitatif (faible / modéré / élevé / critique) justifié par les signaux mesurables fournis (tonalité média, volume, événements de conflit, indices d'instabilité).
3. Explique les moteurs sur 4 axes, uniquement s'ils sont étayés par les données ou par un contexte historique solide que tu signales comme tel : politique/sécuritaire, commercial, territoire & ressources, climat.
4. Utilise country_profiles (ressources, démographie, techno, régime) et support_network (alliés, proxies) pour expliquer les rapports de force ; cite l'année des données.
5. Distingue clairement : ce que disent les données / ce qui relève du contexte général / ce qui est incertain.
6. Si un marché ne correspond pas exactement à la question (horizon, formulation), signale l'écart.

Format : réponse directe (2-3 phrases) → cotes de marché pertinentes → signaux → moteurs → limites."""

def detect_dyad(question):
    q = question.lower()
    scores = {n: sum(a in q for a in d["aliases"]) for n, d in DYADS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] >= 2 else None

def build_context(c, dyad):
    mkts = [dict(r) for r in db.latest_markets(c, dyad)]
    sigs, seen = [], set()
    for r in db.recent_signals(c, dyad, LOOKBACK_DAYS):
        if r["kind"] in seen:        # garde le plus récent par type
            continue
        seen.add(r["kind"])
        sigs.append({"source": r["source"], "kind": r["kind"], "fetched_at": r["fetched_at"],
                     "data": r["payload"][:MAX_PAYLOAD_CHARS]})
    actors, edges = network.load()
    isos = DYADS[dyad]["countries"]
    profiles = {iso: db.get_profile(c, iso)[0] for iso in isos}
    return {"dyad": dyad, "markets": mkts, "signals": sigs,
            "country_profiles": profiles,
            "support_network": {"actors": actors, "edges": network.subgraph(isos, edges, hops=2)}}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("question")
    p.add_argument("--dyad", choices=DYADS.keys())
    a = p.parse_args()

    dyad = a.dyad or detect_dyad(a.question)
    if not dyad:
        sys.exit(f"Dyade non reconnue. Précise --dyad parmi : {', '.join(DYADS)}")

    ctx = build_context(db.conn(), dyad)
    if not ctx["signals"] and not ctx["markets"]:
        sys.exit("Aucune donnée en base — lance d'abord `python ingest.py`.")

    client = anthropic.Anthropic()
    msg = client.messages.create(
        model=os.getenv("CLAUDE_MODEL", "claude-sonnet-5"),
        max_tokens=2000,
        system=SYSTEM,
        messages=[{"role": "user", "content":
            f"Question : {a.question}\n\nDonnées collectées :\n"
            f"{json.dumps(ctx, ensure_ascii=False, indent=1)}"}],
    )
    print("".join(b.text for b in msg.content if b.type == "text"))

if __name__ == "__main__":
    main()
