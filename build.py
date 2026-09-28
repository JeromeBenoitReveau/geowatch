"""python build.py → site/ : graphe interactif + fiches pays + cotes de marché (index.html),
et le graphe en données ouvertes (network.json, network.csv — CC BY 4.0). Publiable tel quel."""
from dotenv import load_dotenv; load_dotenv()
import csv, json
from pathlib import Path
import db, network, track
from config import DYADS, MOVE_ALERT_PTS

OUT = Path("site")
DATA_LICENSE = "CC BY 4.0 — https://creativecommons.org/licenses/by/4.0/ — geowatch network.yaml"
TYPE_COLORS = {"arms": "#d64545", "troops": "#8b1e1e", "financial": "#2f8f5b", "training": "#c98a1b",
               "intelligence": "#6b4fbb", "political": "#3a6fd8", "economic": "#1f9aa5", "dual_use": "#b0569a"}

def export_data(actors, edges):
    (OUT / "network.json").write_text(json.dumps(
        {"license": DATA_LICENSE, "generated_at": db.now(), "actors": actors, "edges": edges},
        ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    with open(OUT / "network.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["from", "from_name", "to", "to_name", "types", "status", "confidence",
                    "sources", "verified", "note"])
        for e in edges:
            w.writerow([e["from"], network.name(actors, e["from"]), e["to"], network.name(actors, e["to"]),
                        ";".join(e["types"]), e["status"], e["confidence"], " | ".join(e["sources"]),
                        e["verified"], e.get("note", "")])

def build():
    actors, edges = network.load()
    c = db.conn()
    profiles = {}
    for aid, a in actors.items():
        iso = aid if a["kind"] in ("state", "bloc") else a.get("base")
        if iso:
            p, fetched = db.get_profile(c, iso)
            if p:
                profiles[iso] = {**p, "fetched_at": fetched}
    markets = {name: {"countries": d["countries"], "markets": track.summary(name)}
               for name, d in DYADS.items()}
    OUT.mkdir(exist_ok=True)
    aligns = network.alignments()
    data = {"actors": actors, "edges": edges, "profiles": profiles, "colors": TYPE_COLORS,
            "align": aligns, "influence": network.influence(actors, edges, aligns), "geo": db.load_geo(), "people": db.load_people(),
            "markets": markets, "alert": MOVE_ALERT_PTS, "built": db.now()}
    html = TEMPLATE.replace("__DATA__", json.dumps(data, ensure_ascii=False, default=str)
                            .replace("</", "<\\/"))
    (OUT / "index.html").write_text(html, encoding="utf-8")
    export_data(actors, edges)
    print(f"→ {OUT}/index.html, network.json, network.csv")

TEMPLATE = r"""<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>geowatch — réseau de soutiens</title>
<script src="https://cdn.jsdelivr.net/npm/vis-network@10.1.2/standalone/umd/vis-network.min.js"></script>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.css">
<script src="https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://cdn.jsdelivr.net/npm/topojson-client@3/dist/topojson-client.min.js"></script>
<style>
:root{--bg:#fafaf8;--fg:#1c1c1c;--mute:#6b6b6b;--line:#e3e3df;--card:#fff;--ocean:#dde6ec;--land:#f4f2ec;--land-hl:#e2dccb}
@media (prefers-color-scheme:dark){:root{--bg:#141414;--fg:#eee;--mute:#9a9a9a;--line:#2c2c2c;--card:#1d1d1d;--ocean:#10171c;--land:#262626;--land-hl:#3a3528}}
*{box-sizing:border-box}body{margin:0;font:14px/1.45 system-ui,sans-serif;background:var(--bg);color:var(--fg);
display:grid;grid-template-columns:1fr 380px;height:100vh}
@media (max-width:800px){body{grid-template-columns:1fr;grid-template-rows:60vh auto;height:auto}}
#stage{position:relative;border-right:1px solid var(--line);min-height:60vh}#graph{position:absolute;inset:0}
#controls{position:absolute;top:10px;left:10px;z-index:1000;background:var(--card);border:1px solid var(--line);
border-radius:8px;padding:8px 10px;font-size:12px;display:flex;flex-direction:column;gap:4px;max-width:calc(100% - 20px)}
#controls select{font:inherit;background:var(--card);color:var(--fg);border:1px solid var(--line);border-radius:4px}
#views{position:absolute;top:10px;right:10px;z-index:1000;display:flex;border:1px solid var(--line);border-radius:8px;overflow:hidden}
#views button{font:inherit;font-size:12px;padding:6px 12px;border:0;background:var(--card);color:var(--fg);cursor:pointer}
#views button[aria-pressed=true]{background:var(--fg);color:var(--bg)}
#map{position:absolute;inset:0;display:none;background:var(--ocean)}
body.map #map{display:block}body.map #graph,body.map .graph-only{display:none}
.leaflet-container{background:var(--ocean);font:inherit}
.leaflet-control-layers,.leaflet-bar a,.leaflet-tooltip{background:var(--card);color:var(--fg);border-color:var(--line)}
.mk{display:flex;align-items:center;justify-content:center;cursor:pointer}
.mk img{width:100%;height:100%;border-radius:50%;box-shadow:0 0 0 1.5px var(--card),0 1px 4px #0006}
.mk i{display:block;width:12px;height:12px;background:#6b4fbb;box-shadow:0 0 0 1.5px var(--card)}
.mk.non_state i{background:#d64545;transform:rotate(45deg)}.mk.party i{background:#6b4fbb}
.mk.person i{background:#6b4fbb;clip-path:polygon(50% 0,100% 100%,0 100%);box-shadow:none;width:14px;height:13px}
aside{padding:20px;overflow:auto}
h1{font-size:20px;margin:0 0 4px}h2{font-size:12px;text-transform:uppercase;letter-spacing:.06em;color:var(--mute);margin:20px 0 6px}
.kv{display:grid;grid-template-columns:140px 1fr;gap:3px 10px}.kv span:nth-child(odd){color:var(--mute)}
.rel{padding:6px 0;border-bottom:1px solid var(--line)}.rel b{cursor:pointer}
.tag{display:inline-block;font-size:11px;padding:1px 6px;border-radius:9px;color:#fff;margin:2px 2px 0 0}
.mute{color:var(--mute);font-size:12px}.legend .tag{margin-right:4px}
.mkt{padding:6px 0;border-bottom:1px solid var(--line);display:grid;grid-template-columns:52px 1fr 80px;gap:8px;align-items:center}
.mkt .p{font-weight:600;font-variant-numeric:tabular-nums}.mkt a{color:inherit}.up{color:#c0392b}.down{color:#2f8f5b}
.spark{width:80px;height:22px}.spark polyline{fill:none;stroke:currentColor;stroke-width:1.5}
</style></head><body>
<div id="stage"><div id="graph"></div><div id="map"></div>
<div id="views"><button id="v-graph" aria-pressed="true">Graphe</button><button id="v-map" aria-pressed="false">Carte</button></div>
<div id="controls">
  <label>Taille des acteurs : <select id="metric">
    <option value="military">dépenses militaires ($)</option><option value="gdp">PIB ($)</option>
    <option value="supports">nombre de soutiens accordés</option></select></label>
  <label class="graph-only"><input type="checkbox" id="lyr-armed" checked> Groupes armés non étatiques</label>
  <label class="graph-only"><input type="checkbox" id="lyr-detail"> Partis & personnalités</label>
</div></div>
<aside id="panel"></aside>
<script>
const D = __DATA__;
const $ = s => document.querySelector(s);
const esc = v => String(v ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const safeUrl = u => /^https?:\/\//.test(u||"") ? esc(u) : "#";
const nm = id => esc((D.actors[id]||{}).name || id);
const KIND = {state:"État", non_state:"acteur armé non étatique", bloc:"bloc", party:"parti politique", person:"personnalité"};
const SHAPE = {non_state:"diamond", party:"square", person:"triangle"};
const DETAIL = new Set(["party","person"]);
const flag = id => `https://cdn.jsdelivr.net/npm/flag-icons@7.2.3/flags/1x1/${id.toLowerCase()}.svg`;
const CONTESTED = "#c98a1b";
// Icônes Lucide (ISC) inlinées : épées = groupe armé, urne = parti, silhouette = personne sans photo
const GLYPH = {
  non_state: '<polyline points="14.5 17.5 3 6 3 3 6 3 17.5 14.5"/><line x1="13" x2="19" y1="19" y2="13"/><line x1="16" x2="20" y1="16" y2="20"/><line x1="19" x2="21" y1="21" y2="19"/><polyline points="14.5 6.5 18 3 21 3 21 6 17.5 9.5"/><line x1="5" x2="9" y1="14" y2="18"/><line x1="7" x2="4" y1="17" y2="20"/><line x1="3" x2="5" y1="19" y2="21"/>',
  party: '<path d="m9 12 2 2 4-4"/><path d="M5 7c0-1.1.9-2 2-2h10a2 2 0 0 1 2 2v12H5V7Z"/><path d="M22 19H2"/>',
  person: '<path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>'};
const badge = (kind, bg) => "data:image/svg+xml;charset=utf-8," + encodeURIComponent(
  `<svg xmlns="http://www.w3.org/2000/svg" viewBox="-6 -6 36 36"><circle cx="12" cy="12" r="18" fill="${bg}"/>` +
  `<g fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${GLYPH[kind]}</g></svg>`);
const BLOCS = D.align.blocs, GROUPS = Object.fromEntries(D.align.groups.map(g => [g.id, g]));
const LEVEL = {3:"défense mutuelle", 2:"partenariat stratégique", 1:"lien formel partiel"};
const TINT = {3:.62, 2:.45, 1:.25};   // intensité de la couleur selon le niveau d'alignement
const inf = id => D.influence[id] || {role:"none", via:[], ties:[]};
const cname = iso => esc((D.actors[iso]||{}).name || (D.geo[iso]||{}).name || iso);
function blocColor(id){ const i = inf(id);
  return i.role==="contested" ? CONTESTED : i.bloc ? BLOCS[i.bloc].color : null; }
// Image d'un acteur : drapeau (État, bloc), photo Commons (personne), sinon pictogramme sur fond de couleur de bloc
function picOf(id){ const a = D.actors[id];
  if(a.kind==="state" || a.kind==="bloc") return flag(id);
  if(D.people[id]) return D.people[id].thumb;
  return badge(a.kind, blocColor(id) || (a.kind==="non_state" ? "#8a8a8a" : "#6b4fbb")); }
const credit = id => { const p = D.people[id]; return p ? `<p class="mute">Photo : ${esc(p.artist)}, ${esc(p.license)} —
  <a href="${safeUrl(p.page)}" target="_blank" rel="noopener">Wikimedia Commons</a></p>` : ""; };
function mix(a, b, t){ const h = x => [1,3,5].map(i => parseInt(x.slice(i,i+2),16));
  const [p,q] = [h(a), h(b)]; return "#"+p.map((v,i)=>Math.round(v*t+q[i]*(1-t)).toString(16).padStart(2,"0")).join(""); }
function blocLine(id){ const i = inf(id), nmv = i.via.map(nm).join(", ");
  const ties = i.ties.filter(t => GROUPS[t].level > 0).map(t => esc(GROUPS[t].name)).join(", ");
  if(i.role==="member") return `Bloc : <b style="color:${blocColor(id)}">${esc(BLOCS[i.bloc].name)}</b> — niveau ${i.level}/3, ${LEVEL[i.level]} (${ties})${nmv ? ` · soutenu par ${nmv}` : ""}`;
  if(i.role==="satellite") return `Bloc : <b style="color:${blocColor(id)}">${esc(BLOCS[i.bloc].name)}</b> — satellite, sans lien formel (soutenu par ${nmv})`;
  if(i.role==="contested") return `Bloc : <b style="color:${CONTESTED}">disputé</b> entre ${i.blocs.map(b=>esc(BLOCS[b].name)).join(" et ")}${ties ? ` (${ties})` : ` (soutenu par ${nmv})`}`;
  return ""; }
// Groupes formels rattachés à une entité (ex. niveaux de l'UE : membres, candidats, zone euro, Schengen)
function tiers(id){ const gs = D.align.groups.filter(g => g.entity===id);
  return gs.length ? `<h2>Niveaux</h2>` + gs.map(g => `<div class="rel"><b>${esc(g.name)}</b>
    <span class="mute">(${g.members.length}${g.level ? ` · niveau ${g.level}/3` : " · sans effet sur l'alignement"})</span><br>
    <span class="mute">${g.members.map(cname).join(", ")}${g.note ? "<br>"+esc(g.note) : ""}<br>${g.sources.map(src).join(" ; ")}</span></div>`).join("") : ""; }
const fg = getComputedStyle(document.body).color;
const outCount = id => D.edges.filter(e=>e.from===id && e.status!=="ended").length;
const layer = id => { const k = D.actors[id].kind; return DETAIL.has(k) ? "detail" : k==="non_state" ? "armed" : "core"; };
const visible = l => l==="core" || $("#lyr-"+l).checked;

// Taille = valeur mesurée (Banque mondiale) ou nombre de soutiens ; échelle en racine carrée
function metricOf(id, m){
  if(m==="supports") return outCount(id);
  const p = D.profiles[id]; const v = p && p[m==="gdp" ? "gdp_usd" : "military_usd"];
  return v ? v.value : null; }
function sizes(m){
  const vals = Object.keys(D.actors).map(id=>metricOf(id,m)).filter(v=>v);
  const max = Math.max(...vals, 1);
  return Object.fromEntries(Object.keys(D.actors).map(id=>{ const v = metricOf(id,m);
    return [id, v ? 10 + 45*Math.sqrt(v/max) : 9]; })); }

function nodeFor(id, size){ const a = D.actors[id], pic = a.kind==="state" || a.kind==="bloc";
  if(!pic) size = Math.max(size, a.kind==="person" ? 18 : 14);
  return {id, label:a.name, size, shape: "circularImage", image: picOf(id),
    color: DETAIL.has(a.kind) ? {background:"#e7e2f5", border:"#6b4fbb"}
         : blocColor(id) ? {border: blocColor(id), background: blocColor(id)} : undefined,
    borderWidth: blocColor(id) ? 1 + (inf(id).level || 1) : pic ? 1 : 1.5, font:{color:fg, size: 11 + Math.round(size/7)},
    hidden: !visible(layer(id))}; }
const edgeList = D.edges.filter(e=>e.status!=="ended").map((e,i) => ({id:"e"+i, from:e.from, to:e.to, arrows:"to",
  color:D.colors[e.types[0]]||"#888", dashes: e.status!=="active" || e.confidence==="low",
  width: e.confidence==="high"?2.2:1.2, title:`${(D.actors[e.from]||{}).name||e.from} → ${(D.actors[e.to]||{}).name||e.to} : ${e.types.join(", ")}`}));
// lien d'ancrage parti/personnalité → pays (calque détail)
const anchors = Object.entries(D.actors).filter(([id,a])=>DETAIL.has(a.kind) && D.actors[a.base])
  .map(([id,a]) => ({id:"b-"+id, from:id, to:a.base, dashes:[2,4], color:"#999", width:1, title:"rattaché à"}));

const S0 = sizes("military");
const nodesDS = new vis.DataSet(Object.keys(D.actors).map(id=>nodeFor(id, S0[id])));
const edgesDS = new vis.DataSet([...edgeList, ...anchors]);
const net = new vis.Network($("#graph"), {nodes:nodesDS, edges:edgesDS},
  {physics:{solver:"forceAtlas2Based", stabilization:{iterations:250}}, interaction:{hover:true}});
net.on("click", p => p.nodes.length ? show(p.nodes[0]) : legend());

function refresh(){
  const S = sizes($("#metric").value);
  const sz = id => ["state","bloc"].includes(D.actors[id].kind) ? S[id] : Math.max(S[id], D.actors[id].kind==="person" ? 18 : 14);
  nodesDS.update(Object.keys(D.actors).map(id=>({id, size:sz(id), font:{color:fg, size:11+Math.round(sz(id)/7)},
    hidden: !visible(layer(id))}))); }
["metric","lyr-armed","lyr-detail"].forEach(i => $("#"+i).addEventListener("change", refresh));
$("#metric").addEventListener("change", () => map && drawMarkers());

// ---------- Vue carte : une couche Leaflet par type d'acteur, chacun dans son pays ----------
const WORLD = "https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json";  // Natural Earth, domaine public
const css = v => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
const MAP_LAYERS = {core:"États & blocs", non_state:"Groupes armés", party:"Partis", person:"Personnalités", links:"Liens de soutien"};
let map, groups, linkLayers = [];
const layerOf = id => { const k = D.actors[id].kind; return k==="state"||k==="bloc" ? "core" : k; };

// Position : coords explicites (bloc), sinon coordonnées Wikidata du pays ; les acteurs rattachés
// à un même pays sont disposés en couronne autour de lui pour ne pas se superposer.
const POS = (() => {
  const geo = iso => { const g = D.geo[iso]; return g ? [g.lat, g.lon] : null; };
  const pos = {}, around = {};
  for(const [id,a] of Object.entries(D.actors)){
    if(a.coords) pos[id] = a.coords;
    else if(a.kind==="state") pos[id] = geo(id);
    else if(a.base) (around[a.base] = around[a.base] || []).push(id); }
  for(const [iso, ids] of Object.entries(around)){ const c = geo(iso); if(!c) continue;
    ids.forEach((id,i) => { const t = 2*Math.PI*i/ids.length - Math.PI/2, r = 3.2 + ids.length*0.3;
      pos[id] = [c[0] + r*Math.sin(t), c[1] + r*Math.cos(t)/Math.cos(c[0]*Math.PI/180)]; }); }
  return pos; })();

// Un contour qui franchit le 180e méridien (Russie, Fidji) est tracé d'un bord à l'autre de la carte :
// on décale ses longitudes négatives de +360° pour qu'il reste d'un seul tenant.
function fixAntimeridian(f){
  const fixRing = r => r.some((p,i) => i && Math.abs(p[0]-r[i-1][0]) > 180) ? r.map(([x,y]) => [x<0 ? x+360 : x, y]) : r;
  const g = f.geometry;
  if(g.type==="Polygon") g.coordinates = g.coordinates.map(fixRing);
  if(g.type==="MultiPolygon") g.coordinates = g.coordinates.map(poly => poly.map(fixRing));
  return f; }
function icon(id, px){ const a = D.actors[id], c = DETAIL.has(a.kind) ? "#6b4fbb" : blocColor(id);
  const ring = c ? `box-shadow:0 0 0 ${a.kind==="person" ? 2 : 1 + (inf(id).level || 1)}px ${c},0 1px 4px #0006` : "";
  return L.divIcon({className:"", iconSize:[px,px], iconAnchor:[px/2,px/2],
    html: `<div class="mk ${a.kind}" style="width:${px}px;height:${px}px"><img src="${picOf(id)}" alt="" style="object-fit:cover;${ring}"></div>`}); }
function drawMarkers(){
  const S = sizes($("#metric").value);
  for(const k of ["core","non_state","party","person"]) groups[k].clearLayers();
  for(const [id, p] of Object.entries(POS)){ if(!p) continue;
    const k = D.actors[id].kind, px = ["state","bloc"].includes(k) ? Math.round(S[id]*0.9) : k==="person" ? 30 : 22;
    L.marker(p, {icon: icon(id, px), riseOnHover:true}).bindTooltip(D.actors[id].name, {direction:"top", offset:[0,-px/2]})
      .on("click", () => show(id)).addTo(groups[layerOf(id)]); } }
// Liens courbes (Bézier quadratique) ; un lien n'est tracé que si ses deux extrémités sont affichées
function curve(a, b){ const mx=(a[0]+b[0])/2, my=(a[1]+b[1])/2, dx=b[0]-a[0], dy=b[1]-a[1];
  const c = [mx - dy*0.18, my + dx*0.18];
  return Array.from({length:25}, (_,i) => { const t=i/24, u=1-t;
    return [u*u*a[0]+2*u*t*c[0]+t*t*b[0], u*u*a[1]+2*u*t*c[1]+t*t*b[1]]; }); }
function drawLinks(){
  groups.links.clearLayers(); linkLayers = [];
  const on = k => map.hasLayer(groups[k]);
  D.edges.filter(e=>e.status!=="ended").forEach(e => {
    const a = POS[e.from], b = POS[e.to];
    if(!a || !b || !on(layerOf(e.from)) || !on(layerOf(e.to))) return;
    const l = L.polyline(curve(a,b), {color: D.colors[e.types[0]]||"#888", weight: e.confidence==="high"?2.2:1.4,
      opacity:.8, dashArray: e.status!=="active"||e.confidence==="low" ? "5 5" : null})
      .bindTooltip(`${D.actors[e.from].name} → ${D.actors[e.to].name} : ${e.types.join(", ")}`, {sticky:true})
      .addTo(groups.links);
    // flèche : petit cercle plein côté bénéficiaire
    const tip = L.circleMarker(b, {radius:3, color: D.colors[e.types[0]]||"#888", fillOpacity:1, weight:0, interactive:false}).addTo(groups.links);
    linkLayers.push({e, l, tip}); }); }
function highlightLinks(id){ linkLayers.forEach(({e,l}) => { const hit = !id || e.from===id || e.to===id;
  l.setStyle({opacity: hit ? .9 : .12, weight: hit && id ? 3.5 : (e.confidence==="high"?2.2:1.4)}); }); }

async function initMap(){
  map = L.map("map", {worldCopyJump:true, minZoom:2, maxZoom:7, zoomSnap:0.5, zoomControl:false})
    .setView([30, 25], 2.5);
  L.control.zoom({position:"bottomright"}).addTo(map);
  map.attributionControl.setPrefix(false).addAttribution("Fonds de carte : Natural Earth (domaine public) via world-atlas");
  const topo = await fetch(WORLD).then(r => r.json());
  const world = topojson.feature(topo, topo.objects.countries);
  world.features = world.features.filter(f => f.id !== "010").map(fixAntimeridian);  // sans l'Antarctique
  const byNum = Object.fromEntries(Object.entries(D.geo).filter(([_,g]) => g.iso_numeric)
    .map(([iso,g]) => [String(+g.iso_numeric), iso]));
  L.geoJSON(world, {
    style: f => { const iso = byNum[String(+f.id)], c = iso && blocColor(iso);
      return {color: css("--line"), weight:.6, fillOpacity:1,
              fillColor: c ? mix(c, css("--land"), TINT[inf(iso).level] || .25) : iso && D.actors[iso] ? css("--land-hl") : css("--land")}; },
    onEachFeature: (f, l) => { const iso = byNum[String(+f.id)];
      if(!iso) return;
      l.bindTooltip(`${cname(iso)}${blocColor(iso) ? " — " + (inf(iso).role==="contested" ? "disputé" : esc(BLOCS[inf(iso).bloc].name) + (inf(iso).role==="member" ? `, niveau ${inf(iso).level}/3` : ", satellite")) : ""}`, {sticky:true});
      l.on("click", () => D.actors[iso] ? show(iso) : showCountry(iso)); }
  }).addTo(map);
  groups = Object.fromEntries(Object.keys(MAP_LAYERS).map(k => [k, L.layerGroup().addTo(map)]));
  L.control.layers(null, Object.fromEntries(Object.entries(MAP_LAYERS).map(([k,label]) => [label, groups[k]])),
    {collapsed: innerWidth < 800, position:"bottomleft"}).addTo(map);
  map.on("overlayadd overlayremove", drawLinks);
  drawMarkers(); drawLinks(); }

function setView(v){
  document.body.classList.toggle("map", v==="map");
  $("#v-graph").setAttribute("aria-pressed", v==="graph"); $("#v-map").setAttribute("aria-pressed", v==="map");
  if(v==="map"){ if(!map) initMap(); else map.invalidateSize(); } }
$("#v-graph").addEventListener("click", () => setView("graph"));
$("#v-map").addEventListener("click", () => setView("map"));

function f(v, unit="", d=1){ if(!v) return "n/d"; let x=v.value, s;
  s = Math.abs(x)>=1e9 ? (x/1e9).toFixed(d)+" Md" : Math.abs(x)>=1e6 ? (x/1e6).toFixed(d)+" M" : x.toLocaleString("fr-FR",{maximumFractionDigits:d});
  return `${s}${unit} <span class="mute">(${v.year})</span>`; }
const tags = t => t.map(x=>`<span class="tag" style="background:${D.colors[x]||'#888'}">${esc(x)}</span>`).join("");
const src = s => esc(s).replace(/https?:\/\/[^\s<]+/g, u => `<a href="${u}" target="_blank" rel="noopener">${u}</a>`);
const rel = (e, other) => `<div class="rel"><b data-id="${esc(other)}">${nm(other)}</b> ${tags(e.types)}
  <div class="mute">${esc(e.status)} · confiance ${esc(e.confidence)} · vérifié ${esc(e.verified)} · ${(e.sources||[]).map(src).join(" ; ")}${e.note?"<br>"+esc(e.note):""}</div></div>`;
document.addEventListener("click", ev => { const b = ev.target.closest("[data-id]"); if(b) show(b.dataset.id); });

function spark(daily){ if(!daily || daily.length<2) return "";
  const n=daily.length, pts=daily.map(([_,p],i)=>`${(i/(n-1)*78+1).toFixed(1)},${(21-p*20).toFixed(1)}`).join(" ");
  return `<svg class="spark" viewBox="0 0 80 22" aria-hidden="true"><polyline points="${pts}"/></svg>`; }
function mkt(m){ const d=m.delta_pts, cls = d==null?"":d>0?"up":d<0?"down":"";
  return `<div class="mkt"><span class="p">${m.prob<0.01?"&lt;1":(m.prob*100).toFixed(0)} %</span>
    <span><a href="${safeUrl(m.url)}" target="_blank" rel="noopener">${esc(m.question)}</a>
    <span class="mute"><br>${esc(m.source)} · ${d==null?"variation 7 j n/d":`<span class="${cls}">${d>0?"+":""}${d} pts</span> sur 7 j`}${m.stale?" · absent du dernier relevé":""}</span></span>
    ${spark(m.daily)}</div>`; }
function marketsFor(id){ return Object.entries(D.markets).filter(([_,v])=>v.countries.includes(id)); }

function show(id){
  const a = D.actors[id]||{};
  if(!visible(layer(id))){ $("#lyr-"+layer(id)).checked = true; refresh(); }  // ouvrir le calque de l'acteur demandé
  const members = Object.keys(D.actors).filter(m=>(D.actors[m].member_of||[]).includes(id));
  net.selectNodes([id, ...members]);
  if(map) highlightLinks(id);
  const iso = (a.kind==="state" || a.kind==="bloc") ? id : a.base;
  const p = D.profiles[iso];
  let h = `<h1>${nm(id)}</h1><div class="mute">${esc(KIND[a.kind]||a.kind)}${a.base&&a.kind!=="state"?" · "+nm(a.base)+" ("+esc(a.base)+")":""}${(a.member_of||[]).length?" · membre : "+a.member_of.map(nm).join(", "):""}</div>`;
  if(D.people[id]) h = `<img src="${safeUrl(D.people[id].thumb)}" alt="" style="width:72px;height:72px;border-radius:50%;object-fit:cover;float:right;margin-left:10px">` + h;
  if(blocLine(id)) h += `<p class="mute">${blocLine(id)}</p>`;
  h += tiers(id);
  if(a.note) h += `<p>${esc(a.note)}${(a.sources||[]).length?`<br><span class="mute">${a.sources.map(src).join(" ; ")}</span>`:""}</p>`;
  h += credit(id);
  if(members.length){
    h += `<h2>Membres suivis (${members.length})</h2><p class="mute">Surlignés sur le graphe.</p>` + members.map(m => {
      const out = D.edges.filter(e=>e.from===m && e.status!=="ended");
      return `<div class="rel"><b data-id="${esc(m)}">${nm(m)}</b> <span class="mute">→ ${out.length ? out.map(e=>nm(e.to)).join(", ") : "aucun soutien recensé"}</span></div>`; }).join(""); }
  const local = Object.keys(D.actors).filter(x=>DETAIL.has(D.actors[x].kind) && D.actors[x].base===id);
  if(local.length) h += `<h2>Partis & personnalités</h2>` + local.map(x=>`<div class="rel"><b data-id="${esc(x)}">${nm(x)}</b> <span class="mute">${esc(KIND[D.actors[x].kind])}</span></div>`).join("");
  const out = D.edges.filter(e=>e.from===id&&e.status!=="ended"), inn = D.edges.filter(e=>e.to===id&&e.status!=="ended");
  if(out.length) h += `<h2>Soutient</h2>` + out.map(e=>rel(e,e.to)).join("");
  if(inn.length) h += `<h2>Soutenu par</h2>` + inn.map(e=>rel(e,e.from)).join("");
  for(const [pair, v] of marketsFor(id)){
    h += `<h2>Marchés · ${esc(pair)}</h2>` + (v.markets.length ? v.markets.map(mkt).join("")
      : `<p class="mute">Aucun marché ouvert trouvé.</p>`); }
  if(p){ const g=p.government||{}, t=p.population_trend, wb=!!p.population;
    if(a.kind!=="state" && a.kind!=="bloc") h += `<h2>Pays d'ancrage : ${nm(iso)}</h2>`;
    if(a.kind!=="bloc") h += `<h2>Régime</h2><div class="kv"><span>Forme</span><span>${esc((g.forms||[]).join(", "))||"n/d"}</span>
      <span>Chef d'État</span><span>${esc((g.head_of_state||[]).join(", "))||"n/d"}</span></div>`;
    h += `${wb ? "" : `<p class="mute">Aucune donnée Banque mondiale pour ce territoire (Taïwan n'y figure pas).</p>`}
    ${!wb ? "" : `<h2>Démographie</h2><div class="kv"><span>Population</span><span>${f(p.population)}</span>
      <span>Tendance</span><span>${t?`${esc(t.label)} (${t.annual_rate_pct>0?"+":""}${t.annual_rate_pct} %/an, ${t.period})${t.below_replacement?"<br>fécondité sous le renouvellement":""}`:"n/d"}</span>
      <span>Fécondité</span><span>${f(p.fertility,"",2)}</span><span>65 ans et +</span><span>${f(p.age65_pct," %")}</span></div>
    <h2>Économie & ressources</h2><div class="kv"><span>PIB</span><span>${f(p.gdp_usd," $")}</span>
      <span>PIB / hab</span><span>${f(p.gdp_per_capita_usd," $",0)}</span>
      <span>Rentes ressources</span><span>${f(p.resource_rents_pct_gdp," % PIB")}</span>
      <span>· pétrole</span><span>${f(p.oil_rents_pct_gdp," %")}</span><span>· gaz</span><span>${f(p.gas_rents_pct_gdp," %")}</span>
      <span>· minerais</span><span>${f(p.mineral_rents_pct_gdp," %")}</span>
      <span>Terres arables</span><span>${f(p.arable_land_pct," %")}</span>
      <span>Eau douce</span><span>${f(p.freshwater_m3_per_capita," m³/hab",0)}</span></div>
    <h2>Technologie & défense</h2><div class="kv"><span>R&D</span><span>${f(p.rd_pct_gdp," % PIB",2)}</span>
      <span>Export high-tech</span><span>${f(p.hightech_exports_pct," %")}</span>
      <span>Internet</span><span>${f(p.internet_users_pct," %")}</span>
      <span>Défense</span><span>${f(p.military_pct_gdp," % PIB")} · ${f(p.military_usd," $")}</span></div>`}
    <p class="mute">Profil du ${esc(p.fetched_at.slice(0,10))} — ${esc(a.kind==="bloc" ? "Banque mondiale WDI (agrégat)" : wb ? p.sources.join(", ") : "Wikidata")}</p>`;
  } else if(iso) h += `<p class="mute">Pas de profil pour ${esc(iso)}.</p>`;
  $("#panel").innerHTML = h;
}
function showCountry(iso){
  if(map) highlightLinks(null);
  const i = inf(iso);
  $("#panel").innerHTML = `<h1>${cname(iso)}</h1><div class="mute">État — hors du graphe de soutiens</div>
    ${blocLine(iso) ? `<p class="mute">${blocLine(iso)}</p>` : ""}
    <h2>Liens formels</h2>` + i.ties.map(t => { const g = GROUPS[t];
      return `<div class="rel"><b>${esc(g.name)}</b> <span class="mute">${g.level ? `niveau ${g.level}/3` : "sans effet sur l'alignement"}
        ${g.note ? "<br>"+esc(g.note) : ""}<br>${g.sources.map(src).join(" ; ")}</span></div>`; }).join("")
    + `<p class="mute">Ce pays n'a encore aucune relation de soutien sourcée dans network.yaml.</p>`; }
function legend(){
  if(map) highlightLinks(null);
  const all = Object.values(D.markets).flatMap(v=>v.markets).filter(m=>!m.stale);
  const moves = all.filter(m=>m.delta_pts!=null && Math.abs(m.delta_pts)>=D.alert)
                   .sort((a,b)=>Math.abs(b.delta_pts)-Math.abs(a.delta_pts));
  $("#panel").innerHTML = `<h1>Réseau de soutiens</h1><p class="mute">Clique un acteur ; clique un bloc (UE) pour voir ses membres.
  Drapeau = État ou bloc · épées = groupe armé · urne = parti · photo = personnalité. Trait plein = actif & confirmé,
  pointillé = réduit / allégué ; pointillé gris = rattachement d'un parti ou d'une personne à son pays.</p>
  <p class="mute">Vue « Carte » : chaque acteur dans son pays d'ancrage (coordonnées Wikidata), une couche par type
  d'acteur (panneau en bas à gauche) ; cliquer un acteur ou un pays surligne ses liens.</p>
  <p class="mute">Taille = dépenses militaires ou PIB en dollars (Banque mondiale, dernière année disponible)
  ou nombre de soutiens accordés — voir le sélecteur. Sans donnée (Taïwan, groupes armés…) : taille minimale.</p>
  <h2>Blocs d'influence</h2>${Object.entries(BLOCS).map(([k,b]) => `<div class="rel">
    <b style="color:${b.color}">■ ${esc(b.name)}</b><br><span class="mute">${D.align.groups.filter(g=>g.bloc===k && g.level>0)
      .map(g => `${esc(g.name)} (niveau ${g.level}, ${g.members.length} pays)`).join(" · ")}</span></div>`).join("")}
  <div class="rel"><b style="color:${CONTESTED}">■ Disputé</b> <span class="mute">— liens ou soutiens venant des deux blocs</span></div>
  <p class="mute">Intensité = niveau du lien formel le plus fort : 3 défense mutuelle, 2 partenariat stratégique,
  1 candidature ou participation gelée (sources : alignments.yaml, cliquer un pays). Sans lien formel, un acteur
  dont tous les soutiens actifs viennent d'un même bloc en est « satellite » (niveau 1, déduit du graphe).
  Les liens formels ne disent rien de la cohésion réelle — ce sera l'étape 2 (votes à l'ONU).
  Partis et personnalités ne sont pas classés.</p>
  <h2>Types de soutien</h2><div class="legend">${tags(Object.keys(D.colors))}</div>
  <h2>Mouvements de marché ≥ ${D.alert} pts sur 7 j</h2>${moves.length ? moves.map(mkt).join("")
    : `<p class="mute">Aucun${all.length?"":" — pas encore de cotes relevées"}.</p>`}
  <p class="mute">Les seuls pourcentages affichés sont des cotes de marchés de prédiction (Polymarket, Kalshi).
  Icônes <a href="https://lucide.dev" target="_blank" rel="noopener">Lucide</a> (ISC) ; photos Wikimedia Commons, crédits dans chaque fiche.
  Données du graphe : <a href="network.json">JSON</a> · <a href="network.csv">CSV</a>, licence CC BY 4.0.
  Généré le ${esc(D.built.slice(0,16).replace("T"," "))} UTC.</p>`; }
legend();
</script></body></html>"""

if __name__ == "__main__":
    build()
