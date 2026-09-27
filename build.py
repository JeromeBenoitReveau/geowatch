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
    data = {"actors": actors, "edges": edges, "profiles": profiles, "colors": TYPE_COLORS,
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
<style>
:root{--bg:#fafaf8;--fg:#1c1c1c;--mute:#6b6b6b;--line:#e3e3df;--card:#fff}
@media (prefers-color-scheme:dark){:root{--bg:#141414;--fg:#eee;--mute:#9a9a9a;--line:#2c2c2c;--card:#1d1d1d}}
*{box-sizing:border-box}body{margin:0;font:14px/1.45 system-ui,sans-serif;background:var(--bg);color:var(--fg);
display:grid;grid-template-columns:1fr 380px;height:100vh}
@media (max-width:800px){body{grid-template-columns:1fr;grid-template-rows:60vh auto;height:auto}}
#stage{position:relative;border-right:1px solid var(--line);min-height:60vh}#graph{position:absolute;inset:0}
#controls{position:absolute;top:10px;left:10px;z-index:1;background:var(--card);border:1px solid var(--line);
border-radius:8px;padding:8px 10px;font-size:12px;display:flex;flex-direction:column;gap:4px;max-width:calc(100% - 20px)}
#controls select{font:inherit;background:var(--card);color:var(--fg);border:1px solid var(--line);border-radius:4px}
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
<div id="stage"><div id="graph"></div>
<div id="controls">
  <label>Taille des acteurs : <select id="metric">
    <option value="military">dépenses militaires ($)</option><option value="gdp">PIB ($)</option>
    <option value="supports">nombre de soutiens accordés</option></select></label>
  <label><input type="checkbox" id="lyr-armed" checked> Groupes armés non étatiques</label>
  <label><input type="checkbox" id="lyr-detail"> Partis & personnalités</label>
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
  return {id, label:a.name, size, shape: pic ? "circularImage" : SHAPE[a.kind]||"dot",
    image: pic ? flag(id) : undefined,
    color: DETAIL.has(a.kind) ? {background:"#e7e2f5", border:"#6b4fbb"} : undefined,
    borderWidth: pic ? 1 : 1.5, font:{color:fg, size: 11 + Math.round(size/7)},
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
  nodesDS.update(Object.keys(D.actors).map(id=>({id, size:S[id], font:{color:fg, size:11+Math.round(S[id]/7)},
    hidden: !visible(layer(id))}))); }
["metric","lyr-armed","lyr-detail"].forEach(i => $("#"+i).addEventListener("change", refresh));

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
  const iso = (a.kind==="state" || a.kind==="bloc") ? id : a.base;
  const p = D.profiles[iso];
  let h = `<h1>${nm(id)}</h1><div class="mute">${esc(KIND[a.kind]||a.kind)}${a.base&&a.kind!=="state"?" · "+nm(a.base)+" ("+esc(a.base)+")":""}${(a.member_of||[]).length?" · membre : "+a.member_of.map(nm).join(", "):""}</div>`;
  if(a.note) h += `<p>${esc(a.note)}${(a.sources||[]).length?`<br><span class="mute">${a.sources.map(src).join(" ; ")}</span>`:""}</p>`;
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
function legend(){
  const all = Object.values(D.markets).flatMap(v=>v.markets).filter(m=>!m.stale);
  const moves = all.filter(m=>m.delta_pts!=null && Math.abs(m.delta_pts)>=D.alert)
                   .sort((a,b)=>Math.abs(b.delta_pts)-Math.abs(a.delta_pts));
  $("#panel").innerHTML = `<h1>Réseau de soutiens</h1><p class="mute">Clique un acteur ; clique un bloc (UE) pour voir ses membres.
  Drapeau = État ou bloc · ◆ groupe armé · ■ parti · ▲ personnalité. Trait plein = actif & confirmé,
  pointillé = réduit / allégué ; pointillé gris = rattachement d'un parti ou d'une personne à son pays.</p>
  <p class="mute">Taille = dépenses militaires ou PIB en dollars (Banque mondiale, dernière année disponible)
  ou nombre de soutiens accordés — voir le sélecteur. Sans donnée (Taïwan, groupes armés…) : taille minimale.</p>
  <h2>Types</h2><div class="legend">${tags(Object.keys(D.colors))}</div>
  <h2>Mouvements de marché ≥ ${D.alert} pts sur 7 j</h2>${moves.length ? moves.map(mkt).join("")
    : `<p class="mute">Aucun${all.length?"":" — pas encore de cotes relevées"}.</p>`}
  <p class="mute">Les seuls pourcentages affichés sont des cotes de marchés de prédiction (Polymarket, Kalshi).
  Données du graphe : <a href="network.json">JSON</a> · <a href="network.csv">CSV</a>, licence CC BY 4.0.
  Généré le ${esc(D.built.slice(0,16).replace("T"," "))} UTC.</p>`; }
legend();
</script></body></html>"""

if __name__ == "__main__":
    build()
