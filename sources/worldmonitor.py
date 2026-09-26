import os, httpx

BASE = "https://api.worldmonitor.app/api"

def call(service, rpc, params):
    r = httpx.get(f"{BASE}/{service}/v1/{rpc}", params=params, timeout=30,
                  headers={"X-WorldMonitor-Key": os.environ["WORLDMONITOR_KEY"]})
    r.raise_for_status()
    return r.json()

def fetch_country(endpoints, iso):
    """Renvoie [(kind, payload)] — payload brut, le LLM le lit tel quel."""
    out = []
    for service, rpc, params in endpoints:
        p = {k: (v.format(iso=iso) if isinstance(v, str) else v) for k, v in params.items()}
        try:
            out.append((f"{service}/{rpc}:{iso}", call(service, rpc, p)))
        except httpx.HTTPError as e:
            print(f"  [wm] {service}/{rpc} {iso} → {e}")
    return out
