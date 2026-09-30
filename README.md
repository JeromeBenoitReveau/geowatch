# Lignes de force

**Qui soutient qui dans les conflits, et pourquoi.** Un site d'information qui explique les conflits à quelqu'un
qui n'y connaît rien : les camps, leurs soutiens étrangers, ce qu'ils y cherchent et ce qui est en jeu. Chaque relation
est **sourcée, datée et relue à la main**, et publiée en données ouvertes.

Site : https://jeromebenoitreveau.github.io/geowatch/ (le dépôt garde son ancien nom, `geowatch`).

Règle non négociable : **aucune prédiction**. Le site n'affiche aucune probabilité ni cote de paris ; les seuls
chiffres sont des mesures sourcées. Pour le suivi en temps réel, le tableau de bord gratuit
[World Monitor](https://www.worldmonitor.app) fait très bien le travail ; Lignes de force est complémentaire.

## Setup
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # clé Anthropic, seulement pour update_network.py
```

## Usage
```bash
python ingest.py              # profils pays, votes ONU, coordonnées, photos → data/ (GitHub Actions, le 1er du mois)
python country.py IR          # fiche pays + soutiens en terminal (marche aussi : houthis)
python build.py               # → site/ : accueil, dossiers, explorateur, méthode, manifeste + network.json/.csv
python validate.py            # contrôle network.yaml, alignments.yaml et dossiers.yaml (tourne aussi en CI)
python update_network.py IR   # Claude + web propose des MAJ → network.pending.yaml, à relire
```
`site/` est statique ; `.github/workflows/pages.yml` le reconstruit et le publie sur GitHub Pages à chaque
changement des données ou du code du site.

## Les dossiers (`dossiers.yaml`)
Un dossier raconte un conflit : résumé, carte d'ouverture, les deux camps et leurs soutiens (lus dans
`network.yaml`, avec le « pourquoi » de chacun), enjeux, coût humain, chronologie, parallèles historiques et situation
actuelle. Chaque phrase cite ses sources ; une analyse est toujours attribuée à qui la formule.

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

Votes à l'ONU : la carte peut aussi colorer chaque pays selon la fréquence à laquelle il vote comme
France/Allemagne ou comme Russie/Chine à l'Assemblée générale (jeu de données d'Erik Voeten, Harvard
Dataverse, CC0 ; dernière année disponible, environ un an de retard). L'écart de vote États-Unis ↔
France/Allemagne est suivi à part, jusqu'à l'année écoulée. Pencher vers Russie/Chine n'est pas appartenir
à l'axe : beaucoup de votes du Sud global coïncident avec ceux de la Chine.

Forums (BRICS, OCS, G7…) : listés dans `alignments.yaml` avec `kind: forum` ; affichés sur la carte, mais sans effet
sur les blocs d'influence (ce sont des cadres de coopération, pas des alliances).

Réseaux d'influence : le site distingue trois étages, les alignements (`alignments.yaml`), les soutiens (le graphe) et
les leviers, des dépendances chiffrées et sourcées (clé `dependencies` de `network.yaml`, pour commencer la part de chaque
fournisseur dans les armes importées, d'après le SIPRI). Médiations (clé `mediations`) : qui négocie entre qui.

La page `methode.html` du site détaille toutes les sources et règles de calcul.

Personnalités : ajouter `wikidata: Qxxx` pour afficher leur photo (Wikimedia Commons, auteur et licence
crédités dans la fiche). Groupes armés et partis sont représentés par des icônes Lucide.

Contribuer : modifier `network.yaml`, lancer `python validate.py`, ouvrir une PR avec les sources.
`update_network.py` aide à repérer les changements, mais rien n'entre sans relecture humaine.

## Structure
- `network.yaml` / `network.py` — le graphe (soutiens, tensions, dirigeants) et ses requêtes ; `validate.py` — son contrôle
- `alignments.yaml` — alliances et organisations, adhésions datées
- `dossiers.yaml` / `dossier.py` — les dossiers ; `data/maps/` — contours régionaux des cartes
- `pages.py` — accueil et manifeste ; `method.py` — page méthode ; `style.py` — feuille de style commune ; `brand.py` — nom
- `glossaire.yaml` / `glossary.py` — une définition par terme, infobulles partout et page glossaire
- `presets.yaml` / `presets.py` — questions pour commencer dans l'explorateur (`explorer.html?vue=<id>`)
- `sources/profiles.py` — Banque mondiale WDI + Wikidata ; `sources/unga.py` — votes à l'ONU (Voeten)
- `db.py` — données en JSON (`data/`) ; `build.py` — site statique + exports

Limites des profils : données Banque mondiale annuelles avec 1-2 ans de retard ; « forme de
gouvernement » Wikidata = forme officielle, pas le fonctionnement réel (V-Dem serait mieux).

## Licences
Code : MIT (`LICENSE`). Données du graphe : CC BY 4.0 (`LICENSE-DATA`).
