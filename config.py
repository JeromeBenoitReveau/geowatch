"""Scope du MVP : quelques dyades chaudes. Ajouter une dyade = ajouter une entrée."""

DYADS = {
    "israel-iran": {
        "countries": ["IL", "IR"],
        "aliases": ["israël", "israel", "iran", "tsahal", "idf", "téhéran", "tehran"],
        "gdelt_query": '(israel OR israeli) (iran OR iranian)',
        "market_keywords": ["israel", "iran"],
    },
    "china-taiwan": {
        "countries": ["CN", "TW"],
        "aliases": ["chine", "china", "taïwan", "taiwan", "pékin", "beijing", "taipei"],
        "gdelt_query": '(china OR chinese OR beijing) taiwan',
        "market_keywords": ["china", "taiwan"],
    },
    "russia-ukraine": {
        "countries": ["RU", "UA"],
        "aliases": ["russie", "russia", "ukraine", "kremlin", "kyiv", "kiev", "poutine", "putin"],
        "gdelt_query": '(russia OR russian) (ukraine OR ukrainian)',
        "market_keywords": ["russia", "ukraine"],
    },
    "india-pakistan": {
        "countries": ["IN", "PK"],
        "aliases": ["inde", "india", "pakistan", "cachemire", "kashmir"],
        "gdelt_query": '(india OR indian) (pakistan OR pakistani)',
        "market_keywords": ["india", "pakistan"],
    },
    "venezuela-guyana": {
        "countries": ["VE", "GY"],
        "aliases": ["venezuela", "guyana", "essequibo", "maduro"],
        "gdelt_query": 'venezuela (guyana OR essequibo)',
        "market_keywords": ["venezuela", "guyana"],
    },
}

# World Monitor : pattern /api/<service>/v1/<rpc-name>.
# ⚠️ Vérifier noms exacts + paramètres dans https://worldmonitor.app/openapi.yaml
# (ou `npx worldmonitor tools`) avant le premier run. {iso} = code pays ISO2.
WM_ENDPOINTS = [
    ("conflict", "list-acled-events", {"country": "{iso}", "days": 7}),
    ("intelligence", "get-cii", {"countries": "{iso}"}),  # Country Instability Index
]

LOOKBACK_DAYS = 7
