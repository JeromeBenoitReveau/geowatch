# geowatch — contexte pour Claude Code

Outil perso (futur open source) de Q&A géopolitique sourcé, en Python.
Auteur : Jérôme. Style attendu : direct, concret, pas de sur-ingénierie.

## Principe non négociable
Aucun pourcentage affiché sans cote de marché de prédiction réelle derrière (Polymarket, Kalshi).
Sinon : niveau de tension qualitatif (faible/modéré/élevé/critique) justifié par des signaux mesurables.
Ne jamais contourner cette règle (elle est dans le SYSTEM de ask.py).

## Architecture
- `config.py` — dyades suivies (5 : israel-iran, china-taiwan, russia-ukraine, india-pakistan, venezuela-guyana) + codes pays UCDP (Gleditsch & Ward)
- `sources/ucdp.py` — UCDP GED Candidate (violence armée, mensuel, ~1 mois de retard), header `x-ucdp-access-token`, 5 000 req/jour
- `tension.py` — indice de tension qualitatif par règles fixes (GDELT tonalité + volume, morts directs UCDP), seuils documentés dans le README
- `sources/gdelt.py` — GDELT DOC 2.0 (tonalité, volume, articles), sans clé, ~1 req / 5 s
- `sources/markets.py` — Polymarket (gamma-api public-search) + Kalshi (trade-api v2)
- `sources/profiles.py` — Banque mondiale WDI + Wikidata SPARQL (régime, chef d'État)
- `network.yaml` — graphe « qui soutient qui » (États, acteurs non étatiques, blocs), curé à la main, chaque arête sourcée et datée
- `network.py` — requêtes sur le graphe
- `db.py` — SQLite : signals, markets, profiles
- `ingest.py` (cron 6 h) / `ingest.py --profiles` (cron hebdo)
- `ask.py` — question → contexte (signaux + marchés + profils + réseau 2 sauts) → Claude API
- `country.py` — fiche pays en terminal ; `export_html.py` — graphe interactif (vis-network) ; `update_network.py` — Claude + web search propose des MAJ du graphe dans network.pending.yaml (relecture humaine obligatoire)

## Décisions prises
- World Monitor abandonné (2026-09-26) : API réservée aux abonnés Pro (39,99 $/mois, 50 appels/jour, licence perso) et son « WM Analyst » recouvre ask.py. On va aux sources primaires.
- ACLED écarté : le niveau gratuit (« Open ») n'a pas accès à l'API.
- Licence du repo : MIT.
- network.yaml reste la source de vérité ; rien n'y entre sans relecture humaine.
- MVP limité à 5 dyades avant généralisation.

## Jamais testé contre les APIs live — à faire en priorité
1. Obtenir un jeton UCDP, puis vérifier la détection de release (`sources/ucdp.py → releases`) et la pagination (1-indexée supposée)
2. Vérifier la forme de réponse Polymarket `public-search` et Kalshi `/markets`
3. Lancer `python ingest.py --profiles` puis `python country.py IR` et `python export_html.py`
4. Lancer `python ingest.py` puis `python ask.py "Quelle probabilité qu'Israël attaque l'Iran ?"`

## Backlog
- Classification de régime réelle via V-Dem (Regimes of the World, CSV) au lieu de la forme officielle Wikidata
- Calibrer les seuils de `tension.py` sur l'historique GDELT stocké (chaque ingestion garde tonalité et volume)
- Import SIPRI (transferts d'armes, inclut acteurs non étatiques) pour enrichir network.yaml
- Tests minimaux sur les parseurs de sources

## Sécurité
Ne jamais committer `.env`, `*.db`. Vérifier `git status` avant chaque premier push.
