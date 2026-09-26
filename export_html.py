"""python export_html.py → geowatch.html (graphe interactif + fiches pays), à ouvrir dans un navigateur."""
from dotenv import load_dotenv; load_dotenv()
import json
import db, network

TYPE_COLORS = {"arms": "#d64545", "troops": "#8b1e1e", "financial": "#2f8f5b", "training": "#c98a1b",
               "intelligence": "#6b4fbb", "political": "#3a6fd8", "economic": "#1f9aa5", "dual_use": "#b0569a"}

def build():
    actors, edges = network.load()
    c = db.conn()
    profiles = {}
    for aid, a in actors.items():
        iso = aid if a["kind"] == "state" else a.get("base")
        if iso:
            p, fetched = db.get_profile(c, iso)
            if p:
                profiles[iso] = {**p, "fetched_at": fetched}
    data = {"actors": actors, "edges": edges, "profiles": profiles, "colors": TYPE_COLORS}
    html = TEMPLATE.replace("__DATA__", json.dumps(data, ensure_ascii=False))
    open("geowatch.html", "w", encoding="utf-8").write(html)
    print("→ geowatch.html")

TEMPLATE = r"""<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>geowatch — réseau de soutiens</title>
<script src="https://cdn.jsdelivr.net/npm/vis-network@10.1.2/standalone/umd/vis-network.min.js"></script>
<style>
:root{--bg:#fafaf8;--fg:#1c1c1c;--mute:#6b6b6b;--line:#e3e3df;--card:#fff}
@media (prefers-color-scheme:dark){:root{--bg:#141414;--fg:#eee;--mute:#9a9a9a;--line:#2c2c2c;--card:#1d1d1d}}
*{box-sizing:border-box}body{margin:0;font:14px/1.45 system-ui,sans-serif;background:var(--bg);color:var(--fg);
display:grid;grid-template-columns:1fr 380px;height:100vh}
@media (max-width:800px){body{grid-template-columns:1fr;grid-template-rows:55vh auto;height:auto}}
#graph{border-right:1px solid var(--line);min-height:55vh}
aside{padding:20px;overflow:auto}
h1{font-size:20px;margin:0 0 4px}h2{font-size:12px;text-transform:uppercase;letter-spacing:.06em;color:var(--mute);margin:20px 0 6px}
.kv{display:grid;grid-template-columns:140px 1fr;gap:3px 10px}.kv span:nth-child(odd){color:var(--mute)}
.rel{padding:6px 0;border-bottom:1px solid var(--line)}.rel b{cursor:pointer}
.tag{display:inline-block;font-size:11px;padding:1px 6px;border-radius:9px;color:#fff;margin:2px 2px 0 0}
.mute{color:var(--mute);font-size:12px}.legend .tag{margin-right:4px}
</style></head><body>
<div id="graph"></div>
<aside id="panel"></aside>
<script>
const D = __DATA__;
const $ = s => document.querySelector(s);
const nm = id => (D.actors[id]||{}).name || id;
const shape = {state:"dot", non_state:"diamond", bloc:"hexagon"};

const nodes = Object.entries(D.actors).map(([id,a]) => ({id, label:a.name, shape:shape[a.kind]||"dot",
  size: a.kind==="state"?16:12, font:{color:getComputedStyle(document.body).color}}));
const edges = D.edges.filter(e=>e.status!=="ended").map((e,i) => ({id:i, from:e.from, to:e.to, arrows:"to",
  color:D.colors[e.types[0]]||"#888", dashes: e.status!=="active" || e.confidence==="low",
  width: e.confidence==="high"?2.2:1.2, title:`${nm(e.from)} → ${nm(e.to)} : ${e.types.join(", ")}`}));

const net = new vis.Network($("#graph"), {nodes, edges},
  {physics:{solver:"forceAtlas2Based", stabilization:{iterations:200}}, interaction:{hover:true}});
net.on("click", p => p.nodes.length ? show(p.nodes[0]) : legend());

function f(v, unit="", d=1){ if(!v) return "n/d"; let x=v.value, s;
  s = Math.abs(x)>=1e9 ? (x/1e9).toFixed(d)+" Md" : Math.abs(x)>=1e6 ? (x/1e6).toFixed(d)+" M" : x.toLocaleString("fr-FR",{maximumFractionDigits:d});
  return `${s}${unit} <span class="mute">(${v.year})</span>`; }
const tags = t => t.map(x=>`<span class="tag" style="background:${D.colors[x]||'#888'}">${x}</span>`).join("");
const rel = (e, other) => `<div class="rel"><b onclick="show('${other}')">${nm(other)}</b> ${tags(e.types)}
  <div class="mute">${e.status} · confiance ${e.confidence} · ${(e.sources||[]).join(" ; ")}${e.note?"<br>"+e.note:""}</div></div>`;

function show(id){
  net.selectNodes([id]); const a = D.actors[id]||{}; const iso = a.kind==="state" ? id : a.base;
  const p = D.profiles[iso]; let h = `<h1>${nm(id)}</h1><div class="mute">${a.kind}${a.base&&a.kind!=="state"?" · basé : "+nm(a.base)+" ("+a.base+")":""}</div>`;
  const out = D.edges.filter(e=>e.from===id&&e.status!=="ended"), inn = D.edges.filter(e=>e.to===id&&e.status!=="ended");
  if(out.length) h += `<h2>Soutient</h2>` + out.map(e=>rel(e,e.to)).join("");
  if(inn.length) h += `<h2>Soutenu par</h2>` + inn.map(e=>rel(e,e.from)).join("");
  if(p){ const g=p.government||{}, t=p.population_trend;
    if(a.kind!=="state") h += `<h2>Pays hôte : ${nm(iso)}</h2>`;
    h += `<h2>Régime</h2><div class="kv"><span>Forme</span><span>${(g.forms||[]).join(", ")||"n/d"}</span>
      <span>Chef d'État</span><span>${(g.head_of_state||[]).join(", ")||"n/d"}</span></div>
    <h2>Démographie</h2><div class="kv"><span>Population</span><span>${f(p.population)}</span>
      <span>Tendance</span><span>${t?`${t.label} (${t.annual_rate_pct>0?"+":""}${t.annual_rate_pct} %/an, ${t.period})${t.below_replacement?"<br>fécondité sous le renouvellement":""}`:"n/d"}</span>
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
      <span>Défense</span><span>${f(p.military_pct_gdp," % PIB")}</span></div>
    <p class="mute">Profil du ${p.fetched_at.slice(0,10)} — ${p.sources.join(", ")}</p>`;
  } else if(iso) h += `<p class="mute">Pas de profil — lancer <code>python ingest.py --profiles</code></p>`;
  $("#panel").innerHTML = h;
}
function legend(){ $("#panel").innerHTML = `<h1>Réseau de soutiens</h1><p class="mute">Clique un acteur.
  ● État · ◆ non étatique · ⬡ bloc. Trait plein = actif & confirmé, pointillé = réduit / allégué.</p>
  <h2>Types</h2><div class="legend">${tags(Object.keys(D.colors))}</div>`; }
legend();
</script></body></html>"""

if __name__ == "__main__":
    build()
