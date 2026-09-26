# geowatch

Q&A géopolitique sourcé. Agrège World Monitor (événements, instabilité), GDELT (tonalité/volume médiatique) et marchés de prédiction (Polymarket, Kalshi), puis répond via Claude — **aucun pourcentage sans cote de marché réelle derrière**.

## Setup
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # clés World Monitor + Anthropic
```

## Avant le premier run
Vérifier les noms d'endpoints World Monitor dans `config.py → WM_ENDPOINTS` contre
https://worldmonitor.app/openapi.yaml (ou `npx worldmonitor tools`).

## Usage
```bash
python ingest.py                                   # à mettre en cron, ex. toutes les 6 h
python ask.py "Quelle probabilité qu'Israël attaque l'Iran ?"
python ask.py "Pourquoi la tension monte ?" --dyad china-taiwan
```

Cron : `0 */6 * * * cd /chemin/geowatch && .venv/bin/python ingest.py >> ingest.log 2>&1`

## Structure
- `config.py` — dyades suivies (pays, alias, requêtes) + endpoints WM
- `sources/` — un client par source
- `db.py` — SQLite : `signals` (payload brut) + `markets` (historique des cotes)
- `ingest.py` / `ask.py` — collecte / interrogation

## Vue pays & réseau de soutiens
```bash
python ingest.py --profiles        # Banque mondiale + Wikidata (cron hebdo suffit)
python country.py IR               # fiche pays en terminal
python country.py houthis          # marche aussi pour un acteur non étatique
python export_html.py              # → geowatch.html : graphe interactif + fiches
python update_network.py IR        # Claude + web propose des MAJ → network.pending.yaml
```
- `network.yaml` = source de vérité du graphe, curé à la main, chaque arête sourcée et datée.
- Profils : démographie + tendance (taux annuel 10 ans, fécondité vs 2,1), rentes de ressources (% PIB),
  terres arables, eau, R&D, export high-tech, défense, forme de gouvernement.
- Limites : données Banque mondiale annuelles avec 1-2 ans de retard ; « forme de gouvernement »
  Wikidata = forme officielle, pas le fonctionnement réel. Pour ça, brancher V-Dem (Regimes of the World).
