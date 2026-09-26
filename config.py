"""Scope du MVP : quelques dyades chaudes. Ajouter une dyade = ajouter une entrée.

keywords : doivent TOUS apparaître dans le titre d'un marché (Polymarket/Kalshi)
           et dans les belligérants d'un événement UCDP pour qu'il compte comme « direct ».
ucdp_gw  : codes pays Gleditsch & Ward (≠ ISO), utilisés par le filtre Country d'UCDP.
"""

DYADS = {
    "israel-iran": {
        "countries": ["IL", "IR"],
        "aliases": ["israël", "israel", "iran", "tsahal", "idf", "téhéran", "tehran"],
        "gdelt_query": '(israel OR israeli) (iran OR iranian)',
        "keywords": ["israel", "iran"],
        "ucdp_gw": [666, 630],
    },
    "china-taiwan": {
        "countries": ["CN", "TW"],
        "aliases": ["chine", "china", "taïwan", "taiwan", "pékin", "beijing", "taipei"],
        "gdelt_query": '(china OR chinese OR beijing) taiwan',
        "keywords": ["china", "taiwan"],
        "ucdp_gw": [710, 713],
    },
    "russia-ukraine": {
        "countries": ["RU", "UA"],
        "aliases": ["russie", "russia", "ukraine", "kremlin", "kyiv", "kiev", "poutine", "putin"],
        "gdelt_query": '(russia OR russian) (ukraine OR ukrainian)',
        "keywords": ["russia", "ukraine"],
        "ucdp_gw": [365, 369],
    },
    "india-pakistan": {
        "countries": ["IN", "PK"],
        "aliases": ["inde", "india", "pakistan", "cachemire", "kashmir"],
        "gdelt_query": '(india OR indian) (pakistan OR pakistani)',
        "keywords": ["india", "pakistan"],
        "ucdp_gw": [750, 770],
    },
    "venezuela-guyana": {
        "countries": ["VE", "GY"],
        "aliases": ["venezuela", "guyana", "essequibo", "maduro"],
        "gdelt_query": 'venezuela (guyana OR essequibo)',
        "keywords": ["venezuela", "guyana"],
        "ucdp_gw": [101, 110],
    },
}

LOOKBACK_DAYS = 7        # GDELT, marchés
UCDP_LOOKBACK_DAYS = 90  # UCDP Candidate est publié mensuellement, avec ~1 mois de retard
