# Lignes de force (dépôt « geowatch ») — contexte pour Claude Code

Site d'information open source : les conflits expliqués aux néophytes, à partir d'un graphe sourcé
« qui soutient qui, et pourquoi », publié en données ouvertes. En Python.
Auteur : Jérôme. Style attendu : direct, concret, pas de sur-ingénierie.

## Principe non négociable
Aucune prédiction : le site n'affiche aucune probabilité ni cote de paris (décision du 2026-09-29 : site d'information ;
et en France, l'ANJ a fait bloquer Polymarket le 16 juillet 2026 — diffuser ses cotes au public peut constituer une
publicité illégale pour des paris non autorisés). Les seuls chiffres sont des mesures sourcées.

## Architecture
- `network.yaml` — graphe (États, non étatiques, blocs), curé à la main, chaque arête sourcée et datée. Source de vérité.
- Kinds du graphe : state, bloc (membres via `member_of`), non_state, party, person (calque « détail », `base` obligatoire)
- Personnes (décision 2026-09-29) : `person` = nœud SEULEMENT si relation propre, distincte de l'institution dirigée (Musk ; Trump/Vance pour RN/AfD). Un chef qui n'agit qu'à travers son institution = champ `leader` de l'acteur ({name, wikidata, role, sources} ou id de person ; photo « leader:<id> » dans people.json). validate.py signale une personne sans relation propre. Session dédiée prévue : typologie des personnalités d'influence (dirigeants, milliardaires, religieux, idéologues, médias) et critères de sélection.
- Interface (2026-09-29, validée par Jérôme sur maquette) : très épurée, le contenu est déjà chargé. `style.py` → site/style.css commun (jetons, Newsreader pour titres/chapeau, Public Sans pour le texte). Couleur réservée aux données (camps --a/--b, soutiens, tensions), interface en encre et gris, pas de boîtes : l'espace et des filets fins séparent. Sources en notes numérotées (classe Notes de dossier.py) listées en bas de page ; pas d'étiquettes en majuscules, pas de « · » ni de « → » décoratifs.
- Site : `index.html` = accueil (`pages.py` : baseline, cartes des conflits, blocs Explorer), `explorer.html` = graphe/carte/organisations (build.py ; ancres #graphe, #carte, #organisations, #graphe:<id>), `manifeste.html` (pages.py), `methode.html` (method.py). Nom et baseline dans `brand.py` (« Lignes de force », validé par Jérôme le 2026-09-29 ; « geowatch » était pris, le dépôt garde ce nom)
- `dossiers.yaml` + `dossier.py` — pages « dossier » pour néophytes (site/<id>.html) : récit sourcé ; camps et soutiens LUS dans network.yaml. Champ `why` sur les arêtes = motivation, analyse attribuée à sa source. Pilote : Soudan (2026-09-29)
- Carte d'ouverture des dossiers (2026-09-29, prototype Soudan) : bloc `map` de dossiers.yaml — zones de contrôle par région (contours geoBoundaries/OCHA dans data/maps/, copiés dans site/maps/), flèches des soutiens depuis data/geo.json, lieux (coords Wikidata), routes et flux, chaque élément sourcé et cliquable. Pas de position inventée : un lieu sans coordonnées vérifiables n'est pas épinglé.
- Tensions (2026-09-29) : clé `tensions:` de network.yaml (war | sanctions | claims | rivalry ; status active | reduced | ended), SÉPARÉES des soutiens : hors calcul des blocs et hors soutiens des dossiers ; graphe (physics:false), carte, fiches, section « Les autres lignes de fracture » des dossiers.
- Dossiers : champ `history` = parallèles historiques ET leurs limites, attribués à des historiens. Page « Revivons-nous les années 30 ? » prévue (débat entre historiens, pas une thèse).
- `network.py` — requêtes sur le graphe ; `validate.py` — contrôle du schéma (CI : `.github/workflows/validate.yml`)
- `sources/profiles.py` — Banque mondiale WDI + Wikidata SPARQL (régime, chef d'État)
- `db.py` — profils pays en JSON versionné : `data/profiles.json` (rafraîchi le 1er du mois par ingest.yml)
- `ingest.py` — profils, votes ONU, coordonnées, photos ; GitHub Actions le 1er du mois (`.github/workflows/ingest.yml`, « data refresh »), commite `data/`
- `.github/workflows/pages.yml` — construit et publie site/ sur GitHub Pages
- `build.py` — site statique `site/` (vis-network, Leaflet) + exports `network.json` / `network.csv` ; `method.py` — page `methode.html` (méthode et sources) générée à partir des mêmes données, à tenir à jour quand une règle de calcul change
- `country.py` — fiche pays en terminal ; `update_network.py` — Claude + web search propose des MAJ dans network.pending.yaml (relecture humaine obligatoire)

## Décisions prises
- 2026-09-29 : réorientation vers les néophytes — l'entrée principale devient les dossiers (qui s'affronte, qui soutient, POURQUOI, enjeux) ; graphe, carte et vue Organisations = mode « Explorer ». World Monitor = stats froides, geowatch = relations expliquées.
- 2026-09-29 : cotes des marchés de prédiction (Polymarket, Kalshi) retirées du site ET de la collecte (code, workflow 6 h, data/odds.csv…) — voir le principe ci-dessus. L'ancien code et les relevés restent dans l'historique git (avant le commit « remove prediction-market odds »).
- 2026-09-26 : recentrage. Le Q&A (ask.py) faisait doublon avec WM Analyst de World Monitor → retiré,
  avec GDELT, UCDP et l'indice de tension (visibles dans l'historique git si besoin).
