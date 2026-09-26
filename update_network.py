"""
python update_network.py IR
Claude + recherche web propose des arêtes nouvelles/modifiées autour d'un acteur
→ network.pending.yaml. Tu relis, tu reportes à la main dans network.yaml.
"""
from dotenv import load_dotenv; load_dotenv()
import os, sys, yaml
import anthropic
import network

PROMPT = """Voici les relations de soutien connues autour de l'acteur « {name} » ({aid}) :

{known}

Avec la recherche web, vérifie leur état actuel et identifie les relations de soutien importantes
manquantes (États ET acteurs non étatiques), dans les deux sens.

Réponds UNIQUEMENT en YAML valide, sans ```:
changes:
  - action: add | update | end
    from: <id>        # ISO2 pour un État, snake_case pour un acteur non étatique
    to: <id>
    types: [arms | financial | training | troops | intelligence | political | economic | dual_use]
    status: active | reduced | ended | alleged
    confidence: high | medium | low
    sources: ["<titre + URL réelle trouvée>"]
    note: "<1 phrase, ce qui a changé>"
new_actors:
  <id>: {{name: ..., kind: state | non_state | bloc, base: <ISO2 si non étatique>}}

Règles : uniquement des faits sourcés par tes recherches ; « alleged » + low si seulement des
allégations ; pas de doublon des relations inchangées."""

def main(aid):
    actors, edges = network.load()
    known = yaml.safe_dump(network.subgraph([aid], edges), allow_unicode=True, sort_keys=False)
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model=os.getenv("CLAUDE_MODEL", "claude-sonnet-5"),
        max_tokens=4000,
        tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 8}],
        messages=[{"role": "user", "content": PROMPT.format(
            name=network.name(actors, aid), aid=aid, known=known or "(aucune)")}],
    )
    text = "".join(b.text for b in msg.content if b.type == "text").strip()
    text = text.removeprefix("```yaml").removeprefix("```").removesuffix("```").strip()
    try:
        yaml.safe_load(text)
    except yaml.YAMLError as e:
        print(f"⚠️ YAML invalide ({e}) — sauvegardé brut quand même.")
    with open("network.pending.yaml", "a", encoding="utf-8") as f:
        f.write(f"\n# ===== {aid} =====\n{text}\n")
    print(text)
    print("\n→ ajouté à network.pending.yaml, à relire avant report dans network.yaml")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage : python update_network.py <id acteur>")
    main(sys.argv[1])
