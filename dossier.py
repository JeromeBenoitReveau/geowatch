"""Pages « dossier » (site/<id>.html) : un conflit expliqué à quelqu'un qui n'y connaît rien.
Le récit vient de dossiers.yaml ; les camps, leurs soutiens et le « pourquoi » de chaque soutien viennent de
network.yaml, pour qu'un dossier ne puisse pas contredire le graphe. Seuls pourcentages : les cotes des marchés."""
from html import escape as e
from pathlib import Path
from urllib.parse import urlparse
import json, re, shutil
import yaml
import brand, network

PATH = Path(__file__).with_name("dossiers.yaml")
URL = re.compile(r"https?://\S+")
TYPES_FR = {"arms": "armes", "financial": "argent", "training": "entraînement", "troops": "troupes",
            "intelligence": "renseignement", "political": "soutien politique", "economic": "soutien économique",
            "dual_use": "matériel à double usage"}
STATUS_FR = {"alleged": "allégué — démenti ou non prouvé", "reduced": "en baisse", "ended": "terminé"}
CONF_FR = {"high": "documenté officiellement", "medium": "sources concordantes", "low": "allégations"}
# Icônes Lucide (ISC), comme build.py
ICONS = {
    "gem": '<path d="M6 3h12l4 6-10 13L2 9Z"/><path d="M11 3 8 9l4 13 4-13-3-6"/><path d="M2 9h20"/>',
    "anchor": '<path d="M12 22V8"/><path d="M5 12H2a10 10 0 0 0 20 0h-3"/><circle cx="12" cy="5" r="3"/>',
    "waves": '<path d="M2 6c.6.5 1.2 1 2.5 1C7 7 7 5 9.5 5c2.6 0 2.4 2 5 2 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1"/><path d="M2 12c.6.5 1.2 1 2.5 1 2.5 0 2.5-2 5-2 2.6 0 2.4 2 5 2 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1"/><path d="M2 18c.6.5 1.2 1 2.5 1 2.5 0 2.5-2 5-2 2.6 0 2.4 2 5 2 2.5 0 2.5-2 5-2 1.3 0 1.9.5 2.5 1"/>',
    "wheat": '<path d="M2 22 16 8"/><path d="M3.47 12.53 5 11l1.53 1.53a3.5 3.5 0 0 1 0 4.94L5 19l-1.53-1.53a3.5 3.5 0 0 1 0-4.94Z"/><path d="M7.47 8.53 9 7l1.53 1.53a3.5 3.5 0 0 1 0 4.94L9 15l-1.53-1.53a3.5 3.5 0 0 1 0-4.94Z"/><path d="M11.47 4.53 13 3l1.53 1.53a3.5 3.5 0 0 1 0 4.94L13 11l-1.53-1.53a3.5 3.5 0 0 1 0-4.94Z"/><path d="M20 2h2v2a4 4 0 0 1-4 4h-2V6a4 4 0 0 1 4-4Z"/>',
    "route": '<circle cx="6" cy="19" r="3"/><path d="M9 19h8.5a3.5 3.5 0 0 0 0-7h-11a3.5 3.5 0 0 1 0-7H15"/><circle cx="18" cy="5" r="3"/>',
}
MONTHS = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juill.", "août", "sept.", "oct.", "nov.", "déc."]

def load():
    return (yaml.safe_load(PATH.read_text(encoding="utf-8")) or {}).get("dossiers", [])

def fr_date(d):
    d = str(d)
    return f"{MONTHS[int(d[5:7]) - 1]} {d[:4]}" if len(d) >= 7 else d[:4]

def sources(items):
    """Liste de sources → « Sources : site1, site2 » cliquables, texte complet au survol."""
    links, seen = [], {}
    for s in items or []:
        m = URL.search(s)
        if m:
            host = urlparse(m.group()).netloc.removeprefix("www.")
            seen[host] = seen.get(host, 0) + 1
            label = host if seen[host] == 1 else f"{host} ({seen[host]})"
            links.append(f'<a href="{e(m.group())}" title="{e(s[:m.start()].rstrip(" —"))}" target="_blank" '
                         f'rel="noopener">{e(label)}</a>')
    return f'<p class="src">Sources : {", ".join(links)}</p>' if links else ""

