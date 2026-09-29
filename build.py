"""python build.py → site/ : accueil, dossiers, explorateur (graphe, carte, organisations), méthode, manifeste,
et le graphe en données ouvertes (network.json, network.csv — CC BY 4.0). Publiable tel quel."""
from dotenv import load_dotenv; load_dotenv()
import csv, json
from pathlib import Path
import brand, db, dossier, method, network, pages, style

OUT = Path("site")
DATA_LICENSE = "CC BY 4.0 — https://creativecommons.org/licenses/by/4.0/ — geowatch network.yaml"
TYPE_COLORS = {"arms": "#d64545", "troops": "#8b1e1e", "financial": "#2f8f5b", "training": "#c98a1b",
               "intelligence": "#6b4fbb", "political": "#3a6fd8", "economic": "#1f9aa5", "dual_use": "#b0569a"}

def export_data(actors, edges):
    (OUT / "network.json").write_text(json.dumps(
        {"license": DATA_LICENSE, "generated_at": db.now(), "actors": actors, "edges": edges,
         "tensions": network.tensions()},
        ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    with open(OUT / "network.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["from", "from_name", "to", "to_name", "types", "status", "confidence",
                    "sources", "verified", "note", "why"])
        for e in edges:
            w.writerow([e["from"], network.name(actors, e["from"]), e["to"], network.name(actors, e["to"]),
                        ";".join(e["types"]), e["status"], e["confidence"], " | ".join(e["sources"]),
                        e["verified"], e.get("note", ""), e.get("why", "")])

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
    OUT.mkdir(exist_ok=True)
    aligns = network.alignments()
    geo, unga = db.load_geo(), db.load_unga()
    if unga:  # le jeu Voeten est indexé en ISO3, le site en ISO2
        by3 = {v["iso3"]: k for k, v in geo.items() if v.get("iso3")}
        unga["countries"] = {by3[c]: v for c, v in unga["countries"].items() if c in by3}
        unga["by_year"] = {y: {by3[c]: v for c, v in d.items() if c in by3} for y, d in unga.get("by_year", {}).items()}
    data = {"actors": actors, "edges": edges, "profiles": profiles, "colors": TYPE_COLORS,
            "tensions": network.tensions(), "align": aligns, "influence": network.influence(actors, edges, aligns), "geo": geo, "people": db.load_people(), "unga": unga,
            "dossiers": [{"id": x["id"], "title": x["title"]} for x in dossier.load()], "built": db.now()}
    html = TEMPLATE.replace("__DATA__", json.dumps(data, ensure_ascii=False, default=str)
                            .replace("</", "<\\/"))
    (OUT / "explorer.html").write_text(html.replace("__NAME__", brand.NAME).replace("__FONTS__", style.FONTS).replace("__TOP__", style.top("explorer.html"))
        .replace("__ICON_ORGS__", style.icon("orgs", 16)).replace("__ICON_MAP__", style.icon("map", 16)).replace("__ICON_GRAPH__", style.icon("graph", 16)), encoding="utf-8")
    export_data(actors, edges)
    method.write(OUT, data)
    style.write(OUT)
    dossier.write(OUT, data)
    pages.write(OUT, data)
    print(f"→ {OUT}/ : index.html (accueil), explorer.html, manifeste.html, methode.html, dossiers, network.json, network.csv")
    return data

TEMPLATE = r"""<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Explorer — __NAME__</title>
<script src="https://cdn.jsdelivr.net/npm/vis-network@10.1.2/standalone/umd/vis-network.min.js"></script>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.css">
<script src="https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://cdn.jsdelivr.net/npm/topojson-client@3/dist/topojson-client.min.js"></script>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link rel="stylesheet" href="__FONTS__">
<link rel="stylesheet" href="style.css"><link rel="icon" href="favicon.svg" type="image/svg+xml">
<style>
/* explorateur : mêmes jetons que style.css ; l'interface reste discrète, la couleur sert aux données */
:root{--land-hl:#e9ecef}
@media (prefers-color-scheme:dark){:root{--land-hl:#28303b}}
body{font:14.5px/1.5 var(--sans);display:grid;grid-template-columns:1fr 380px;grid-template-rows:auto minmax(0,1fr);height:100vh}
.xhead{grid-column:1/-1;padding:0 18px 12px;border-bottom:1px solid var(--mist);position:relative;z-index:1500}.xhead .top{padding-top:14px}
@media (max-width:800px){body{grid-template-columns:1fr;grid-template-rows:auto 60vh auto;height:auto}}
#stage{position:relative;min-height:60vh}#graph{position:absolute;inset:0}
/* sélecteur de vue : en tête du panneau de gauche, mêmes icônes que le menu Explorer */
#views{display:flex;gap:4px;margin:-2px 0 4px;padding-bottom:8px;border-bottom:1px solid var(--mist)}
#views button{font:inherit;font-size:13.5px;display:flex;align-items:center;gap:6px;padding:5px 8px;border:0;border-radius:4px;
background:none;color:var(--graphite);cursor:pointer}#views button:hover{color:var(--ink)}
#views button .ico{color:var(--peach)}
#views button[aria-pressed=true]{color:var(--ink);background:color-mix(in srgb,var(--ink) 7%,transparent)}
#controls{position:absolute;top:14px;left:14px;z-index:1000;background:color-mix(in srgb,var(--paper) 94%,transparent);
border:1px solid var(--mist);border-radius:3px;padding:10px 12px;font-size:13.5px;display:flex;flex-direction:column;gap:6px;
max-width:calc(100% - 28px);width:340px}
#controls select{font:inherit;background:var(--paper);color:var(--ink);border:1px solid var(--mist);border-radius:3px;padding:1px 2px;max-width:100%}
#controls summary{cursor:pointer;color:var(--graphite)}#controls summary:hover{color:var(--ink)}
#controls details[open] summary{color:var(--ink);margin-bottom:4px}#settings label{display:block;margin:4px 0}
#year{accent-color:var(--peach)}
#map{position:absolute;inset:0;display:none;background:var(--ocean)}
body.map #map{display:block}body.map #graph,body.map .graph-only{display:none}
.map-only{display:none}body.map label.map-only{display:block}
#venn{position:absolute;inset:0;display:none;padding:190px 12px 12px}body.venn #venn{display:block}
body.venn #graph,body.venn .graph-only{display:none}#venn svg{width:100%;height:100%;overflow:visible}
#venn text{font-family:system-ui,sans-serif}.vc{cursor:pointer}.vc:hover circle{stroke:var(--fg)}
.venn-empty{max-width:380px;margin:120px auto;text-align:center}.venn-note{position:absolute;bottom:4px;left:12px;right:12px;margin:0}
.leaflet-container{background:var(--ocean);font:inherit}
.leaflet-control-layers,.leaflet-bar a,.leaflet-tooltip{background:var(--card);color:var(--fg);border-color:var(--line)}
.mk{display:flex;align-items:center;justify-content:center;cursor:pointer}
.mk img{width:100%;height:100%;border-radius:50%;box-shadow:0 0 0 1.5px var(--card),0 1px 4px #0006}
.mk i{display:block;width:12px;height:12px;background:#6b4fbb;box-shadow:0 0 0 1.5px var(--card)}
.mk.non_state i{background:#d64545;transform:rotate(45deg)}.mk.party i{background:#6b4fbb}
.mk.person i{background:#6b4fbb;clip-path:polygon(50% 0,100% 100%,0 100%);box-shadow:none;width:14px;height:13px}
aside{padding:24px 24px 40px;overflow:auto;border-left:1px solid var(--mist)}aside a{color:inherit}
aside h1{font:400 26px/1.2 var(--serif);margin:0 0 6px}aside h2{font:400 18px/1.3 var(--serif);color:var(--ink);margin:26px 0 8px}
aside p{margin:0 0 10px}.keys{display:grid;grid-template-columns:78px 1fr;gap:6px 12px;margin:0;font-size:13.5px}
.keys dt{color:var(--graphite)}.keys dd{margin:0}.key{display:inline-flex;align-items:center;gap:5px;margin:0 10px 2px 0;white-space:nowrap}
.key i{width:9px;height:9px;border-radius:50%;display:inline-block}
.kv{display:grid;grid-template-columns:140px 1fr;gap:3px 10px}.kv span:nth-child(odd){color:var(--mute)}
.rel{padding:10px 0;border-bottom:1px solid var(--mist)}.rel b{cursor:pointer}.rel .mute{margin-top:2px}
.tag{display:inline-block;font-size:11px;padding:1px 6px;border-radius:9px;color:#fff;margin:2px 2px 0 0}
.mute{color:var(--mute);font-size:13px}.legend .tag{margin-right:4px}
#orgs summary{cursor:pointer}#orgs .list{max-height:40vh;overflow:auto;margin-top:4px;padding-right:4px}
#orgs .og{font-weight:600;color:var(--mute);margin-top:6px}#orgs label{display:flex;align-items:center;gap:6px}
#orgs i,.sw{display:inline-block;width:11px;height:11px;border-radius:3px;flex:none;border:1px solid var(--line);vertical-align:-1px}
.future{opacity:.45}
</style></head><body>
<header class="xhead">__TOP__</header>
<div id="stage"><div id="graph"></div><div id="map"></div><div id="venn"></div>
<div id="controls">
  <div id="views" role="group" aria-label="Vue"><button id="v-venn" aria-pressed="false">__ICON_ORGS__Organisations</button><button id="v-map" aria-pressed="false">__ICON_MAP__Carte</button><button id="v-graph" aria-pressed="true">__ICON_GRAPH__Graphe</button></div>
  <label>Année <input type="range" id="year" min="2014" step="1" style="vertical-align:middle;width:140px"> <b id="year-label"></b></label>
  <details id="orgs"><summary>Organisations <b id="orgs-n"></b></summary><div class="list"></div></details>
  <details id="settings"><summary>Réglages</summary>
  <label>Taille des acteurs <select id="metric">
    <option value="military">dépenses militaires ($)</option><option value="gdp">PIB ($)</option>
    <option value="supports">nombre de soutiens accordés</option></select></label>
  <label class="map-only">Couleur des pays <select id="colormode">
    <option value="formal">liens formels (traités, adhésions)</option><option value="votes">votes à l'ONU</option></select></label>
  <label class="graph-only"><input type="checkbox" id="lyr-armed" checked> Groupes armés non étatiques</label>
  <label class="graph-only"><input type="checkbox" id="lyr-detail"> Partis et personnalités</label>
  <label class="graph-only"><input type="checkbox" id="lyr-tensions" checked> Tensions (guerres, sanctions…)</label>
  </details>
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
// Dirigeant (champ leader) : affiché sur la fiche, pas un nœud du graphe (sauf s'il a des relations propres)
const leaderKey = id => { const l = (D.actors[id]||{}).leader; return typeof l === "string" ? l : l ? "leader:" + id : null; };
function leaderLine(id){ const l = (D.actors[id]||{}).leader; if(!l) return "";
  const k = leaderKey(id), p = D.people[k], name = typeof l === "string" ? `<b data-id="${esc(l)}" style="cursor:pointer">${nm(l)}</b>` : `<b>${esc(l.name)}</b>`;
  const role = typeof l === "string" ? "" : l.role ? ` — ${esc(l.role)}` : "";
  return `<div class="rel" style="display:flex;gap:10px;align-items:center">${p ? `<img src="${safeUrl(p.thumb)}" alt=""
    style="width:40px;height:40px;border-radius:50%;object-fit:cover">` : ""}<div>Dirigeant : ${name}${role}</div></div>`; }
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
// ---------- Organisations (groupes d'alignments.yaml) : calques superposables de la carte, fiches ----------
// Jusqu'à 6 calques, palette catégorielle validée (clair / sombre) ; une couleur reste attachée à son organisation
// tant qu'elle est cochée, pour que cocher ou décocher une autre ne repeigne pas la carte.
const ORG_PAL = matchMedia("(prefers-color-scheme: dark)").matches
  ? ["#3987e5","#d95926","#199e70","#c98500","#d55181","#008300"]
  : ["#2a78d6","#eb6834","#1baf7a","#eda100","#e87ba4","#008300"];
const SEL = new Map();  // id du groupe → couleur
const yr = d => +String(d).slice(0,4);
// Membres l'année Y : adhésions (joined) et départs (left) datés depuis 2014 ; un membre sans date l'était déjà.
function membersAt(g, Y){ if(g.since && yr(g.since) > Y) return [];
  const j = g.joined || {}, l = g.left || {};
  return [...g.members.filter(m => !j[m] || yr(j[m]) <= Y), ...Object.keys(l).filter(m => yr(l[m]) > Y)]; }
function movesOf(g){ return [...(g.since ? [{g, d:g.since, t:"création"}] : []),
  ...Object.entries(g.joined||{}).filter(([m,d]) => d !== g.since).map(([m,d]) => ({g, m, d, t:"entrée"})),
  ...Object.entries(g.left||{}).map(([m,d]) => ({g, m, d, t:"sortie"}))]; }
(() => { const box = $("#orgs .list"), add = (label, gs) => { if(!gs.length) return;
    box.insertAdjacentHTML("beforeend", `<div class="og">${esc(label)}</div>` + gs.map(g =>
      `<label><input type="checkbox" autocomplete="off" value="${esc(g.id)}"><i></i>${esc(g.name)} <span class="mute">(${g.members.length})</span></label>`).join("")); };
  add("Forums économiques et politiques", D.align.groups.filter(g => g.kind==="forum"));
  Object.entries(BLOCS).forEach(([k,b]) => add(b.name, D.align.groups.filter(g => g.bloc===k)));
  box.addEventListener("change", syncOrgs);
  addEventListener("pageshow", () => SEL.size || document.querySelector("#orgs input:checked") ? syncOrgs() : null); })();
// Les cases cochées font foi (le navigateur peut les restaurer au rechargement) : SEL est réaligné sur elles.
function syncOrgs(){
  const on = new Set([...document.querySelectorAll("#orgs input:checked")].map(i => i.value));
  [...SEL.keys()].forEach(id => on.has(id) || SEL.delete(id));
  on.forEach(id => { if(!SEL.has(id) && SEL.size < ORG_PAL.length){ const used = new Set(SEL.values());
    SEL.set(id, ORG_PAL.find(c => !used.has(c))); } });
  document.querySelectorAll("#orgs input").forEach(i => i.checked = SEL.has(i.value));
  document.querySelectorAll("#orgs input").forEach(i => { i.nextElementSibling.style.background = SEL.has(i.value) ? tint(SEL.get(i.value)) : "transparent";
    i.disabled = !i.checked && SEL.size >= ORG_PAL.length; });
  $("#orgs-n").textContent = SEL.size ? `(${SEL.size}/${ORG_PAL.length})` : "";
  if(map) drawOrgs();
  drawVenn();
  SEL.size ? showLayers() : legend(); }
// même teinte partout (carte, cases, panneau) : couleur de l'organisation légèrement adoucie vers le fond de carte
const tint = c => mix(c, css("--land"), .8);
const sw = c => `<span class="sw" style="background:${tint(c)}"></span>`;
function showLayers(){ const Y = YEAR(), gs = [...SEL.keys()].map(id => GROUPS[id]);
  const at = Object.fromEntries(gs.map(g => [g.id, membersAt(g, Y)])), where = {};
  gs.forEach(g => at[g.id].forEach(m => (where[m] = where[m] || []).push(g.id)));
  const pivots = Object.entries(where).filter(([,v]) => v.length > 1)
    .sort((a,b) => b[1].length - a[1].length || cname(a[0]).localeCompare(cname(b[0])));
  const moves = gs.flatMap(movesOf).sort((a,b) => a.d < b.d ? -1 : a.d > b.d ? 1 : 0);
  $("#panel").innerHTML = `<div id="layers-panel"><h1>Organisations superposées</h1>
    <div class="mute">Situation en ${Y} — curseur « Année » pour voir les adhésions et les départs</div>
    ${gs.map(g => `<div class="rel">${sw(SEL.get(g.id))}<a href="#" data-group="${esc(g.id)}">${esc(g.name)}</a>
      <span class="mute">— ${at[g.id].length} pays${g.kind==="forum" ? " · forum" : ` · ${esc(BLOCS[g.bloc].name)}, niveau ${g.level}/3`}</span></div>`).join("")}
    ${gs.length > 1 ? `<h2>Pays à la croisée (${pivots.length})</h2>` + (pivots.length ? pivots.map(([m,ids]) =>
        `<div class="rel"><a href="#" data-country="${esc(m)}">${cname(m)}</a> ${ids.map(id => sw(SEL.get(id))).join("")}
        <span class="mute">${ids.map(id => esc(GROUPS[id].name)).join(" · ")}</span></div>`).join("")
      : `<p class="mute">Aucun pays n'appartient à plusieurs de ces organisations en ${Y}.</p>`) : ""}
    <h2>Mouvements depuis 2014</h2>${moves.length ? moves.map(v => `<div class="rel${yr(v.d) > Y ? " future" : ""}">${sw(SEL.get(v.g.id))}
      <b>${esc(v.d)}</b> · ${v.m ? `<a href="#" data-country="${esc(v.m)}">${cname(v.m)}</a> ${v.t==="entrée" ? "entre dans" : "quitte"}` : "création de"}
      ${esc(v.g.name)}</div>`).join("") : `<p class="mute">Aucune adhésion ni départ daté depuis 2014 pour ces organisations.</p>`}
    <p class="mute">Chaque organisation a sa couleur ; un pays membre de plusieurs organisations cochées est rayé de
    toutes leurs couleurs, sans mélange.
    Dates d'adhésion et de départ sourcées dans <code>alignments.yaml</code> (voir chaque organisation).
    Les couleurs des blocs d'influence sont masquées tant qu'un calque est affiché.</p></div>`; }
const forumsOf = iso => D.align.groups.filter(g => g.kind==="forum" && g.members.includes(iso));
const forumLine = iso => { const f = forumsOf(iso);
  return f.length ? `Organisations : ${f.map(g => `<a href="#" data-group="${esc(g.id)}">${esc(g.name)}</a>`).join(", ")}` : ""; };
function showGroup(gid){ const g = GROUPS[gid]; if(!g) return;
  $("#panel").innerHTML = `<h1>${esc(g.name)}</h1><div class="mute">${g.kind==="forum" ? "forum — sans effet sur les blocs d'influence"
      : `${esc(BLOCS[g.bloc].name)} — niveau ${g.level}/3`} · ${g.members.length} pays</div>
    <p>${g.members.map(m => `<a href="#" data-country="${esc(m)}">${cname(m)}</a>${(g.joined||{})[m] ? ` <span class="mute">(depuis ${esc(g.joined[m])})</span>` : ""}`).join(", ")}</p>
    ${Object.keys(g.left||{}).length ? `<p class="mute">Anciens membres : ${Object.entries(g.left).map(([m,d]) =>
      `<a href="#" data-country="${esc(m)}">${cname(m)}</a> (jusqu'en ${esc(d)})`).join(", ")}</p>` : ""}
    ${g.since ? `<p class="mute">Créée en ${esc(g.since)}.</p>` : ""}
    ${g.note ? `<p class="mute">${esc(g.note)}</p>` : ""}<p class="mute">${g.sources.map(src).join(", ")}</p>`; }
document.addEventListener("click", ev => {
  const gl = ev.target.closest("[data-group]"); if(gl){ ev.preventDefault(); showGroup(gl.dataset.group); }
  const cl = ev.target.closest("[data-country]"); if(cl){ ev.preventDefault(); D.actors[cl.dataset.country] ? show(cl.dataset.country) : showCountry(cl.dataset.country); } });

// ---------- Votes à l'ONU (Voeten) ----------
const U = D.unga || {}, UC = U.countries || {};
const pct = x => x == null ? "n/d" : Math.round(x*100) + " %";
function ungaLine(iso){ const v = UC[iso]; if(!v) return "";
  return `Votes à l'ONU (${U.agreement_year}) : comme France/Allemagne <b>${pct(v.west)}</b>, comme Russie/Chine <b>${pct(v.axis)}</b>,
    ${iso==="US" ? "" : `comme les États-Unis ${pct(v.usa)} `}— penche ${v.lean > .05 ? "vers l'Europe" : v.lean < -.05 ? "vers Russie/Chine" : "entre les deux"}
    (${v.lean > 0 ? "+" : ""}${v.lean.toFixed(2)})`; }
const voteYear = () => Math.min(YEAR(), U.agreement_year);
const leanAt = iso => ((U.by_year || {})[voteYear()] || {})[iso];
function votesColor(iso){ const lean = leanAt(iso); if(lean == null) return null;
  const t = Math.min(1, Math.abs(lean) / .5) * .7;
  return mix(lean >= 0 ? BLOCS.west.color : BLOCS.axis.color, css("--land"), t); }
// Écart de vote États-Unis ↔ moyenne France/Allemagne (axe unique Voeten), comparé à l'écart France ↔ Allemagne
function driftBlock(){ const d = U.drift || []; if(d.length < 2) return "";
  const W = 260, H = 60, max = Math.max(...d.map(x => x.us_gap)), X = i => 8 + i*(W-16)/(d.length-1), Y = v => H-8 - v/max*(H-16);
  const line = k => d.map((x,i) => `${X(i).toFixed(1)},${Y(x[k]).toFixed(1)}`).join(" ");
  const a = d[d.length-2], b = d[d.length-1];
  return `<h2>Dérive transatlantique</h2><svg viewBox="0 0 ${W} ${H}" style="width:100%;max-width:${W}px" aria-hidden="true">
    <polyline points="${line("us_gap")}" fill="none" stroke="${BLOCS.west.color}" stroke-width="2"/>
    <polyline points="${line("fr_de_gap")}" fill="none" stroke="var(--mute)" stroke-width="1.5" stroke-dasharray="3 3"/></svg>
    <p class="mute">Écart de vote à l'ONU États-Unis ↔ France/Allemagne (trait plein) : <b>${a.us_gap} en ${a.year} → ${b.us_gap} en ${b.year}</b>,
    contre ${b.fr_de_gap} entre France et Allemagne (pointillés), ${d[0].year}–${b.year}. Mesure sur l'axe unique de Voeten,
    fiable pour un écart entre deux pays, pas pour placer un pays entre deux blocs.</p>`; }
function euCohesion(id){ const g = D.align.groups.find(x => x.entity===id && x.level===3); if(!g) return "";
  const vals = g.members.filter(m => UC[m]).map(m => [m, UC[m].west]).sort((a,b) => a[1]-b[1]);
  if(!vals.length) return "";
  const mean = vals.reduce((s,[,v]) => s+v, 0) / vals.length;
  return `<h2>Cohésion des votes (${U.agreement_year})</h2><p class="mute">Les membres votent comme France/Allemagne en moyenne
    <b>${pct(mean)}</b> des fois. Les plus éloignés : ${vals.slice(0,3).map(([m,v]) => `${cname(m)} ${pct(v)}`).join(", ")}.</p>`; }

// Groupes formels rattachés à une entité (ex. niveaux de l'UE : membres, candidats, zone euro, Schengen)
function tiers(id){ const gs = D.align.groups.filter(g => g.entity===id);
  return gs.length ? `<h2>Niveaux</h2>` + gs.map(g => `<div class="rel"><b>${esc(g.name)}</b>
    <span class="mute">(${g.members.length}${g.level ? ` · niveau ${g.level}/3` : " · sans effet sur l'alignement"})</span><br>
    <span class="mute">${g.members.map(cname).join(", ")}${g.note ? "<br>"+esc(g.note) : ""}<br>${g.sources.map(src).join(", ")}</span></div>`).join("") : ""; }
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
// ---------- Temps : une relation est affichée pour l'année Y si since ≤ Y ≤ until ----------
const NOW = +D.built.slice(0,4);
const YEAR = () => +($("#year") ? $("#year").value : NOW);
(() => { const y = $("#year"); y.max = NOW; y.value = NOW; })();
function activeAt(e, Y){
  const since = e.since ? +String(e.since).slice(0,4) : null, until = e.until ? +String(e.until).slice(0,4) : null;
  if(since && Y < since) return false;
  if(until && Y > until) return false;
  return Y < NOW || e.status !== "ended";  // aujourd'hui : on masque ce qui est terminé
}
const dated = e => e.since ? `depuis ${e.since}${e.until ? ` jusqu'à ${e.until}` : ""}` : "début non daté";
const edgeList = D.edges.map((e,i) => ({id:"e"+i, from:e.from, to:e.to, arrows:"to", hidden: !activeAt(e, NOW),
  color:D.colors[e.types[0]]||"#888", dashes: e.status!=="active" || e.confidence==="low",
  width: e.confidence==="high"?2.2:1.2, title:`${(D.actors[e.from]||{}).name||e.from} → ${(D.actors[e.to]||{}).name||e.to} : ${e.types.join(", ")} (${dated(e)})`}));
// lien d'ancrage parti/personnalité → pays (calque détail)
const anchors = Object.entries(D.actors).filter(([id,a])=>DETAIL.has(a.kind) && D.actors[a.base])
  .map(([id,a]) => ({id:"b-"+id, from:id, to:a.base, dashes:[2,4], color:"#999", width:1, title:"rattaché à"}));

// ---------- Tensions : guerres, sanctions, revendications, rivalités — hors soutiens ----------
// Tracées sans effet sur la disposition du graphe (physics:false) ; atténuées si trêve ou cessez-le-feu.
const TENSION = {war:{label:"guerre", color:"#b91c1c", width:3.2, dashes:false, arrows:""},
  sanctions:{label:"sanctionne", color:"#7c3aed", width:1.8, dashes:[8,5], arrows:"to"},
  claims:{label:"revendique", color:"#d97706", width:1.8, dashes:[3,4], arrows:"to"},
  rivalry:{label:"rivalité", color:"#64748b", width:1.8, dashes:[10,6], arrows:""}};
const TS = D.tensions || [], BG = getComputedStyle(document.documentElement).getPropertyValue("--bg").trim();
const tensionTitle = t => `${(D.actors[t.from]||{}).name||t.from} ${t.type==="war"||t.type==="rivalry" ? "⟷" : "→"} ${(D.actors[t.to]||{}).name||t.to} : ${TENSION[t.type].label}${t.status==="reduced" ? " (trêve ou cessez-le-feu)" : ""} (${dated(t)})`;
const tensionEdges = TS.map((t,i) => { const s = TENSION[t.type];
  return {id:"t"+i, from:t.from, to:t.to, arrows:s.arrows, physics:false, width:s.width, label:s.label,
    color:{color:s.color, opacity: t.status==="active" ? 1 : .55}, dashes: t.status==="active" ? s.dashes : [2,6],
    smooth:{type:"curvedCW", roundness:.18}, font:{size:10, color:s.color, strokeWidth:3, strokeColor:BG},
    hidden: !activeAt(t, NOW), title: tensionTitle(t)}; });
const tensionsVisible = () => TS.map((t,i) => ({id:"t"+i, hidden: !$("#lyr-tensions").checked || !activeAt(t, YEAR())}));

const S0 = sizes("military");
const nodesDS = new vis.DataSet(Object.keys(D.actors).map(id=>nodeFor(id, S0[id])));
const edgesDS = new vis.DataSet([...edgeList, ...anchors, ...tensionEdges]);
const net = new vis.Network($("#graph"), {nodes:nodesDS, edges:edgesDS},
  {physics:{solver:"forceAtlas2Based", stabilization:{iterations:250}}, interaction:{hover:true}});
net.on("click", p => p.nodes.length ? show(p.nodes[0]) : legend());

// ---------- Vue « Organisations » : diagramme d'ensembles (Euler) ----------
// Un cercle par organisation cochée, d'aire proportionnelle à son nombre de membres ; les cercles sont placés pour
// que leurs chevauchements suivent le nombre de membres communs. Chaque pays est posé dans la zone qui correspond
// exactement à ses appartenances (Chine : dans BRICS et OCS, hors OTAN). Contours sans remplissage : aucun mélange.
const VU = 26;
// « Organisation de coopération de Shanghai (OCS) » → « OCS » ; « OTAN (article 5) » → « OTAN »
const shortName = n => { const m = n.match(/^(.*) \(([^)]*)\)$/); return !m ? n : /^[A-ZÉ]{2,6}$/.test(m[2]) ? m[2] : m[1]; };  // côté de la place réservée à un pays, en unités du dessin
function lens(r1, r2, d){ if(d >= r1 + r2) return 0; if(d <= Math.abs(r1 - r2)) return Math.PI*Math.min(r1,r2)**2;
  const a = r1*r1*Math.acos((d*d + r1*r1 - r2*r2)/(2*d*r1)), b = r2*r2*Math.acos((d*d + r2*r2 - r1*r1)/(2*d*r2));
  return a + b - .5*Math.sqrt((-d+r1+r2)*(d+r1-r2)*(d-r1+r2)*(d+r1+r2)); }
function targetDist(r1, r2, area){ let lo = Math.abs(r1 - r2), hi = r1 + r2;   // lens() décroît avec d
  if(area <= 0) return {d: hi + VU*.6, kind: "apart"};
  if(area >= Math.PI*Math.min(r1,r2)**2*.999) return {d: Math.max(0, lo - VU*.6), kind: "inside"};
  for(let k = 0; k < 50; k++){ const m = (lo + hi)/2; lens(r1, r2, m) > area ? lo = m : hi = m; }
  return {d: (lo + hi)/2, kind: "exact"}; }
function eulerLayout(sets){  // sets : [{id, members:Set}]
  const n = sets.length, cell = VU*VU*2.4;
  const C = sets.map((s, i) => ({...s, r: Math.sqrt(Math.max(1, s.members.size)*cell/Math.PI),
    x: 200*Math.cos(2*Math.PI*i/n), y: 200*Math.sin(2*Math.PI*i/n)}));
  const T = [];
  for(let i = 0; i < n; i++) for(let j = i+1; j < n; j++){
    const common = [...C[i].members].filter(m => C[j].members.has(m)).length;
    T.push({i, j, ...targetDist(C[i].r, C[j].r, common*cell)}); }
  for(let it = 0; it < 600; it++){ const lr = .12*(1 - it/700);   // descente de gradient sur l'écart aux distances cibles
    for(const t of T){ const a = C[t.i], b = C[t.j], dx = b.x - a.x, dy = b.y - a.y, d = Math.hypot(dx, dy) || .01;
      // cercles disjoints : rapprochés doucement (pas d'espace perdu) ; inclus : libres à l'intérieur
      let e = d - t.d; if(t.kind==="apart" && e > 0) e *= .15; if(t.kind==="inside" && e < 0) e = 0;
      const ux = dx/d*e*lr, uy = dy/d*e*lr; a.x += ux; a.y += uy; b.x -= ux; b.y -= uy; } }
  return C; }
function placeCountries(C, all){  // {iso: {x, y, ok}} ; ok = false si la zone exacte n'existe pas dans le dessin
  const minX = Math.min(...C.map(c => c.x - c.r)), maxX = Math.max(...C.map(c => c.x + c.r));
  const minY = Math.min(...C.map(c => c.y - c.r)), maxY = Math.max(...C.map(c => c.y + c.r));
  const pts = [], step = VU/3;
  for(let x = minX; x <= maxX; x += step) for(let y = minY; y <= maxY; y += step){
    const ins = C.map(c => Math.hypot(x - c.x, y - c.y) < c.r);
    if(!ins.some(Boolean)) continue;
    pts.push({x, y, sig: ins.map(Number).join(""), clear: Math.min(...C.map(c => Math.abs(Math.hypot(x - c.x, y - c.y) - c.r)))}); }
  const bySig = {}; all.forEach(iso => { const sig = C.map(c => c.members.has(iso) ? 1 : 0).join("");
    (bySig[sig] = bySig[sig] || []).push(iso); });
  const out = {}, taken = [];
  for(const [sig, isos] of Object.entries(bySig)){
    let cand = pts.filter(p => p.sig === sig), ok = cand.length > 0;
    if(!ok){ const score = p => [...sig].filter((b, k) => b === p.sig[k]).length;   // zone absente : la plus proche
      const best = Math.max(...pts.map(score)); cand = pts.filter(p => score(p) === best); }
    isos.sort((a, b) => cname(a).localeCompare(cname(b)));
    const chosen = [];
    for(const iso of isos){   // échantillonnage « le plus loin possible » : loin des bords et des pays déjà posés
      let best = null, bs = -Infinity;
      for(const p of cand){ const near = Math.min(VU*2, ...chosen.concat(taken).map(q => Math.hypot(p.x - q.x, p.y - q.y)));
        const sc = Math.min(near, VU*1.2) + Math.min(p.clear, VU*.7)*1.5; if(sc > bs){ bs = sc; best = p; } }
      chosen.push(best); out[iso] = {x: best.x, y: best.y, ok}; }
    taken.push(...chosen); }
  return out; }
function drawVenn(){ const box = $("#venn"); if(!document.body.classList.contains("venn")) return;
  const Y = YEAR(), sets = [...SEL.keys()].map(id => ({id, members: new Set(membersAt(GROUPS[id], Y))}));
  if(sets.length < 2){ box.innerHTML = `<p class="venn-empty mute">Coche au moins deux organisations dans « Organisations
    superposées » : chacune devient un cercle, et chaque pays se place à l'intersection des organisations dont il est membre.</p>`; return; }
  const C = eulerLayout(sets), all = [...new Set(sets.flatMap(s => [...s.members]))], P = placeCountries(C, all);
  // textes en pixels écran : on estime l'échelle du dessin, puis on agrandit le cadre pour y faire tenir les noms
  const W = Math.max(200, box.clientWidth - 24), H = Math.max(200, box.clientHeight - 142);
  let minX = Math.min(...C.map(c => c.x - c.r)), maxX = Math.max(...C.map(c => c.x + c.r));
  let minY = Math.min(...C.map(c => c.y - c.r)), maxY = Math.max(...C.map(c => c.y + c.r));
  const k = Math.min(W/(maxX - minX + 60), H/(maxY - minY + 60)), px = v => v/k;
  const f = VU*.36, placed = [];
  // nom de l'organisation au-dessus de son cercle ; remonté d'une ligne s'il chevaucherait un nom déjà posé
  const labels = [...C].sort((a, b) => (a.y - a.r) - (b.y - b.r)).map(c => {
    const text = `${shortName(GROUPS[c.id].name)} · ${c.members.size}`, w = px(text.length*7.2);
    let ly = c.y - c.r - px(9);
    while(placed.some(p => Math.abs(p.y - ly) < px(16) && Math.abs(p.x - c.x) < (p.w + w)/2 + px(8))) ly -= px(16);
    placed.push({x: c.x, y: ly, w});
    minX = Math.min(minX, c.x - w/2); maxX = Math.max(maxX, c.x + w/2); minY = Math.min(minY, ly - px(10));
    return `<text x="${c.x.toFixed(1)}" y="${ly.toFixed(1)}" fill="${SEL.get(c.id)}" font-weight="600" font-size="${px(13).toFixed(2)}"
      text-anchor="middle" stroke="var(--bg)" stroke-width="${px(4).toFixed(2)}" paint-order="stroke">${esc(text)}</text>`; }).join("");
  minX -= px(12); maxX += px(12); minY -= px(12); maxY += px(16);
  const off = all.filter(iso => !P[iso].ok);
  box.innerHTML = `<svg viewBox="${minX} ${minY} ${maxX - minX} ${maxY - minY}" preserveAspectRatio="xMidYMid meet" role="img"
      aria-label="Diagramme d'ensembles des organisations cochées">
    <defs><clipPath id="vclip" clipPathUnits="objectBoundingBox"><circle cx=".5" cy=".5" r=".5"/></clipPath></defs>
    ${C.map(c => `<circle cx="${c.x.toFixed(1)}" cy="${c.y.toFixed(1)}" r="${c.r.toFixed(1)}" fill="none" stroke="${SEL.get(c.id)}" stroke-width="2.5"/>`).join("")}
    ${all.map(iso => { const p = P[iso];
      return `<g class="vc" data-country="${esc(iso)}" transform="translate(${p.x.toFixed(1)},${p.y.toFixed(1)})"><title>${cname(iso)} — ${
        sets.filter(s => s.members.has(iso)).map(s => esc(GROUPS[s.id].name)).join(" · ")}${p.ok ? "" : " (zone impossible à dessiner avec des cercles : placé au plus près)"}</title>
        <circle r="${f + 1.5}" fill="var(--card)" stroke="${p.ok ? "var(--line)" : "var(--fg)"}" ${p.ok ? "" : 'stroke-dasharray="2 2"'}/>
        <image href="${flag(iso)}" x="${-f}" y="${-f}" width="${2*f}" height="${2*f}" clip-path="url(#vclip)"/>
        <text y="${(f + px(10)).toFixed(1)}" text-anchor="middle" font-size="${px(10).toFixed(2)}" fill="var(--fg)"
          stroke="var(--bg)" stroke-width="${px(3).toFixed(2)}" paint-order="stroke">${cname(iso)}</text></g>`; }).join("")}
    ${labels}
  </svg>${off.length ? `<p class="venn-note mute">${off.length} pays dans une combinaison que des cercles ne peuvent pas représenter (contour pointillé) : placés dans la zone la plus proche.</p>` : ""}`; }
function refresh(){
  const S = sizes($("#metric").value);
  const sz = id => ["state","bloc"].includes(D.actors[id].kind) ? S[id] : Math.max(S[id], D.actors[id].kind==="person" ? 18 : 14);
  nodesDS.update(Object.keys(D.actors).map(id=>({id, size:sz(id), font:{color:fg, size:11+Math.round(sz(id)/7)},
    hidden: !visible(layer(id))}))); }
["metric","lyr-armed","lyr-detail"].forEach(i => $("#"+i).addEventListener("change", refresh));
$("#lyr-tensions").addEventListener("change", () => edgesDS.update(tensionsVisible()));
function onYear(){ const Y = YEAR();
  $("#year-label").textContent = String(Y);
  edgesDS.update([...D.edges.map((e,i) => ({id:"e"+i, hidden: !activeAt(e, Y)})), ...tensionsVisible()]);
  drawVenn();
  if($("#layers-panel")) showLayers(); }
$("#year").addEventListener("input", onYear); onYear();
$("#metric").addEventListener("change", () => map && drawMarkers());

// ---------- Vue carte : une couche Leaflet par type d'acteur, chacun dans son pays ----------
const WORLD = "https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json";  // Natural Earth, domaine public
const css = v => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
const MAP_LAYERS = {core:"États & blocs", non_state:"Groupes armés", party:"Partis", person:"Personnalités", links:"Liens de soutien", tensions:"Tensions"};
let map, groups, linkLayers = [], countries;
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
  drawTensions();
  groups.links.clearLayers(); linkLayers = [];
  const on = k => map.hasLayer(groups[k]);
  D.edges.filter(e => activeAt(e, YEAR())).forEach(e => {
    const a = POS[e.from], b = POS[e.to];
    if(!a || !b || !on(layerOf(e.from)) || !on(layerOf(e.to))) return;
    const l = L.polyline(curve(a,b), {color: D.colors[e.types[0]]||"#888", weight: e.confidence==="high"?2.2:1.4,
      opacity:.8, dashArray: e.status!=="active"||e.confidence==="low" ? "5 5" : null})
      .bindTooltip(`${D.actors[e.from].name} → ${D.actors[e.to].name} : ${e.types.join(", ")} (${dated(e)})`, {sticky:true})
      .addTo(groups.links);
    // flèche : petit cercle plein côté bénéficiaire
    const tip = L.circleMarker(b, {radius:3, color: D.colors[e.types[0]]||"#888", fillOpacity:1, weight:0, interactive:false}).addTo(groups.links);
    linkLayers.push({e, l, tip}); }); }
// Tensions sur la carte : traits droits, distincts des liens de soutien (courbes)
function drawTensions(){ groups.tensions.clearLayers();
  const on = k => map.hasLayer(groups[k]);
  TS.filter(t => activeAt(t, YEAR())).forEach(t => { const a = POS[t.from], b = POS[t.to], s = TENSION[t.type];
    if(!a || !b || !on(layerOf(t.from)) || !on(layerOf(t.to))) return;
    L.polyline([a, b], {color:s.color, weight: s.width + .6, opacity: t.status==="active" ? .9 : .45,
      dashArray: t.status!=="active" ? "2 6" : s.dashes ? s.dashes.join(" ") : null})
      .bindTooltip(tensionTitle(t), {sticky:true}).addTo(groups.tensions); }); }
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
  const formalTip = iso => `${cname(iso)}${blocColor(iso) ? " — " + (inf(iso).role==="contested" ? "disputé" : esc(BLOCS[inf(iso).bloc].name) + (inf(iso).role==="member" ? `, niveau ${inf(iso).level}/3` : ", satellite")) : ""}`;
  const votesTip = iso => leanAt(iso) == null ? `${cname(iso)} — pas de données de vote pour ${voteYear()}`
    : voteYear() === U.agreement_year && UC[iso] ? `${cname(iso)} — vote comme France/Allemagne ${pct(UC[iso].west)}, comme Russie/Chine ${pct(UC[iso].axis)} (${U.agreement_year})`
    : `${cname(iso)} — penchant ${leanAt(iso) > 0 ? "+" : ""}${leanAt(iso).toFixed(2)} en ${voteYear()} (+ = vote comme France/Allemagne, − = comme Russie/Chine)`;
  const style = f => { const iso = byNum[String(+f.id)], votes = $("#colormode").value==="votes";
    const c = iso && (votes ? votesColor(iso) : blocColor(iso) && mix(blocColor(iso), css("--land"), TINT[inf(iso).level] || .25));
    // organisations cochées : fond neutre, chaque pays prend la couleur de ses organisations (rayures si plusieurs)
    if(SEL.size) return {color: css("--line"), weight: .6, fillOpacity: 1, fillColor: orgFill(iso) || css("--land")};
    return {color: css("--line"), weight: .6, fillOpacity: 1,
            fillColor: c || (iso && D.actors[iso] ? css("--land-hl") : css("--land"))}; };
  const orgTip = iso => { const ids = [...SEL.keys()].filter(id => membersAt(GROUPS[id], YEAR()).includes(iso));
    return ids.length ? "<br>" + ids.map(id => sw(SEL.get(id)) + esc(GROUPS[id].name)).join("<br>") : ""; };
  countries = L.geoJSON(world, {style,
    onEachFeature: (f, l) => { const iso = byNum[String(+f.id)];
      if(!iso) return;
      l.bindTooltip(() => SEL.size ? cname(iso) + orgTip(iso) : ($("#colormode").value==="votes" ? votesTip : formalTip)(iso), {sticky:true});
      l.on("click", () => D.actors[iso] ? show(iso) : showCountry(iso)); }
  }).addTo(map);
  $("#colormode").addEventListener("change", () => countries.setStyle(style));
  $("#year").addEventListener("input", () => { drawOrgs(); drawLinks(); });
  drawOrgs.restyle = () => countries.setStyle(style);
  groups = Object.fromEntries(Object.keys(MAP_LAYERS).map(k => [k, L.layerGroup().addTo(map)]));
  L.control.layers(null, Object.fromEntries(Object.entries(MAP_LAYERS).map(([k,label]) => [label, groups[k]])),
    {collapsed: innerWidth < 800, position:"bottomleft"}).addTo(map);
  // différé : pendant l'événement de retrait, la couche est encore attachée à la carte et y ajouterait les liens
  map.on("overlayadd overlayremove", () => setTimeout(drawLinks));
  drawOrgs(); drawMarkers(); drawLinks(); }
function drawOrgs(){ if(drawOrgs.restyle) drawOrgs.restyle(); }
// Remplissage d'un pays selon les organisations cochées dont il est membre l'année choisie : couleur unie pour une,
// rayures juxtaposées pour plusieurs. Les teintes ne se mélangent jamais : chaque couleur reste celle d'une organisation.
const STRIPE = 5;
function orgFill(iso){ if(!iso) return null; const Y = YEAR();
  const cs = [...SEL].filter(([id]) => membersAt(GROUPS[id], Y).includes(iso)).map(([,c]) => tint(c));
  if(cs.length < 2) return cs[0] || null;
  const pid = "stripes-" + cs.map(c => c.slice(1)).join("-");
  if(!document.getElementById(pid)){
    let defs = document.getElementById("org-defs");
    if(!defs){ document.body.insertAdjacentHTML("beforeend",
      '<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs id="org-defs"></defs></svg>');
      defs = document.getElementById("org-defs"); }
    defs.insertAdjacentHTML("beforeend", `<pattern id="${pid}" patternUnits="userSpaceOnUse" width="${cs.length*STRIPE}"
      height="${cs.length*STRIPE}" patternTransform="rotate(45)">${cs.map((c,i) =>
      `<rect x="${i*STRIPE}" y="0" width="${STRIPE}" height="${cs.length*STRIPE}" fill="${c}"/>`).join("")}</pattern>`); }
  return `url(#${pid})`; }

function setView(v){
  document.body.classList.toggle("map", v==="map"); document.body.classList.toggle("venn", v==="venn");
  ["graph","map","venn"].forEach(k => $("#v-"+k).setAttribute("aria-pressed", v===k));
  if(v==="map"){ if(!map) initMap(); else map.invalidateSize(); }
  if(v==="venn"){
    // première visite : une sélection parlante plutôt qu'une liste vide
    if(!SEL.size) document.querySelectorAll("#orgs input").forEach(i => i.checked = ["nato","eu","brics","sco"].includes(i.value));
    if(!SEL.size) syncOrgs(); else drawVenn(); } }
$("#v-venn").addEventListener("click", () => setView("venn"));
$("#v-graph").addEventListener("click", () => setView("graph"));
$("#v-map").addEventListener("click", () => setView("map"));

function f(v, unit="", d=1){ if(!v) return "n/d"; let x=v.value, s;
  s = Math.abs(x)>=1e9 ? (x/1e9).toFixed(d)+" Md" : Math.abs(x)>=1e6 ? (x/1e6).toFixed(d)+" M" : x.toLocaleString("fr-FR",{maximumFractionDigits:d});
  return `${s}${unit} <span class="mute">(${v.year})</span>`; }
const tags = t => t.map(x=>`<span class="tag" style="background:${D.colors[x]||'#888'}">${esc(x)}</span>`).join("");
// source → lien court vers le site (texte complet au survol) ; sans URL, le texte tel quel
const src = s => { const m = String(s).match(/https?:\/\/[^\s<]+/); if(!m) return esc(s);
  let host = m[0]; try { host = new URL(m[0]).hostname.replace(/^www\./, ""); } catch(_) {}
  return `<a href="${esc(m[0])}" target="_blank" rel="noopener" title="${esc(String(s).slice(0, m.index).replace(/[\s—]+$/, ""))}">${esc(host)}</a>`; };
const STATUS_FR = {active:"actif", reduced:"en baisse", ended:"terminé", alleged:"allégué"};
const CONF_FR = {high:"documenté officiellement", medium:"sources concordantes", low:"allégations"};
const rel = (e, other) => `<div class="rel"><b data-id="${esc(other)}">${nm(other)}</b> <span class="mute">${esc(e.types.map(t => ({arms:"armes", troops:"troupes", financial:"argent", training:"entraînement", intelligence:"renseignement", political:"politique", economic:"économique", dual_use:"double usage"})[t] || t).join(", "))}</span>
  ${e.why ? `<div>${esc(e.why)}</div>` : ""}
  <div class="mute">${esc(STATUS_FR[e.status] || e.status)}, ${esc(CONF_FR[e.confidence] || e.confidence)}, ${esc(dated(e))}. ${e.note ? esc(e.note) + ". " : ""}Sources : ${(e.sources||[]).map(src).join(", ")}</div></div>`;
document.addEventListener("click", ev => { const b = ev.target.closest("[data-id]"); if(b) show(b.dataset.id); });


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
  h += leaderLine(id);
  if(blocLine(id)) h += `<p class="mute">${blocLine(id)}</p>`;
  if(ungaLine(id)) h += `<p class="mute">${ungaLine(id)}</p>`;
  if(forumLine(id)) h += `<p class="mute">${forumLine(id)}</p>`;
  h += tiers(id) + euCohesion(id) + (id==="US" || id==="EU" ? driftBlock() : "");
  if(a.note) h += `<p>${esc(a.note)}${(a.sources||[]).length?`<br><span class="mute">${a.sources.map(src).join(", ")}</span>`:""}</p>`;
  h += credit(id) + credit(leaderKey(id));
  if(members.length){
    h += `<h2>Membres suivis (${members.length})</h2><p class="mute">Surlignés sur le graphe.</p>` + members.map(m => {
      const out = D.edges.filter(e=>e.from===m && e.status!=="ended");
      return `<div class="rel"><b data-id="${esc(m)}">${nm(m)}</b> <span class="mute">→ ${out.length ? out.map(e=>nm(e.to)).join(", ") : "aucun soutien recensé"}</span></div>`; }).join(""); }
  const local = Object.keys(D.actors).filter(x=>DETAIL.has(D.actors[x].kind) && D.actors[x].base===id);
  if(local.length) h += `<h2>Partis & personnalités</h2>` + local.map(x=>`<div class="rel"><b data-id="${esc(x)}">${nm(x)}</b> <span class="mute">${esc(KIND[D.actors[x].kind])}</span></div>`).join("");
  const out = D.edges.filter(e=>e.from===id&&e.status!=="ended"), inn = D.edges.filter(e=>e.to===id&&e.status!=="ended");
  if(out.length) h += `<h2>Soutient</h2>` + out.map(e=>rel(e,e.to)).join("");
  if(inn.length) h += `<h2>Soutenu par</h2>` + inn.map(e=>rel(e,e.from)).join("");
  const tens = TS.filter(t => (t.from===id || t.to===id) && t.status!=="ended");
  if(tens.length) h += `<h2>Tensions</h2>` + tens.map(t => { const other = t.from===id ? t.to : t.from, s = TENSION[t.type];
    const verb = t.type==="sanctions" ? (t.from===id ? "sanctionne" : "sanctionné par") : t.type==="claims" ? (t.from===id ? "revendique un territoire de" : "territoire revendiqué par") : s.label + " avec";
    return `<div class="rel"><b style="color:${s.color}">■</b> ${esc(verb[0].toUpperCase() + verb.slice(1))} <b data-id="${esc(other)}">${nm(other)}</b>
      <div class="mute">${t.status==="reduced" ? "trêve ou cessez-le-feu · " : ""}${esc(dated(t))} · ${(t.sources||[]).map(src).join(", ")}${t.note ? "<br>"+esc(t.note) : ""}</div></div>`; }).join("");
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
    ${ungaLine(iso) ? `<p class="mute">${ungaLine(iso)}</p>` : ""}
    ${forumLine(iso) ? `<p class="mute">${forumLine(iso)}</p>` : ""}
    ${i.ties.some(t => GROUPS[t].kind!=="forum") ? "<h2>Liens formels</h2>" : ""}` + i.ties.filter(t => GROUPS[t].kind!=="forum").map(t => { const g = GROUPS[t];
      return `<div class="rel"><b>${esc(g.name)}</b> <span class="mute">${g.level ? `niveau ${g.level}/3` : "sans effet sur l'alignement"}
        ${g.note ? "<br>"+esc(g.note) : ""}<br>${g.sources.map(src).join(", ")}</span></div>`; }).join("")
    + `<p class="mute">Ce pays n'a ${i.ties.some(t => GROUPS[t].kind!=="forum") ? "encore" : "ni lien formel dans alignments.yaml, ni"} aucune relation de soutien sourcée dans network.yaml.</p>`; }
function legend(){
  if(map) highlightLinks(null);
  const key = (color, label) => `<span class="key"><i style="background:${color}"></i>${esc(label)}</span>`;
  const TYPES_FR = {arms:"armes", troops:"troupes", financial:"argent", training:"entraînement", intelligence:"renseignement",
    political:"politique", economic:"économique", dual_use:"double usage"};
  $("#panel").innerHTML = `<h1>Explorer</h1>
  <p>Cliquez sur un acteur, un pays ou un lien pour voir ce qui les relie, avec les sources.</p>
  <p class="mute">Pour commencer simplement, lisez un dossier : ${(D.dossiers||[]).map(x => `<a href="${esc(x.id)}.html">${esc(x.title.replace(/^La guerre /, "la guerre "))}</a>`).join(", ")}.</p>
  <h2>Lire le graphe</h2>
  <dl class="keys">
    <dt>Formes</dt><dd>Drapeau : un État ou un bloc. Épées : un groupe armé. Urne : un parti. Photo : une personnalité.</dd>
    <dt>Traits</dt><dd>Plein : soutien actif et confirmé. Pointillé : en baisse ou allégué.</dd>
    <dt>Soutiens</dt><dd>${Object.keys(D.colors).map(k => key(D.colors[k], TYPES_FR[k] || k)).join("")}</dd>
    <dt>Tensions</dt><dd>${Object.values(TENSION).map(t => key(t.color, t.label)).join("")}</dd>
    <dt>Blocs</dt><dd>${Object.values(BLOCS).map(b => key(b.color, b.name)).join("")}${key(CONTESTED, "disputé")}</dd>
    <dt>Taille</dt><dd>Dépenses militaires, PIB ou nombre de soutiens, selon les réglages.</dd>
  </dl>
  <p class="mute" style="margin-top:26px">Blocs, votes à l'ONU, curseur Année, organisations : tout est expliqué dans la
  <a href="methode.html">méthode</a>. Données réutilisables : <a href="network.json">JSON</a>, <a href="network.csv">CSV</a>
  (CC BY 4.0). Mis à jour le ${esc(D.built.slice(0,10).split("-").reverse().join("/"))}.</p>`; }
legend();
// Liens directs (accueil, menu Explorer) : #graphe, #carte, #organisations, #graphe:<id acteur>
// — aussi quand on est déjà sur la page : le menu change l'ancre sans recharger
function route(){ const [v, id] = decodeURIComponent(location.hash.slice(1)).split(":");
  const view = {carte:"map", organisations:"venn", graphe:"graph"}[v];
  if(view) setView(view);
  if(id && D.actors[id]) show(id);
  document.querySelectorAll("details.menu[open]").forEach(d => d.open = false); }
route();
addEventListener("hashchange", route);
</script></body></html>"""

if __name__ == "__main__":
    build()
