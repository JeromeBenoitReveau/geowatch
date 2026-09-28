# geowatch — contexte pour Claude Code

Outil perso (futur open source) : graphe sourcé « qui soutient qui » dans les conflits, publié en
données ouvertes, relié aux cotes des marchés de prédiction historisées. En Python.
Auteur : Jérôme. Style attendu : direct, concret, pas de sur-ingénierie.

## Principe non négociable
Aucun pourcentage affiché sans cote de marché de prédiction réelle derrière (Polymarket, Kalshi).
geowatch ne calcule ni n'estime de probabilité.

## Architecture
- `network.yaml` — graphe (États, non étatiques, blocs), curé à la main, chaque arête sourcée et datée. Source de vérité.
- Kinds du graphe : state, bloc (membres via `member_of`), non_state, party, person (calque « détail », `base` obligatoire)
- `network.py` — requêtes sur le graphe ; `validate.py` — contrôle du schéma (CI : `.github/workflows/validate.yml`)
- `config.py` — paires suivies (`countries` = ids du graphe, `keywords` pour matcher les titres de marchés)
- `sources/markets.py` — Polymarket (gamma-api public-search) + Kalshi (trade-api v2)
- `sources/profiles.py` — Banque mondiale WDI + Wikidata SPARQL (régime, chef d'État)
- `history.py` — historique des cotes en CSV versionné : `data/markets.csv` + `data/odds.csv`
- `db.py` — profils pays en JSON versionné : `data/profiles.json` (rafraîchi le 1er du mois par ingest.yml)
- `ingest.py` : GitHub Actions toutes les 6 h (`.github/workflows/ingest.yml`), commite `data/` / `ingest.py --profiles` (GitHub Actions, mensuel)
- `.github/workflows/pages.yml` — construit et publie site/ sur GitHub Pages (inactif tant que le dépôt est privé)
- `track.py` — cotes actuelles, variation 7 j, marchés disparus du relevé
- `build.py` — site statique `site/` (vis-network) + exports `network.json` / `network.csv`
- `country.py` — fiche pays en terminal ; `update_network.py` — Claude + web search propose des MAJ dans network.pending.yaml (relecture humaine obligatoire)

## Décisions prises
- 2026-09-26 : historique des cotes en CSV dans le dépôt (et non SQLite) pour que GitHub Actions l'alimente ; c'est aussi une donnée ouverte.
- Kalshi : scan unique des événements World/Politics par run ; très peu de marchés sur nos paires (surtout US-centrés), Polymarket fournit l'essentiel.
- 2026-09-26 : recentrage. Le Q&A (ask.py) faisait doublon avec WM Analyst de World Monitor → retiré,
  avec GDELT, UCDP et l'indice de tension (visibles dans l'historique git si besoin).
- World Monitor : API payante (Pro 39,99 $/mois = MCP/SDK 50 appels/j ; REST = API Starter 99,99 $/mois).
  Non utilisé ; son tableau de bord gratuit sert au suivi temps réel. ACLED : pas d'API au niveau gratuit.
- Licences : code MIT, données du graphe CC BY 4.0.
- network.yaml reste la source de vérité ; rien n'y entre sans relecture humaine.
- Blocs d'influence : `alignments.yaml` = liens FORMELS par niveau (3 défense mutuelle, 2 partenariat stratégique, 1 candidature/participation gelée, 0 intégration affichée seulement), sourcés ; `entity` rattache des groupes à un acteur (niveaux de l'UE). Satellites et « disputés » déduits des arêtes par `network.influence()`. Partis et personnalités jamais classés. Étape 2 prévue : cohésion réelle via les votes à l'Assemblée générale de l'ONU.
- Personnes : champ `wikidata: Qxxx` → photo Wikimedia Commons (P18) dans `data/people.json`, avec auteur et licence, crédités dans la fiche (obligatoire pour CC BY-SA). Icônes Lucide (ISC) inlinées dans build.py.
- YAML : le code ISO « NO » (Norvège) doit être entre guillemets, sinon il est lu comme false.
- Carte (Leaflet + Natural Earth/world-atlas, sans tuiles) : `data/geo.json` (Wikidata P625/P299, tous les pays des acteurs et d'alignments.yaml, rafraîchi avec les profils) ; `coords` explicites pour les blocs.
- Taille des nœuds = valeur mesurée (Banque mondiale : MS.MIL.XPND.CD, PIB ; UE via l'agrégat EUU) ou nb de soutiens — jamais un poids choisi à la main.
- Les sites/pages générés échappent tout texte venant du graphe ou des marchés (contributions externes).

## À faire en priorité
1. Ajouter des URL aux sources de network.yaml (validate.py les signale toutes)
2. Lancer `python ingest.py --profiles` puis `python build.py`

## Backlog
- Bilan de calibration : récupérer l'issue des marchés résolus et la comparer aux cotes passées
- Historique des arêtes (depuis quand, fin) pour voir l'évolution des alliances
- Import SIPRI (transferts d'armes, inclut acteurs non étatiques) pour enrichir network.yaml
- Classification de régime via V-Dem au lieu de la forme officielle Wikidata
- Tests minimaux sur les parseurs de sources

## Sécurité
Ne jamais committer `.env`, `*.db`. Vérifier `git status` avant chaque push.
