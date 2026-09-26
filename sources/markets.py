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

def kalshi(keywords, max_pages=5):
    base = "https://api.elections.kalshi.com/trade-api/v2/markets"
    out, cursor = [], None
    for _ in range(max_pages):
        params = {"status": "open", "limit": 1000}
        if cursor:
            params["cursor"] = cursor
        r = httpx.get(base, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        for m in data.get("markets", []):
            if _match(m.get("title"), keywords) and m.get("last_price") is not None:
                out.append({"source": "kalshi", "id": m["ticker"], "question": m["title"],
                            "prob": m["last_price"] / 100, "volume": m.get("volume", 0),
                            "url": f"https://kalshi.com/markets/{m['event_ticker']}"})
        cursor = data.get("cursor")
        if not cursor:
            break
    return out

def fetch(keywords):
    out = []
    for fn in (polymarket, kalshi):
        try:
            out += fn(keywords)
        except httpx.HTTPError as e:
            print(f"  [{fn.__name__}] → {e}")
    return out