def glossed(text, glossary):
    """Texte échappé, chaque terme du glossaire expliqué au survol (première occurrence). Une seule passe sur le
    texte : une définition qui contient elle-même un terme n'est jamais re-balisée."""
    h = e(" ".join(str(text).split()))
    if not glossary:
        return h
    terms = sorted(glossary, key=len, reverse=True)
    pattern = re.compile(r"(?<!\w)(" + "|".join(re.escape(e(t)) for t in terms) + r")(?!\w)")
    by_escaped, seen = {e(t): t for t in terms}, set()
    def tag(m):
        t = by_escaped[m.group()]
        if t in seen:
            return m.group()
        seen.add(t)
        return f'<abbr title="{e(glossary[t])}" tabindex="0">{m.group()}</abbr>'
    return pattern.sub(tag, h)

def portrait(aid, d):
    """Photo (personne), drapeau (État) ou pastille (groupe armé)."""
    a = d["actors"].get(aid, {})
    if aid in d["people"]:
        return f'<img class="pic" src="{e(d["people"][aid]["thumb"])}" alt="">'
    if a.get("kind") in ("state", "bloc"):
        return f'<img class="pic" src="https://cdn.jsdelivr.net/npm/flag-icons@7.2.3/flags/1x1/{e(aid.lower())}.svg" alt="">'
    return '<span class="pic dot"></span>'

def supporter(edge, d, g):
    a = d["actors"][edge["from"]]
    types = ", ".join(TYPES_FR.get(t, t) for t in edge["types"])
    flag = STATUS_FR.get(edge["status"])
    why = f'<p class="why"><b>Pourquoi ?</b> {glossed(edge["why"], g)}</p>' if edge.get("why") else \
          '<p class="why mute">Motivation non encore documentée.</p>'
    return f"""<div class="sup{" alleged" if edge["status"] == "alleged" else ""}">
  <div class="who">{portrait(edge["from"], d)}<div><b>{e(a["name"])}</b>
    <div class="mute">{e(types)}{f" · {e(flag)}" if flag else ""}{f" · depuis {e(fr_date(edge['since']))}" if edge.get("since") else ""}
    · {e(CONF_FR.get(edge["confidence"], ""))}</div></div></div>
  {why}{f'<p class="mute">{glossed(edge["note"], g)}</p>' if edge.get("note") else ""}{sources(edge["sources"])}</div>"""

def fractures(dos, d, g):
    """Tensions (network.yaml) qui touchent un camp, hors la guerre entre les deux camps : sanctions, autres fronts…"""
    sides = [set(s["actors"]) for s in dos["sides"]]
    main = lambda t: t["type"] == "war" and any(t["from"] in a and t["to"] in b for a in sides for b in sides if a is not b)
    ts = [t for t in d.get("tensions", []) if t["status"] != "ended" and not main(t)
          and ({t["from"], t["to"]} & set().union(*sides))]
    if not ts:
        return ""
    name = lambda a: e(d["actors"][a]["name"])
    label = {"war": "Guerre", "sanctions": "Sanctions", "claims": "Revendication territoriale", "rivalry": "Rivalité"}
    arrow = lambda t: "→" if t["type"] in ("sanctions", "claims") else "⟷"
    rows = "".join(f"""<div class="sup">{label[t["type"]]} : <b>{name(t["from"])}</b> {arrow(t)} <b>{name(t["to"])}</b>
  <span class="mute">{" · trêve ou cessez-le-feu" if t["status"] == "reduced" else ""}{f" · depuis {e(fr_date(t['since']))}" if t.get("since") else ""}</span>
  {f'<p class="mute">{glossed(t["note"], g)}</p>' if t.get("note") else ""}{sources(t["sources"])}</div>""" for t in ts)
    return f"""<h2>Les autres lignes de fracture</h2>
<p class="mute">Guerres, sanctions, revendications et rivalités qui touchent aussi les deux camps.</p>{rows}"""

