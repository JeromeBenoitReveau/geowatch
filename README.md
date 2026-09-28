# geowatch

Qui soutient qui dans les conflits en cours — États, acteurs non étatiques, blocs — sous forme
de graphe **sourcé, daté et relu à la main**, publié en données ouvertes. Chaque paire suivie est
reliée aux cotes des marchés de prédiction (Polymarket, Kalshi), historisées pour voir ce qui bouge.

Règle non négociable : **aucun pourcentage sans cote de marché réelle derrière**. geowatch ne produit
pas de probabilités ; il affiche celles des marchés, avec leur source.

Pour le suivi en temps réel (événements, instabilité), le tableau de bord gratuit
[World Monitor](https://www.worldmonitor.app) fait très bien le travail ; geowatch est complémentaire.

## Setup
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # clé Anthropic, seulement pour update_network.py
```
Aucune clé n'est nécessaire pour les marchés, les profils pays ou le site.

## Usage
```bash
python ingest.py              # relève les cotes → data/ (tourne déjà toutes les 6 h via GitHub Actions)
python ingest.py --profiles   # profils pays → data/profiles.json (GitHub Actions, le 1er du mois)
python track.py               # cotes actuelles + variation 7 j, ⚡ si ≥ 10 pts
python track.py israel-iran
python country.py IR          # fiche pays + soutiens en terminal (marche aussi : houthis)
python build.py               # → site/ : graphe interactif, fiches, marchés + network.json/.csv
python validate.py            # contrôle network.yaml (tourne aussi en CI)
python update_network.py IR   # Claude + web propose des MAJ → network.pending.yaml, à relire
```
L'historique des cotes est relevé par GitHub Actions (`.github/workflows/ingest.yml`, toutes les 6 h,
déclenchable à la main depuis l'onglet Actions) et commité dans `data/` : `markets.csv` (un marché par
ligne) et `odds.csv` (un relevé par ligne). En local, faire `git pull` avant `track.py` / `build.py`,
et éviter de commiter des relevés locaux (conflits avec ceux de la CI).

`site/` est statique. Une fois le dépôt public, `.github/workflows/pages.yml` le reconstruit et le publie
sur GitHub Pages à chaque changement du graphe et après chaque relevé.

## Le graphe (`network.yaml`)
Source de vérité, curé à la main. Chaque arête a des types (armes, financement, troupes…), un statut,
un niveau de confiance, des sources et une date de vérification. `validate.py` refuse une arête sans
source, avec un acteur inconnu ou une valeur hors liste, et signale celles vérifiées il y a plus de
6 mois ou dont aucune source n'a d'URL.

Acteurs : États, blocs (`member_of` pour les membres, ex. `[EU]`), groupes armés non étatiques, et
en calque « détail » les partis et personnalités (`base` = pays d'ancrage obligatoire). Sur le site, la
taille des acteurs suit une valeur mesurée (dépenses militaires ou PIB en dollars, Banque mondiale) ou le
nombre de soutiens accordés ; cliquer un bloc surligne ses membres et liste leurs soutiens.

Blocs d'influence : `alignments.yaml` liste les liens formels (traités, adhésions) avec un niveau —
3 défense mutuelle (OTAN, UE, traités bilatéraux américains, OTSC…), 2 partenariat stratégique,
1 candidature ou participation gelée, 0 intégration sans effet (zone euro, Schengen). Un acteur sans lien
formel dont tous les soutiens actifs viennent d'un même bloc en est déduit « satellite ». La carte colore
chaque pays selon son bloc, plus ou moins intensément selon le niveau.

Personnalités : ajouter `wikidata: Qxxx` pour afficher leur photo (Wikimedia Commons, auteur et licence
crédités dans la fiche). Groupes armés et partis sont représentés par des icônes Lucide.

Contribuer : modifier `network.yaml`, lancer `python validate.py`, ouvrir une PR avec les sources.
`update_network.py` aide à repérer les changements, mais rien n'entre sans relecture humaine.

## Structure
- `network.yaml` / `network.py` — le graphe et ses requêtes ; `validate.py` — son contrôle
- `config.py` — paires suivies sur les marchés (acteurs + mots-clés)
- `sources/markets.py` — Polymarket (gamma-api) + Kalshi (trade-api v2), sans clé
- `sources/profiles.py` — Banque mondiale WDI + Wikidata (régime, chef d'État)
- `history.py` — historique des cotes en CSV (`data/`) ; `db.py` — profils pays en JSON (`data/profiles.json`)
- `track.py` — lecture de l'historique des cotes ; `build.py` — site statique + exports

Limites des profils : données Banque mondiale annuelles avec 1-2 ans de retard ; « forme de
gouvernement » Wikidata = forme officielle, pas le fonctionnement réel (V-Dem serait mieux).

## Licences
Code : MIT (`LICENSE`). Données du graphe : CC BY 4.0 (`LICENSE-DATA`).
