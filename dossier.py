"""Pages « dossier » (site/<id>.html) : un conflit expliqué à quelqu'un qui n'y connaît rien.
Le récit vient de dossiers.yaml ; les camps, leurs soutiens et le « pourquoi » de chaque soutien viennent de
network.yaml, pour qu'un dossier ne puisse pas contredire le graphe. Le site n'affiche aucune probabilité."""
from html import escape as e
from pathlib import Path
from urllib.parse import urlparse
import json, re, shutil
import yaml
import brand, glossary, network, style

PATH = Path(__file__).with_name("dossiers.yaml")
URL = re.compile(r"https?://\S+")
TYPES_FR = {"arms": "armes", "financial": "argent", "training": "entraînement", "troops": "troupes",
            "intelligence": "renseignement", "political": "soutien politique", "economic": "soutien économique",
            "dual_use": "matériel à double usage"}
MONTHS = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juill.", "août", "sept.", "oct.", "nov.", "déc."]


CSS = """
header.doc{padding:72px 0 28px;max-width:760px}.doc .meta{margin:0 0 26px}
.hero-map{margin:8px 0 0}#dmap{height:min(68vh,620px);border-radius:3px;background:var(--ocean)}
.legend-map{display:flex;flex-wrap:wrap;gap:4px 22px;font-size:14px;color:var(--graphite);margin:14px 0 6px}
.legend-map span{display:inline-flex;align-items:center;gap:7px}.legend-map i{width:12px;height:12px;border-radius:2px;opacity:.8}
.legend-map .ln{width:20px;border-top:2px solid}.legend-map .ln.dot{border-top-style:dotted}
.map-note{font-size:14px;color:var(--graphite);margin:0 0 4px;max-width:64em}
.flag{width:22px;height:22px;border-radius:50%;box-shadow:0 0 0 2px var(--land)}
.leaflet-container{font:inherit;background:var(--ocean)}
.leaflet-popup-content-wrapper{border-radius:3px;box-shadow:0 2px 10px #0002}.leaflet-popup-content{font-size:14px;line-height:1.5;max-width:280px}
.leaflet-tooltip.pin-label{background:transparent;border:0;box-shadow:none;font:500 13px var(--sans);color:var(--ink);
  text-shadow:0 0 3px var(--land),0 0 3px var(--land),0 0 3px var(--land)}.leaflet-tooltip.pin-label::before{display:none}
.camps{display:grid;grid-template-columns:1fr 1fr;gap:16px;align-items:start}
.camp{border-top:3px solid var(--c);border-radius:4px 4px 6px 6px}
.camp .who{display:flex;gap:14px;align-items:center;margin-bottom:12px}
.camp .who img{width:52px;height:52px;border-radius:50%;object-fit:cover}
.camp h3{font-size:21px;margin:0}.camp .lead{color:var(--graphite);font-size:15px}
.camp > p{margin:0 0 20px;font-size:16px}
.backers-title{font-size:15px;color:var(--graphite);margin:0 0 4px}
.backer{display:grid;grid-template-columns:22px 1fr;gap:4px 12px;padding:12px 0;border-top:1px solid var(--mist)}
.backer img{width:22px;height:22px;border-radius:50%;margin-top:2px}
.backer .name{font-weight:600}.backer .kind{color:var(--graphite);font-size:14px;margin-left:6px}
.backer .why{grid-column:2;font-size:15.5px;line-height:1.55}
.backer details{grid-column:2;font-size:14px;color:var(--graphite)}.backer summary{cursor:pointer;width:max-content}
.backer details p{margin:6px 0 0}
.alleged{font-size:13px;color:var(--c);border:1px solid currentColor;border-radius:9px;padding:0 6px;margin-left:6px}
.frac .intro{margin:-8px 0 14px}.frac .card{padding:6px 24px}.frac .row{padding:14px 0;border-top:1px solid var(--mist)}.frac .row:first-child{border-top:0}
.frac .row p{margin:4px 0 0;color:var(--graphite);font-size:15px}
.stakes{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px}
.stake h3{font-size:19px;margin-bottom:6px}.stake p{margin:0;font-size:16px}
.block p{margin:0;max-width:44em}.block p + p{margin-top:12px}.pair{display:grid;grid-template-columns:1fr 1fr;gap:16px}.pair>div{display:flex;flex-direction:column}.pair .card{flex:1}
.tl{list-style:none;margin:18px 0 0;padding:16px 0 0;border-top:1px solid var(--mist)}
.tl li{display:grid;grid-template-columns:104px 1fr;gap:16px;padding:7px 0}
.tl time{white-space:nowrap;color:var(--graphite);font-variant-numeric:tabular-nums;font-size:15px}
@media (max-width:760px){header.doc{padding:44px 0 22px}.camps,.pair{grid-template-columns:1fr}.card{padding:18px}
  .tl li{grid-template-columns:88px 1fr;gap:10px}#dmap{height:62vh}}
"""

