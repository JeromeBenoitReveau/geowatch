# geowatch

Q&A géopolitique sourcé. Agrège UCDP (violence armée), GDELT (tonalité/volume médiatique) et marchés de prédiction (Polymarket, Kalshi), puis répond via Claude — **aucun pourcentage sans cote de marché réelle derrière**. Toutes les sources sont gratuites.

## Setup
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # clé Anthropic + jeton UCDP
```

## Jeton UCDP
L'API UCDP est gratuite mais demande un jeton. L'obtenir par e-mail à mertcan.yilmaz@pcr.uu.se
(objet « UCDP API Access Request » : nom, affiliation, rôle, usage prévu) — réponse sous 3 à 5 jours ouvrés.
Voir https://ucdp.uu.se/apidocs/. Sans jeton, `ingest.py` tourne quand même, sans la composante violence.

## Usage
```bash
python ingest.py                                   # à mettre en cron, ex. toutes les 6 h
python ask.py "Quelle probabilité qu'Israël attaque l'Iran ?"
python ask.py "Pourquoi la tension monte ?" --dyad china-taiwan
python tension.py                                  # niveau de tension de chaque dyade
```

Cron : `0 */6 * * * cd /chemin/geowatch && .venv/bin/python ingest.py >> ingest.log 2>&1`

## Structure
- `config.py` — dyades suivies (pays, alias, requêtes, codes UCDP)
- `sources/` — un client par source
- `db.py` — SQLite : `signals` (payload brut) + `markets` (historique des cotes)
- `ingest.py` / `ask.py` — collecte / interrogation
- `tension.py` — indice de tension qualitatif (voir ci-dessous)

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

## Indice de tension
Quand aucun marché ne couvre la question, on affiche un niveau **faible / modéré / élevé / critique**,
calculé par règles fixes dans `tension.py` — jamais un pourcentage. Trois composantes, notées 0 à 3
selon le nombre de seuils franchis :

| Composante | Mesure | Seuils (1 / 2 / 3 points) |
|---|---|---|
| `media_tone` | Tonalité GDELT moyenne des dernières 24 h | ≤ −2 / ≤ −4 / ≤ −6 |
| `media_surge` | Volume d'articles 24 h ÷ moyenne journalière des jours précédents | × 1,5 / × 2,5 / × 4 |
| `violence` | Morts (estimation `best`) dans les affrontements **directs** entre les deux pays, 90 j, UCDP | ≥ 1 / ≥ 25 / ≥ 1 000 |

Niveau = part des points obtenus sur les composantes disponibles (< 25 % faible, < 50 % modéré,
< 75 % élevé, sinon critique), avec un plancher : des morts directs imposent au moins « modéré »
(≥ 25 morts : au moins « élevé »). Les seuils 25 et 1 000 reprennent les seuils UCDP de conflit armé
et de guerre (annuels chez UCDP, appliqués ici à 90 jours, donc plus stricts).

Limites : seuils = heuristiques initiales, à calibrer quand l'historique GDELT sera suffisant ;
UCDP a ~1 mois de retard ; « direct » = les deux pays nommés parmi les belligérants, donc les
proxies (Hezbollah, Houthis…) n'y comptent pas — ils passent par `network.yaml`.