- World Monitor : API payante (Pro 39,99 $/mois = MCP/SDK 50 appels/j ; REST = API Starter 99,99 $/mois).
  Non utilisé ; son tableau de bord gratuit sert au suivi temps réel. ACLED : pas d'API au niveau gratuit.
- Licences : code MIT, données du graphe CC BY 4.0.
- network.yaml reste la source de vérité ; rien n'y entre sans relecture humaine.
- Blocs d'influence : `alignments.yaml` = liens FORMELS par niveau (3 défense mutuelle, 2 partenariat stratégique, 1 candidature/participation gelée, 0 intégration affichée seulement), sourcés ; `entity` rattache des groupes à un acteur (niveaux de l'UE). Satellites et « disputés » déduits des arêtes par `network.influence()`. Partis et personnalités jamais classés. Étape 2 prévue : cohésion réelle via les votes à l'Assemblée générale de l'ONU.
- Personnes : champ `wikidata: Qxxx` → photo Wikimedia Commons (P18) dans `data/people.json`, avec auteur et licence, crédités dans la fiche (obligatoire pour CC BY-SA). Icônes Lucide (ISC) inlinées dans build.py.
- Votes à l'ONU (étape 2) : `sources/unga.py`, jeu Voeten (Harvard Dataverse, CC0), `data/unga.json` retéléchargé seulement si nouvelle version (vérifié avec les profils, mensuel). Placement des pays = taux d'accord (dernière année dispo, ~1 an de retard) avec France/Allemagne vs Russie/Chine. Les points idéaux (axe unique, année écoulée) ne servent QU'à l'écart États-Unis ↔ France/Allemagne : un axe unique place mal un pays entre deux blocs (en 2025 la Russie y « remonte » artificiellement).
- `data/geo.json` couvre tous les membres de l'ONU (requête Wikidata par ISO3, P298).
- Forums (BRICS, OCS, UEEA, G7, Mercosur, ASEAN) : groupes `kind: forum` d'alignments.yaml, sans bloc ni niveau, hors calcul des blocs ; sélecteur « Organisation » de la carte.
- YAML : le code ISO « NO » (Norvège) doit être entre guillemets, sinon il est lu comme false.
- Carte (Leaflet + Natural Earth/world-atlas, sans tuiles) : `data/geo.json` (Wikidata P625/P299, tous les pays des acteurs et d'alignments.yaml, rafraîchi avec les profils) ; `coords` explicites pour les blocs.
- Taille des nœuds = valeur mesurée (Banque mondiale : MS.MIL.XPND.CD, PIB ; UE via l'agrégat EUU) ou nb de soutiens — jamais un poids choisi à la main.
- Organisations superposées : jusqu'à 6, palette catégorielle fixe, JAMAIS de transparence qui mélange les couleurs (retour de Jérôme). Carte : rayures des couleurs des organisations d'un pays. Vue « Organisations » : diagramme d'Euler (un cercle par organisation, aire ∝ nb de membres, chevauchements ∝ membres communs, chaque pays dans la zone exacte de ses appartenances ; zone impossible → placé au plus près, contour pointillé). Rejeté : contours sur le graphe de soutiens (les liens tirent les pays ailleurs). Adhésions/départs datés depuis 2014 dans alignments.yaml (`joined`, `left`, `since`).
- Les sites/pages générés échappent tout texte venant du graphe ou des marchés (contributions externes).

## À faire en priorité
1. Ajouter des URL aux sources de network.yaml (validate.py les signale toutes)
2. Lancer `python ingest.py --profiles` puis `python build.py`

## Backlog
- Historique des arêtes (depuis quand, fin) pour voir l'évolution des alliances
- Import SIPRI (transferts d'armes, inclut acteurs non étatiques) pour enrichir network.yaml
- Classification de régime via V-Dem au lieu de la forme officielle Wikidata
- Tests minimaux sur les parseurs de sources

## Sécurité
Ne jamais committer `.env`, `*.db`. Vérifier `git status` avant chaque push.