SIDE_COLORS = ["#2a78d6", "#eb6834"]   # camp 1, camp 2 (palette catégorielle du site)
CONTESTED = "#9ca3af"
MAPS = Path(__file__).with_name("data") / "maps"

def hero_map(dos, d, backers):
    """Carte d'ouverture : zones de contrôle par région, soutiens étrangers en flèches vers chaque camp, lieux clés,
    routes d'approvisionnement et flux. Tout est sourcé ; les textes sont insérés côté navigateur sans HTML."""
    m = dos.get("map")
    if not m:
        return ""
    geo = d["geo"]
    arrows = []
    for side, bs in enumerate(backers):
        for x in bs:
            g = geo.get(x["from"])
            if not g or not g.get("lat"):
                continue
            arrows.append({"side": side, "at": [g["lat"], g["lon"]], "iso": x["from"].lower(),
                           "name": d["actors"][x["from"]]["name"], "alleged": x["status"] == "alleged",
                           "types": ", ".join(TYPES_FR.get(t, t) for t in x["types"]), "why": x.get("why", ""),
                           "source": x["sources"]})
    flows = [{**f, "to": [geo[f["to_actor"]]["lat"], geo[f["to_actor"]]["lon"]]} for f in m.get("flows", [])
             if geo.get(f.get("to_actor"), {}).get("lat")]
    payload = {"bounds": m["bounds"], "regions": m.get("regions"), "anchors": m["anchors"],
               "sides": [s["name"] for s in dos["sides"]], "colors": SIDE_COLORS, "contested": CONTESTED,
               "arrows": arrows, "pins": m.get("pins", []), "routes": m.get("routes", []), "flows": flows}
    data = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    reg = m.get("regions") or {}
    names = [e(s["name"]) for s in dos["sides"]]
    return f"""<section class="hero-map"><div id="dmap" role="img" aria-label="Carte du conflit : zones de contrôle, soutiens étrangers et lieux clés"></div>
<div class="legend-map">
  <span><i style="background:{SIDE_COLORS[0]}"></i>{names[0]}</span><span><i style="background:{SIDE_COLORS[1]}"></i>{names[1]}</span>
  <span><i style="background:{CONTESTED}"></i>Disputé / ligne de front</span>
  <span><b class="ln" style="border-color:{SIDE_COLORS[0]}"></b>Soutien étranger (pointillé : allégué)</span>
  <span><b class="ln dot" style="border-color:{SIDE_COLORS[1]}"></b>Route d'approvisionnement</span>
  <span><b class="ln" style="border-color:#b7791f"></b>Flux (or)</span>
</div>
<p class="src">Cliquer un élément pour son explication et sa source. {glossed(reg.get("note", ""), dos.get("glossary") or {})}</p>{sources(reg.get("sources"))}
<p class="src">Fond : Natural Earth via world-atlas ; limites des États : geoBoundaries / OCHA (CC BY 3.0 IGO) ; villes : Wikidata.</p>
</section>
<script src="https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://cdn.jsdelivr.net/npm/topojson-client@3/dist/topojson-client.min.js"></script>
<script>
(async () => {{
const M = {data};
const css = v => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
const map = L.map("dmap", {{zoomSnap:.25, scrollWheelZoom:false, attributionControl:false}});
map.fitBounds(M.bounds);
// fenêtre explicative : texte + lien vers la source, construits sans HTML venant des données
const pop = (title, text, source) => {{ const div = document.createElement("div"), b = document.createElement("b");
  b.textContent = title; div.append(b);
  if(text){{ const p = document.createElement("p"); p.style.margin = "4px 0"; p.textContent = text; div.append(p); }}
  const urls = [].concat(source || []).map(x => (x.match(/https?:\\/\\/\\S+/) || [])[0]).filter(Boolean);
  if(urls.length){{ const p = document.createElement("div"); p.textContent = urls.length > 1 ? "Sources : " : "Source : ";
    urls.forEach((u, i) => {{ const a = document.createElement("a"); a.href = u; a.target = "_blank"; a.rel = "noopener";
      a.textContent = new URL(u).hostname.replace(/^www\\./, ""); p.append(a); if(i < urls.length - 1) p.append(", "); }});
    div.append(p); }}
  return div; }};
const world = await fetch("https://cdn.jsdelivr.net/npm/world-atlas@2/countries-50m.json").then(r => r.json());
L.geoJSON(topojson.feature(world, world.objects.countries), {{interactive:false,
  style: {{color: css("--line"), weight:.8, fillColor: css("--land"), fillOpacity:1}}}}).addTo(map);
if(M.regions){{
  const control = n => M.regions.sides[0].includes(n) ? 0 : M.regions.sides[1].includes(n) ? 1 : M.regions.contested.includes(n) ? 2 : -1;
  const reg = await fetch("maps/" + M.regions.file + ".geojson").then(r => r.json());
  L.geoJSON(reg, {{style: f => {{ const c = control(f.properties.name);
      return {{color: css("--card"), weight:1, fillOpacity: c < 0 ? 0 : .55, fillColor: c === 2 ? M.contested : M.colors[c] || "transparent"}}; }},
    onEachFeature: (f, l) => {{ const c = control(f.properties.name);
      if(c >= 0) l.bindTooltip(f.properties.name + " — " + (c === 2 ? "disputé" : "tenu par " + M.sides[c].toLowerCase()), {{sticky:true}}); }}
  }}).addTo(map); }}
const curve = (a, b, k = .2) => {{ const mx = (a[0]+b[0])/2, my = (a[1]+b[1])/2, dx = b[0]-a[0], dy = b[1]-a[1], c = [mx - dy*k, my + dx*k];
  return Array.from({{length:30}}, (_, i) => {{ const t = i/29, u = 1-t; return [u*u*a[0]+2*u*t*c[0]+t*t*b[0], u*u*a[1]+2*u*t*c[1]+t*t*b[1]]; }}); }};
const head = (a, b, color) => L.circleMarker(b, {{radius:4, color, fillColor:color, fillOpacity:1, weight:0, interactive:false}}).addTo(map);
for(const f of M.flows){{
  L.polyline(curve(f.from, f.to, -.15), {{color:"#b7791f", weight:3, dashArray:"1 7", lineCap:"round"}}).bindPopup(pop(f.label, f.text, f.source)).addTo(map);
  head(f.from, f.to, "#b7791f"); }}
for(const r of M.routes){{
  const to = M.anchors[r.to];
  L.polyline(curve(r.from, to, .1), {{color:M.colors[r.to], weight:2, dashArray:"2 5"}}).bindPopup(pop(r.label, r.text, r.source)).addTo(map); }}
for(const a of M.arrows){{
  const to = M.anchors[a.side], color = M.colors[a.side];
  L.polyline(curve(a.at, to), {{color, weight: a.alleged ? 2 : 3, opacity:.9, dashArray: a.alleged ? "6 6" : null}})
    .bindPopup(pop(a.name + " → " + M.sides[a.side] + (a.alleged ? " (allégué)" : ""), a.types + (a.why ? " — Pourquoi ? " + a.why : ""), a.source)).addTo(map);
  head(a.at, to, color);
  L.marker(a.at, {{icon: L.divIcon({{className:"", iconSize:[26,26], iconAnchor:[13,13],
    html:'<img src="https://cdn.jsdelivr.net/npm/flag-icons@7.2.3/flags/1x1/' + a.iso + '.svg" alt="" class="flag">'}})}})
    .bindTooltip(a.name, {{direction:"top", offset:[0,-12]}}).bindPopup(pop(a.name + " → " + M.sides[a.side], a.types + (a.why ? " — Pourquoi ? " + a.why : ""), a.source)).addTo(map); }}
for(const p of M.pins){{
  L.circleMarker(p.at, {{radius:5, color:css("--fg"), weight:2, fillColor:css("--card"), fillOpacity:1}})
    .bindTooltip(p.label, {{permanent:true, direction: p.dir || "right", offset:[p.dir === "left" ? -6 : 6, 0], className:"pin-label"}})
    .bindPopup(pop(p.label, p.text, p.source)).addTo(map); }}
}})();
</script>"""

