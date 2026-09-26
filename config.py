"""Paires suivies sur les marchés de prédiction. Ajouter une paire = ajouter une entrée.

countries : ids d'acteurs de network.yaml (ISO2 pour un État)
keywords  : doivent TOUS apparaître dans le titre d'un marché (Polymarket/Kalshi)
"""

DYADS = {
    "israel-iran": {
        "countries": ["IL", "IR"],
        "keywords": ["israel", "iran"],
    },
    "china-taiwan": {
        "countries": ["CN", "TW"],
        "keywords": ["china", "taiwan"],
    },
    "russia-ukraine": {
        "countries": ["RU", "UA"],
        "keywords": ["russia", "ukraine"],
    },
    "india-pakistan": {
        "countries": ["IN", "PK"],
        "keywords": ["india", "pakistan"],
    },
    "venezuela-guyana": {
        "countries": ["VE", "GY"],
        "keywords": ["venezuela", "guyana"],
    },
}

MOVE_ALERT_PTS = 10  # variation de cote (points de %) sur 7 j jugée notable
