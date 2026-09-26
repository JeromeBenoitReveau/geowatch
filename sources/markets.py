"""Marchés de prédiction = seules vraies probabilités qu'on affiche."""
import json, httpx

def _match(text, keywords):
    t = (text or "").lower()
    return all(k in t for k in keywords)

def polymarket(keywords):
    r = httpx.get("https://gamma-api.polymarket.com/public-search",
                  params={"q": " ".join(keywords), "limit_per_type": 20}, timeout=30)
    r.raise_for_status()
    out = []
    for ev in r.json().get("events", []):
        for m in ev.get("markets", []):
            if m.get("closed") or not _match(m.get("question"), keywords):
                continue
            prices = m.get("outcomePrices")
            prices = json.loads(prices) if isinstance(prices, str) else prices
            if not prices:
                continue
            out.append({"source": "polymarket", "id": str(m.get("id")),
                        "question": m["question"], "prob": float(prices[0]),  # prix du "Yes"
                        "volume": float(m.get("volume") or 0),
                        "url": f"https://polymarket.com/event/{ev.get('slug', '')}"})
    return out

KALSHI = "https://api.elections.kalshi.com/trade-api/v2"
KALSHI_CATEGORIES = {"World", "Politics"}

def kalshi_events(max_pages=150):
    """Événements Kalshi ouverts des catégories géopolitiques, marchés inclus.
    Un seul scan par run (~70 pages, ~30 s) : /markets seul est noyé sous les paris sportifs."""
    out, cursor = [], None
    for _ in range(max_pages):
        params = {"status": "open", "limit": 200, "with_nested_markets": "true"}
        if cursor:
            params["cursor"] = cursor
        r = httpx.get(f"{KALSHI}/events", params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        out += [e for e in data.get("events", []) if e.get("category") in KALSHI_CATEGORIES]
        cursor = data.get("cursor")
        if not cursor:
            break
    return out

def kalshi(keywords, events):
    out = []
    for ev in events:
        for m in ev.get("markets") or []:
            # titre du marché seulement : celui de l'événement donne des faux positifs
            question = m.get("title") or ""
            if m.get("yes_sub_title"):
                question += f" — {m['yes_sub_title']}"
            volume = float(m.get("volume_fp") or 0)
            if not _match(question, keywords) or not m.get("last_price_dollars") or not volume:
                continue
            out.append({"source": "kalshi", "id": m["ticker"], "question": question,
                        "prob": float(m["last_price_dollars"]), "volume": volume,
                        "url": f"https://kalshi.com/markets/{ev.get('series_ticker', '').lower()}"})
    return out

def fetch(keywords, kalshi_evs):
    out = []
    try:
        out += polymarket(keywords)
    except httpx.HTTPError as e:
        print(f"  [polymarket] → {e}")
    return out + kalshi(keywords, kalshi_evs)