def markets_block(dos, d):
    """Cotes des marchés liés au dossier ; market_labels (dossiers.yaml) traduit les questions en français."""
    ms = [m for m in (d["markets"].get(dos.get("dyad"), {}) or {}).get("markets", []) if not m["stale"]]
    labels = dos.get("market_labels") or {}
    if labels:  # questions choisies dans dossiers.yaml, dans leur ordre (certaines paires ont des dizaines de marchés)
        by_q = {m["question"]: m for m in ms}
        ms = [by_q[q] for q in labels if q in by_q]
    if not ms:
        return '<p class="mute">Aucun marché de prédiction ne porte aujourd\'hui sur ce conflit.</p>'
    rows = "".join(
        f'<div class="mkt"><b>{round(m["prob"] * 100)} %</b><div>{e(labels.get(m["question"], m["question"]))}'
        f'<div class="mute">Question d\'origine : « {e(m["question"])} »</div>'
        f'<div class="mute">{e(m["source"].capitalize())}'
        f'{f", {m["delta_pts"]:+.0f} pts en 7 jours" if m.get("delta_pts") is not None else ""}'
        f' — <a href="{e(m["url"])}" target="_blank" rel="noopener">voir le marché</a></div></div></div>' for m in ms[:4])
    return f"""<p>Sur les marchés de prédiction, des parieurs misent de l'argent sur ce qui va se passer. Le prix d'une
mise se lit comme une probabilité : c'est ce que <i>la foule des parieurs</i> anticipe, pas une certitude, et {e(brand.NAME)}
ne calcule rien lui-même.</p>{rows}"""