def load():
    return (yaml.safe_load(PATH.read_text(encoding="utf-8")) or {}).get("dossiers", [])

def fr_date(d):
    d = str(d)
    return f"{MONTHS[int(d[5:7]) - 1]} {d[:4]}" if len(d) >= 7 else d[:4]

def glossed(text, g):
    """Texte échappé, termes du glossaire du site expliqués (première occurrence dans la page) : voir glossary.py."""
    return g(text)

class Notes:
    """Sources → appels de note numérotés (dédoublonnés par URL), listés en bas de page."""
    def __init__(self):
        self.items, self.index = [], {}
    def __call__(self, srcs):
        marks = []
        for s in srcs or []:
            m = URL.search(s)
            key = m.group() if m else s
            if key not in self.index:
                self.items.append(s)
                self.index[key] = len(self.items)
            n = self.index[key]
            title = s[:m.start()].rstrip(" —") if m else s
            if not any(f'href="#n{n}"' in x for x in marks):
                marks.append(f'<a href="#n{n}" title="{e(title)}">{n}</a>')
        return f'<sup class="fns">{",".join(marks)}</sup>' if marks else ""
    def html(self):
        def item(i, s):
            m = URL.search(s)
            if not m:
                return f'<li id="n{i}">{e(s)}</li>'
            label = s[:m.start()].rstrip(" —")
            return f'<li id="n{i}">{e(label)}, <a href="{e(m.group())}" target="_blank" rel="noopener">{e(urlparse(m.group()).netloc.removeprefix("www."))}</a></li>'
        return "".join(item(i, s) for i, s in enumerate(self.items, 1))

def flag(aid, d):
    kind = d["actors"][aid]["kind"]
    code = aid.lower() if kind == "state" else "eu" if aid == "EU" else None
    return f'<img src="https://cdn.jsdelivr.net/npm/flag-icons@7.2.3/flags/1x1/{code}.svg" alt="">' if code else '<span></span>'

def backers_block(bs, d, g, cite):
    """Une ligne par soutien ; ceux qui partagent le même « pourquoi » sont regroupés sur une ligne."""
    groups = {}
    for x in bs:
        groups.setdefault(x.get("why") or x["from"], []).append(x)
    rows = []
    for why, xs in groups.items():
        names = [e(d["actors"][x["from"]]["name"]) for x in xs]
        kinds = sorted({TYPES_FR.get(t, t) for x in xs for t in x["types"]})
        alleged = any(x["status"] == "alleged" for x in xs)
        notes = [x for x in xs if x.get("note")]
        srcs = [s for x in xs for s in x["sources"]]
        rows.append(f"""<div class="backer">{flag(xs[0]["from"], d) if len(xs) == 1 else flag("EU", d) if any(x["from"] == "EU" for x in xs) else flag(xs[0]["from"], d)}
  <div><span class="name">{", ".join(names)}</span><span class="kind">{e(", ".join(kinds))}</span>{'<span class="alleged">allégué</span>' if alleged else ""}</div>
  <div class="why">{glossed(xs[0]["why"], g) if xs[0].get("why") else '<span style="color:var(--graphite)">Motivation pas encore documentée.</span>'}{cite(srcs)}</div>
  {f'<details><summary>Détails</summary>{"".join(f"<p>{glossed(x['note'], g)}</p>" for x in notes)}</details>' if notes else ""}</div>""")
    return "".join(rows)

def fractures(dos, d, g, cite):
    """Tensions (network.yaml) qui touchent un camp, hors la guerre entre les deux camps : sanctions, autres fronts…"""
    sides = [set(s["actors"]) for s in dos["sides"]]
    main = lambda t: t["type"] == "war" and any(t["from"] in a and t["to"] in b for a in sides for b in sides if a is not b)
    ts = [t for t in d.get("tensions", []) if t["status"] != "ended" and not main(t)
          and ({t["from"], t["to"]} & set().union(*sides))]
    if not ts:
        return ""
    name = lambda a: e(d["actors"][a]["name"])
    label = {"war": "Guerre", "sanctions": "Sanctions", "claims": "Revendication territoriale", "rivalry": "Rivalité"}
    link = lambda t: f"{name(t['from'])} {'→' if t['type'] in ('sanctions', 'claims') else 'et'} {name(t['to'])}"
    when = lambda t: ", ".join(x for x in (f"depuis {fr_date(t['since'])}" if t.get("since") else "",
                                            "trêve ou cessez-le-feu" if t["status"] == "reduced" else "") if x)
    rows = "".join(f"""<div class="row"><div><b>{label[t["type"]]}</b> {link(t)}{f'<span class="quiet">, {e(when(t))}</span>' if when(t) else ""}</div>
  {f'<p>{glossed(t["note"], g)}{cite(t["sources"])}</p>' if t.get("note") else cite(t["sources"])}</div>""" for t in ts)
    return f"""<h2>Les autres lignes de fracture</h2>
<p class="quiet intro">Guerres, sanctions, revendications et rivalités qui touchent aussi les deux camps.</p><div class="card">{rows}</div>"""

