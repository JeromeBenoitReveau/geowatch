"""Marchés de prédiction = seules vraies probabilités qu'on affiche."""
import json, time, httpx

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
                        "url": f"https://polymarket.com/event/{ev.get('slug', '')}",
                        "end_date": m.get("endDate")})
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
        try:
            data = _kalshi_page(params)
        except httpx.HTTPError as e:
            print(f"[kalshi] scan interrompu après {len(out)} événements → {e}")
            break  # on garde ce qui a déjà été lu
        out += [e for e in data.get("events", []) if e.get("category") in KALSHI_CATEGORIES]
        cursor = data.get("cursor")
        if not cursor:
            break
    return out

def _kalshi_page(params):
    for wait in (2, 5, 15, None):
        time.sleep(0.25)  # ~70 pages d'affilée déclenchent sinon des 429 depuis les runners GitHub
        r = httpx.get(f"{KALSHI}/events", params=params, timeout=30)
        if r.status_code == 429 and wait:
            ra = r.headers.get("Retry-After", "")
            time.sleep(float(ra) if ra.replace(".", "", 1).isdigit() else wait)
            continue
        r.raise_for_status()
        return r.json()

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
                        "url": f"https://kalshi.com/markets/{ev.get('series_ticker', '').lower()}",
                        "end_date": m.get("close_time")})
    return out

def fetch(keywords, kalshi_evs):
    out = []
    try:
        out += polymarket(keywords)
    except httpx.HTTPError as e:
        print(f"  [polymarket] → {e}")
    return out + kalshi(keywords, kalshi_evs)

def resolve(source, market_id):
    """Issue d'un marché clos : {"resolved_at", "outcome": 1 (Oui) | 0 (Non)}, ou None s'il n'est pas
    (encore) tranché. Un marché annulé ou réglé à 50/50 reste None : il n'entre pas dans le bilan."""
    if source == "polymarket":
        # l'API renvoie l'état ouvert d'un marché tant qu'on ne demande pas explicitement closed=true,
        # et un marché archivé après résolution n'apparaît qu'avec archived=true
        m = {}
        for extra in ({}, {"archived": "true"}):
            r = httpx.get("https://gamma-api.polymarket.com/markets", timeout=30,
                          params={"id": market_id, "closed": "true", **extra})
            r.raise_for_status()
            if r.json():
                m = r.json()[0]
                break
        if not m.get("closed") or m.get("umaResolutionStatus") != "resolved":
            return None
        prices = m.get("outcomePrices")
        prices = json.loads(prices) if isinstance(prices, str) else prices
        yes = float(prices[0]) if prices else None
        if yes is None or 0.01 < yes < 0.99:
            return None
        return {"resolved_at": m.get("closedTime") or m.get("endDate"), "outcome": int(yes >= 0.99)}
    if source == "kalshi":
        r = httpx.get(f"{KALSHI}/markets/{market_id}", timeout=30)
        r.raise_for_status()
        m = r.json().get("market", {})
        if m.get("status") not in ("finalized", "settled") or m.get("result") not in ("yes", "no"):
            return None
        return {"resolved_at": m.get("close_time"), "outcome": int(m["result"] == "yes")}
    return None