def page(dos, d):
    g = dos.get("glossary") or {}
    edges = d["edges"]
    side_ids = [set(s["actors"]) for s in dos["sides"]]
    backers = [[x for x in edges if x["to"] in ids and x["from"] not in ids and x["status"] != "ended"]
               for ids in side_ids]
    for bs in backers:
        bs.sort(key=lambda x: ({"high": 0, "medium": 1, "low": 2}[x["confidence"]], d["actors"][x["from"]]["name"]))

    def side_card(s, bs):
        lead = next((ld for a in s["actors"] if (ld := network.leader(d["actors"], a))), None)
        pic = d["people"].get(lead["photo_key"]) if lead else None
        return f"""<div class="side">
  <div class="who big">{f'<img class="pic" src="{e(pic["thumb"])}" alt="">' if pic else portrait(s["actors"][0], d)}
  <div><h3>{glossed(s["name"], g)}</h3>
  {f'<div class="mute">Dirigeant : {e(lead["name"])}</div>' if lead else ""}</div></div>
  <p>{glossed(s["text"], g)}</p>{sources(s.get("sources"))}
  <h4>Ses soutiens étrangers ({len(bs)})</h4>{"".join(supporter(x, d, g) for x in bs) or '<p class="mute">Aucun soutien documenté.</p>'}</div>"""

    # frise : événements du dossier + débuts de soutien datés dans le graphe
    events = [(str(t["date"]), glossed(t["text"], g), sources([t["source"]])) for t in dos.get("timeline", [])]
    for bs, s in zip(backers, dos["sides"]):
        # since = plus ancienne date documentée par les sources, pas forcément le vrai début ; une ligne par date et par camp
        by_date = {}
        for x in bs:
            if x.get("since"):
                by_date.setdefault(str(x["since"]), []).append(x)
        side = e(s["name"][:1].lower() + s["name"][1:])
        for dt, xs in by_date.items():
            names = [e(d["actors"][x["from"]]["name"]) for x in xs]
            who = names[0] if len(names) == 1 else ", ".join(names[:-1]) + " et " + names[-1]
            what = f"premier soutien documenté à {side}" if len(xs) == 1 else f"premiers soutiens documentés à {side}"
            events.append((dt, f"{who} : {what}", sources([x["sources"][0] for x in xs])))
    events.sort(key=lambda ev: ev[0])
    keys = [ld["photo_key"] for s in dos["sides"] for a in s["actors"] if (ld := network.leader(d["actors"], a))]
    credits = [d["people"][k] for k in keys if k in d["people"]]

    return f"""<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(dos["title"])} — {e(brand.NAME)}</title>
<style>
:root{{--bg:#fafaf8;--fg:#1c1c1c;--mute:#6b6b6b;--line:#e3e3df;--card:#fff;--accent:#2b6cb0;--warn:#b7791f;--ocean:#dde6ec;--land:#f4f2ec}}
@media (prefers-color-scheme:dark){{:root{{--bg:#141414;--fg:#eee;--mute:#9a9a9a;--line:#2c2c2c;--card:#1d1d1d;--accent:#7aa7e0;--warn:#d69e2e;--ocean:#10171c;--land:#262626}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--fg);font:16px/1.6 system-ui,sans-serif}}
main{{max-width:980px;margin:0 auto;padding:20px 16px 64px}}a{{color:var(--accent)}}
h1{{font-size:30px;line-height:1.2;margin:12px 0 8px}}h2{{font-size:20px;margin:40px 0 12px;padding-top:12px;border-top:1px solid var(--line)}}
h3{{font-size:18px;margin:0}}h4{{font-size:13px;text-transform:uppercase;letter-spacing:.05em;color:var(--mute);margin:18px 0 8px}}
.lede{{font-size:19px;line-height:1.55;max-width:760px}}.mute{{color:var(--mute);font-size:13px}}
.src{{color:var(--mute);font-size:12px;margin:4px 0 0}}.src a{{color:inherit}}
abbr{{text-decoration:underline dotted;cursor:help}}
.sides{{display:grid;grid-template-columns:1fr auto 1fr;gap:16px;align-items:start}}
.vs{{align-self:center;font-weight:700;color:var(--mute);font-size:14px;padding-top:40px}}
@media (max-width:760px){{.sides{{grid-template-columns:1fr}}.vs{{padding:0;text-align:center}}}}
.side{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px}}
.who{{display:flex;gap:10px;align-items:center}}.pic{{width:36px;height:36px;border-radius:50%;object-fit:cover;flex:none;background:var(--line)}}
.big .pic{{width:56px;height:56px}}.dot{{display:inline-block;background:#d64545}}
.sup{{border-top:1px solid var(--line);padding:10px 0}}.sup.alleged .who b::after{{content:" *";color:var(--warn)}}
.why{{margin:6px 0 2px;font-size:15px}}
.stakes{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}}
.stake{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px}}
.stake svg{{width:24px;height:24px;stroke:var(--accent)}}.stake b{{display:block;margin:4px 0}}
.tl{{list-style:none;padding:0;margin:0;border-left:2px solid var(--line)}}.tl li{{position:relative;padding:0 0 14px 18px}}
.tl li::before{{content:"";position:absolute;left:-6px;top:7px;width:10px;height:10px;border-radius:50%;background:var(--accent)}}
.tl time{{font-weight:600;font-variant-numeric:tabular-nums;margin-right:6px}}.tl .src{{display:inline;margin-left:6px}}
.mkt{{display:grid;grid-template-columns:64px 1fr;gap:10px;padding:10px 0;border-top:1px solid var(--line)}}
.mkt>b{{font-size:24px;font-variant-numeric:tabular-nums}}
.box{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 16px}}
.hero-map{{margin:24px 0 8px}}#dmap{{height:min(62vh,560px);border:1px solid var(--line);border-radius:12px;background:var(--ocean)}}
.legend-map{{display:flex;flex-wrap:wrap;gap:6px 16px;font-size:13px;margin:10px 0 2px}}.legend-map span{{display:inline-flex;align-items:center;gap:6px}}
.legend-map i{{width:14px;height:14px;border-radius:3px;opacity:.75}}.legend-map .ln{{width:22px;border-top:3px solid}}.legend-map .ln.dot{{border-top-style:dotted}}
.flag{{width:24px;height:24px;border-radius:50%;box-shadow:0 0 0 2px var(--card),0 1px 4px #0006}}
.leaflet-container{{font:inherit;background:var(--ocean)}}.leaflet-popup-content{{font-size:14px;line-height:1.45;max-width:280px}}
.leaflet-tooltip.pin-label{{background:transparent;border:0;box-shadow:none;font-weight:600;color:var(--fg);text-shadow:0 0 3px var(--bg),0 0 3px var(--bg)}}
.leaflet-tooltip.pin-label::before{{display:none}}
</style>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.css">
</head><body><main>
<p class="mute"><a href="index.html">← {e(brand.NAME)}</a> · <a href="index.html#conflits">Tous les conflits</a> · <a href="explorer.html">Explorer le graphe et la carte</a></p>
<h1>{e(dos["title"])}</h1>
<p class="mute">Depuis {e(fr_date(dos["since"]))} · dossier vérifié en {e(fr_date(dos["verified"]))} · termes soulignés en pointillés : survoler pour une définition</p>
<p class="lede">{glossed(dos["lede"], g)}</p>{sources(dos.get("lede_sources"))}
{hero_map(dos, d, backers)}

<h2>Qui s'affronte, et qui les soutient</h2>
<div class="sides">{side_card(dos["sides"][0], backers[0])}<div class="vs">contre</div>{side_card(dos["sides"][1], backers[1])}</div>
<p class="mute">* soutien allégué : démenti par l'intéressé ou pas encore prouvé. Le « pourquoi » est une analyse,
attribuée à qui la formule (think tank, ONU, presse). Détail des types de preuve : <a href="methode.html">méthode et sources</a>.</p>

{fractures(dos, d, g)}

<h2>Ce qui est en jeu</h2>
<div class="stakes">{"".join(f'''<div class="stake"><svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round"
  stroke-linejoin="round" aria-hidden="true">{ICONS.get(s.get("icon"), "")}</svg><b>{e(s["label"])}</b>
  <div>{glossed(s["text"], g)}</div>{sources(s.get("sources"))}</div>''' for s in dos.get("stakes", []))}</div>

<h2>Le coût humain</h2>
<div class="box"><p>{glossed(dos["toll"]["text"], g)}</p>{sources(dos["toll"].get("sources"))}</div>

<h2>Comment on en est arrivé là</h2>
<p>{glossed(dos["origins"]["text"], g)}</p>{sources(dos["origins"].get("sources"))}
<ul class="tl">{"".join(f'<li><time>{e(fr_date(dt))}</time>{txt}{src}</li>' for dt, txt, src in events)}</ul>

{f"""<h2>Ce que l'histoire éclaire, et ses limites</h2>
<div class="box"><p>{glossed(dos["history"]["text"], g)}</p>{sources(dos["history"].get("sources"))}</div>""" if dos.get("history") else ""}

<h2>Où en est-on</h2>
<p>{glossed(dos["now"]["text"], g)}</p>{sources(dos["now"].get("sources"))}

<h2>Ce qu'anticipent les parieurs</h2>
{markets_block(dos, d)}

<p class="mute" style="margin-top:40px">Photos : {"; ".join(f'<a href="{e(c["page"])}">{e(c["artist"] or "auteur inconnu")}</a> ({e(c["license"])})' for c in credits) or "—"},
via Wikimedia Commons. Icônes <a href="https://lucide.dev">Lucide</a> (ISC). Texte et données CC BY 4.0 —
<a href="{brand.REPO}">corriger ou compléter sur GitHub</a>.</p>
</main></body></html>"""

def write(out, data):
    dossiers = load()
    if MAPS.exists():  # contours régionaux utilisés par les cartes des dossiers
        (out / "maps").mkdir(exist_ok=True)
        for f in MAPS.glob("*.geojson"):
            shutil.copy(f, out / "maps" / f.name)
    for dos in dossiers:
        (out / f"{dos['id']}.html").write_text(page(dos, data), encoding="utf-8")
    return dossiers