SIDE_COLORS = ["#2a78d6", "#eb6834"]   # camp 1, camp 2 (palette catégorielle du site)
CONTESTED = "#9ca3af"
MAPS = Path(__file__).with_name("data") / "maps"

def hero_map(dos, d, backers, cite):
    """Carte d'ouverture : zones de contrôle par région, soutiens étrangers en flèches vers chaque camp, lieux clés,
    routes d'approvisionnement et flux. Tout est sourcé ; les textes sont insérés côté navigateur sans HTML."""
    m = dos.get("map")
    if not m:
        return ""
    geo = d["geo"]
    (s_lat, w_lon), (n_lat, e_lon) = m["bounds"]
    def place(aid):
        """Position d'un soutien : son pays (Wikidata) ou les coords d'un bloc ; ramenée au bord du cadre si elle en sort,
        pour garder la région du conflit lisible (le nom le signale alors « hors carte »)."""
        g = geo.get(aid) or {}
        lat, lon = (g.get("lat"), g.get("lon")) if g.get("lat") else (d["actors"][aid].get("coords") or [None, None])
        if lat is None:
            return None, False
        inset = 1.5
        c = [min(max(lat, s_lat + inset), n_lat - inset), min(max(lon, w_lon + inset), e_lon - inset)]
        return c, c != [lat, lon]
    arrows, taken = [], []
    for side, bs in enumerate(backers):
        for x in bs:
            at, off = place(x["from"])
            if not at:
                continue
            # deux drapeaux ramenés au même endroit du bord : on décale le second le long du bord
            while off and any(abs(at[0] - t[0]) < 2 and abs(at[1] - t[1]) < 3 for t in taken):
                at = [at[0], at[1] - 3.5] if at[0] <= s_lat + 1.6 or at[0] >= n_lat - 1.6 else [at[0] - 2.5, at[1]]
            taken.append(at)
            flag = x["from"].lower() if d["actors"][x["from"]]["kind"] == "state" else ("eu" if x["from"] == "EU" else "")
            arrows.append({"side": side, "at": at, "iso": flag,
                           "name": d["actors"][x["from"]]["name"] + (" (hors carte)" if off else ""), "alleged": x["status"] == "alleged",
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
  {f'<span><i style="background:{CONTESTED}"></i>{e(reg.get("contested_label", "Disputé / ligne de front"))}</span>' if reg.get("contested") else ""}
  <span><b class="ln" style="border-color:{SIDE_COLORS[0]}"></b>Soutien étranger (pointillé : allégué)</span>
  {f'<span><b class="ln dot" style="border-color:{SIDE_COLORS[1]}"></b>Route d\'approvisionnement</span>' if m.get("routes") else ""}
  {'<span><b class="ln" style="border-color:#b7791f"></b>Flux (or)</span>' if m.get("flows") else ""}
</div>
<p class="map-note">Cliquez sur un élément pour son explication et ses sources. {glossed(reg.get("note", ""), glossary.Glosser())}{cite(reg.get("sources"))}</p>
<p class="map-note">Fond de carte Natural Earth ; {e(reg.get("credit", ""))} ; villes : Wikidata.</p>
</section>
<script src="https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://cdn.jsdelivr.net/npm/topojson-client@3/dist/topojson-client.min.js"></script>
<script>
(async () => {{
const M = {data};
window.THEME_RELOAD = true;  // couleurs de la carte lues au chargement
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
      if(c >= 0) l.bindTooltip(f.properties.name + " — " + (c === 2 ? (M.regions.contested_label || "disputé").toLowerCase() : "tenu par " + M.sides[c].toLowerCase()), {{sticky:true}}); }}
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

def page(dos, d):
    g, cite = glossary.Glosser(), Notes()
    sides = [set(s["actors"]) for s in dos["sides"]]
    backers = [[x for x in d["edges"] if x["to"] in ids and x["from"] not in ids and x["status"] != "ended"] for ids in sides]
    for bs in backers:
        bs.sort(key=lambda x: ({"high": 0, "medium": 1, "low": 2}[x["confidence"]], d["actors"][x["from"]]["name"]))

    def camp(i, s, bs):
        lead = next((ld for a in s["actors"] if (ld := network.leader(d["actors"], a))), None)
        pic = d["people"].get(lead["photo_key"]) if lead else None
        return f"""<div class="card camp" style="--c:var(--{'ab'[i]})">
  <div class="who">{f'<img src="{e(pic["thumb"])}" alt="">' if pic else ""}<div><h3>{glossed(s["name"], g)}</h3>
  {f'<div class="lead">{e(lead["name"])}</div>' if lead else ""}</div></div>
  <p>{glossed(s["text"], g)}{cite(s.get("sources"))}</p>
  <p class="backers-title">{len(bs)} soutien{"s" if len(bs) > 1 else ""} étranger{"s" if len(bs) > 1 else ""}</p>
  {backers_block(bs, d, g, cite) or '<p style="color:var(--graphite)">Aucun soutien documenté.</p>'}</div>"""

    events = [(str(t["date"]), glossed(t["text"], g) + cite([t["source"]])) for t in dos.get("timeline", [])]
    for bs, s in zip(backers, dos["sides"]):
        by_date = {}
        for x in bs:
            if x.get("since"):
                by_date.setdefault(str(x["since"]), []).append(x)
        for dt, xs in by_date.items():
            names = [e(d["actors"][x["from"]]["name"]) for x in xs]
            who = names[0] if len(names) == 1 else ", ".join(names[:-1]) + " et " + names[-1]
            what = "premier soutien documenté" if len(xs) == 1 else "premiers soutiens documentés"
            events.append((dt, f"{who} : {what} à {e(s['name'][:1].lower() + s['name'][1:])}" + cite([xs[0]["sources"][0]])))
    events.sort(key=lambda ev: ev[0])

    frac = fractures(dos, d, g, cite)
    credits = [d["people"][ld["photo_key"]] for s in dos["sides"] for a in s["actors"]
               if (ld := network.leader(d["actors"], a)) and ld["photo_key"] in d["people"]]

    body = f"""<div class="wrap">
{style.top(f"{dos['id']}.html")}

<header class="doc"><h1>{e(dos["title"])}</h1>
<p class="meta">Depuis {e(fr_date(dos["since"]))}. Dossier vérifié en {e(fr_date(dos["verified"]))}. Les mots soulignés en pointillés ont une définition au survol.</p>
<p class="lede">{glossed(dos["lede"], g)}{cite(dos.get("lede_sources"))}</p></header>

{hero_map(dos, d, backers, cite)}

<section class="s"><h2>Qui s'affronte, et qui les soutient</h2>
<div class="camps">{camp(0, dos["sides"][0], backers[0])}{camp(1, dos["sides"][1], backers[1])}</div></section>

{f'<section class="s frac">{frac}</section>' if frac else ""}

<section class="s"><h2>Ce qui est en jeu</h2><div class="stakes">{"".join(
  f'<div class="card stake"><h3>{e(s["label"])}</h3><p>{glossed(s["text"], g)}{cite(s.get("sources"))}</p></div>' for s in dos.get("stakes", []))}</div></section>

<section class="s pair">
<div><h2>Le coût humain</h2><div class="card block"><p>{glossed(dos["toll"]["text"], g)}{cite(dos["toll"].get("sources"))}</p></div></div>
<div><h2>Où en est-on</h2><div class="card block"><p>{glossed(dos["now"]["text"], g)}{cite(dos["now"].get("sources"))}</p></div></div>
</section>

<section class="s"><h2>Comment on en est arrivé là</h2>
<div class="card block"><p>{glossed(dos["origins"]["text"], g)}{cite(dos["origins"].get("sources"))}</p>
<ol class="tl">{"".join(f"<li><time>{e(fr_date(dt))}</time><span>{txt}</span></li>" for dt, txt in events)}</ol></div></section>

{f'<section class="s"><h2>Ce que l’histoire éclaire, et ses limites</h2><div class="card block"><p>{glossed(dos["history"]["text"], g)}{cite(dos["history"].get("sources"))}</p></div></section>' if dos.get("history") else ""}

<section class="notes"><h2>Sources</h2><ol>{cite.html()}</ol>
<p class="fix">Une erreur, une source manquante, une information dépassée ? {style.correction(dos["title"])}</p></section>
</div>
{style.foot(f'Photos {"; ".join(f"""<a href="{e(c['page'])}">{e(c['artist'] or 'auteur inconnu')}</a>, {e(c['license'])}""" for c in credits)}, via Wikimedia Commons. ' if credits else "", dos["title"])}"""
    extra = f'<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.css"><style>{CSS}</style>'
    return style.head(f"{dos['title']} — {brand.NAME}", " ".join(dos["lede"].split())[:180], extra) + f"<body>{body}</body></html>"

def write(out, data):
    dossiers = load()
    if MAPS.exists():  # contours régionaux utilisés par les cartes des dossiers
        (out / "maps").mkdir(exist_ok=True)
        for f in MAPS.glob("*.geojson"):
            shutil.copy(f, out / "maps" / f.name)
    for dos in dossiers:
        (out / f"{dos['id']}.html").write_text(page(dos, data), encoding="utf-8")
    return dossiers
