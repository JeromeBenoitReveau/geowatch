"""Page « Croiser » (site/croiser.html) : on choisit au moins deux entités (pays, groupe, conflit) et la page dessine
ce que le graphe contient ENTRE elles — tensions, soutiens, médiations, leviers. Aucun texte rédigé : chaque trait
est un fait de network.yaml, affiché avec sa date, son statut et ses sources. Un conflit apporte les acteurs de ses camps.
État dans l'URL (croiser.html?e=US,d:ukraine,CN), donc partageable."""
from html import escape as e
import json
import brand, dossier, glossary, style

CSS = """
.cross{padding:56px 0 0}.cross h1{margin-bottom:8px}
.pick{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:22px 0 6px}
.chip{display:inline-flex;align-items:center;gap:7px;padding:5px 6px 5px 10px;border:1px solid var(--mist);border-radius:4px;background:var(--land);font-size:15px}
.chip img,.fact img,.ex img{width:16px;height:16px;border-radius:50%;object-fit:cover;box-shadow:0 0 0 1px var(--mist);flex:none}
.chip button{background:none;border:0;color:var(--graphite);cursor:pointer;font-size:16px;line-height:1;padding:2px 4px;border-radius:3px}
.chip button:hover{color:var(--ink)}
#addbtn{font:15px var(--sans);color:var(--ink);background:none;border:1px dashed var(--graphite);border-radius:4px;padding:5px 12px;cursor:pointer}
#addbtn::before{content:"+ ";color:var(--graphite)}#addbtn:hover,#addbtn[aria-expanded=true]{border-color:var(--peach);border-style:solid}
/* panneau de choix : tout est visible d'un coup, rangé par catégorie ; le champ ne fait que filtrer cette liste */
.picker{position:relative}.pick{position:relative;z-index:1002}
#panel{position:absolute;left:0;right:0;top:100%;z-index:1002;border:1px solid var(--mist);border-radius:6px;background:var(--land);padding:14px 16px 6px;margin:8px 0 4px;
  max-height:70vh;overflow:auto;box-shadow:0 12px 32px #0003}
/* voile derrière le panneau ouvert : le reste de la page s'efface, la sélection reste lisible au-dessus */
#veil{position:fixed;inset:0;z-index:1001;background:color-mix(in srgb,var(--paper) 78%,transparent)}
#q{font:15px var(--sans);color:var(--ink);background:var(--paper);border:1px solid var(--mist);border-radius:4px;padding:7px 10px;width:100%;max-width:340px}
#groups h3{font:500 13.5px var(--sans);color:var(--graphite);margin:14px 0 7px}
#groups .g{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 6px}
#groups button{display:inline-flex;align-items:center;gap:6px;font:14px var(--sans);color:var(--ink);background:none;border:1px solid var(--mist);border-radius:4px;padding:4px 9px;cursor:pointer}
#groups button:hover{border-color:var(--peach)}#groups button:disabled{color:var(--graphite);opacity:.45;cursor:default;border-color:var(--mist)}
#groups img{width:15px;height:15px;border-radius:50%;object-fit:cover;box-shadow:0 0 0 1px var(--mist)}
.scope{font-size:13.5px;color:var(--graphite);margin:0;min-height:1.6em}
.scope button{display:inline;text-align:left;background:none;border:0;padding:0;font:inherit;color:inherit;cursor:pointer;text-decoration:underline;text-decoration-color:var(--peach);text-underline-offset:3px}
.sug{display:flex;flex-wrap:wrap;align-items:center;gap:8px;font-size:13.5px;color:var(--graphite);margin:10px 0 0}
.sug:empty{display:none}
.sug button{display:inline-flex;align-items:center;gap:6px;font:14px var(--sans);color:var(--ink);background:none;border:1px dashed var(--graphite);border-radius:4px;padding:4px 9px;cursor:pointer}
.sug button:hover{border-color:var(--peach);border-style:solid}.sug button::before{content:"+";color:var(--graphite)}
.sug img{width:15px;height:15px;border-radius:50%;object-fit:cover}.sug small{color:var(--graphite);font-size:12px}
.ex{display:flex;flex-direction:column;gap:10px;margin:28px 0 0;font-size:16px}
.ex a{display:inline-flex;align-items:center;gap:8px;flex-wrap:wrap}
#schema{display:block;width:100%;height:auto;margin:10px 0 0;overflow:visible}
#schema text{font-family:var(--sans);fill:var(--ink)}
#schema .lab{font-size:14px}#schema .val{font-size:12px;fill:var(--ink);font-variant-numeric:tabular-nums}#schema .pill{fill:var(--paper);stroke:var(--mist)}
#schema .hit{stroke:transparent;stroke-width:16;fill:none;cursor:pointer}
#schema .node{cursor:pointer}#schema .ring{fill:var(--land);stroke:var(--mist);stroke-width:1.5}
#schema .node.extra .ring{stroke-dasharray:3 3}#schema .node.on .ring{stroke:var(--peach);stroke-width:2.5}
#schema .ini{font-size:13px;font-weight:600;fill:var(--paper)}
#schema .rel{transition:opacity .15s}#schema.focus .rel:not(.on){opacity:.14}#schema.focus .node:not(.on){opacity:.35}
.legend{display:flex;flex-wrap:wrap;gap:6px 18px;font-size:13px;color:var(--graphite);margin:4px 0 14px}
.legend span{display:inline-flex;align-items:center;gap:7px}.fact p svg{vertical-align:-2px}
#detail{border-top:1px solid var(--mist);padding:16px 0 0;min-height:92px}
.fact{padding:0 0 14px;font-size:15.5px;max-width:46em}
.fact .who{display:flex;align-items:center;gap:7px;flex-wrap:wrap;font-weight:600}
.fact .who .k{font-weight:400;color:var(--graphite)}
.fact p{margin:3px 0 0}.fact .m{font-size:13.5px;color:var(--graphite)}
.all{margin:26px 0 0;border-top:1px solid var(--mist);padding:16px 0 0}
.all summary{cursor:pointer;font:500 19px/1.3 var(--serif)}
.all h3{margin:22px 0 10px}
.none{font-size:15px;color:var(--graphite);margin:18px 0 0;max-width:46em}
"""

def data(d):
    live = lambda xs: [x for x in xs if x.get("status") != "ended"]
    people = {k: v.get("thumb") for k, v in (d.get("people") or {}).items() if k in d["actors"] and v.get("thumb")}
    return {"actors": {k: {"name": a["name"], "kind": a["kind"]} for k, a in d["actors"].items()},
            "edges": live(d["edges"]), "tensions": live(d["tensions"]), "mediations": live(d["mediations"]),
            "dependencies": live(d["dependencies"]), "colors": d["colors"], "people": people,
            "dossiers": [{"id": x["id"], "title": x["title"], "sides": [s["actors"] for s in x["sides"]]}
                         for x in dossier.load()]}

SCRIPT = r"""<script>
const D = __DATA__;
const $ = s => document.querySelector(s);
const esc = v => String(v ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const nm = id => esc((D.actors[id] || {}).name || id);
const isFlag = id => ["state", "bloc"].includes((D.actors[id] || {}).kind);
const flag = id => `https://cdn.jsdelivr.net/npm/flag-icons@7.2.3/flags/1x1/${id.toLowerCase()}.svg`;
const pic = id => isFlag(id) ? flag(id) : D.people[id] || null;
const img = id => pic(id) ? `<img src="${esc(pic(id))}" alt="">` : "";
const who = id => `${img(id)}<span>${nm(id)}</span>`;
const DOS = Object.fromEntries(D.dossiers.map(x => ["d:" + x.id, x]));
const label = t => DOS[t] ? esc(DOS[t].title) : nm(t);
// source → lien court vers le site (texte complet au survol) ; sans URL, le texte tel quel
const src = s => { const m = String(s).match(/https?:\/\/[^\s<]+/); if(!m) return esc(s);
  let host = m[0]; try { host = new URL(m[0]).hostname.replace(/^www\./, ""); } catch(_) {}
  return `<a href="${esc(m[0])}" target="_blank" rel="noopener" title="${esc(String(s).slice(0, m.index).replace(/[\s—]+$/, ""))}">${esc(host)}</a>`; };
const TYPES_FR = {arms:"armes", troops:"troupes", financial:"argent", training:"entraînement", intelligence:"renseignement",
  political:"politique", economic:"économique", dual_use:"double usage"};
const TENSION = {war:{label:"Guerre", color:"#b91c1c", width:4, dash:null, arrow:false},
  sanctions:{label:"Sanctions", color:"#7c3aed", width:2, dash:"8 5", arrow:true},
  claims:{label:"Revendication", color:"#d97706", width:2, dash:"3 4", arrow:true},
  rivalry:{label:"Rivalité", color:"#64748b", width:2, dash:"10 6", arrow:false}};
const STATUS_FR = {active:"actif", reduced:"en baisse", alleged:"allégué"};
const CONF_FR = {high:"documenté officiellement", medium:"sources concordantes", low:"allégations"};
const WIDTH = {high: 3.2, medium: 2.2, low: 1.3}, DEP = "#b08968";
const DEP_FR = {arms: "d'armes", gas: "de gaz", oil: "de pétrole"};
const depWhat = x => x.resource ? (/^[aeiouyéèh]/i.test(x.resource) ? "d'" : "de ") + x.resource : DEP_FR[x.type] || x.type;
const pct = x => String(x.share).replace(".", ",") + " %";
const depText = x => `${pct(x)} ${x.type === "debt" ? "de sa dette publique extérieure"
  : x.type === "trade" ? (x.direction === "exports" ? "de ses exportations" : "de ses importations de marchandises")
  : "de ses importations " + depWhat(x)} (${esc(x.period || x.year)})`;
// pictogrammes des dépendances (Lucide, ISC) : la ressource se lit d'un coup d'œil, le chiffre reste à côté
const DEP_ICON = __DEP_ICONS__;
const DEP_NAME = {oil: "pétrole", gas: "gaz", arms: "armes", minerals: "minerais", food: "denrées", debt: "dette", trade: "commerce"};
const depIcon = (t, size = 14) => `<svg viewBox="0 0 24 24" width="${size}" height="${size}" fill="none" stroke="${DEP}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${DEP_ICON[t] || ""}</svg>`;
const depShort = x => `${x.type === "debt" ? "dette" : x.type === "trade" ? (x.direction === "exports" ? "exportations" : "importations")
  : x.resource || {arms:"armes", gas:"gaz", oil:"pétrole"}[x.type] || x.type} ${pct(x)}`;
const MONTHS = ["janvier","février","mars","avril","mai","juin","juillet","août","septembre","octobre","novembre","décembre"];
const when = d => { const [y, m] = String(d).split("-"); return m && MONTHS[+m - 1] ? `${MONTHS[+m - 1]} ${y}` : y; };
const since = x => x.since ? `Depuis ${esc(when(x.since))}. ` : "";
const tail = x => `<p class="m">${x.note ? esc(x.note) + ". " : ""}Sources : ${(x.sources || []).map(src).join(", ")}</p>`;
const ARROW = '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-label="vers"><path d="M5 12h14M13 6l6 6-6 6"/></svg>';

// ---------- Sélection : jetons « US » (acteur) ou « d:ukraine » (conflit), gardés dans l'URL ----------
let SEL = (new URLSearchParams(location.search).get("e") || "").split(",").filter(t => D.actors[t] || DOS[t]);
let PICK = null;   // trait ou acteur mis en avant
function scope(){ const ids = [];
  SEL.forEach(t => (DOS[t] ? DOS[t].sides.flat() : [t]).forEach(id => { if(D.actors[id] && !ids.includes(id)) ids.push(id); }));
  return ids; }

// ---------- Faits entre les acteurs du périmètre : un fait = un trait (deux pour une médiation) ----------
function facts(ids){ const S = new Set(ids), F = [], extra = [];   // extra : réservé aux acteurs ajoutés hors sélection (aucun pour l'instant)
  D.tensions.forEach(t => { if(!S.has(t.from) || !S.has(t.to)) return; const s = TENSION[t.type];
    F.push({group: "tension", links: [[t.from, t.to]], color: s.color, width: s.width, dash: s.dash, arrow: s.arrow, nodes: [t.from, t.to],
      html: `<div class="who">${who(t.from)}${s.arrow ? ARROW : '<span class="k">et</span>'}${who(t.to)}</div>
        <p>${s.label}. ${since(t)}${t.status === "reduced" ? "Trêve ou cessez-le-feu en cours." : ""}</p>${tail(t)}`}); });
  D.edges.forEach(x => { if(!S.has(x.from) || !S.has(x.to)) return;
    F.push({group: "support", links: [[x.from, x.to]], color: D.colors[x.types[0]] || "#888", width: WIDTH[x.confidence] || 2,
      dash: x.status === "active" ? null : "9 5", arrow: true, nodes: [x.from, x.to],
      html: `<div class="who">${who(x.from)}${ARROW}${who(x.to)}</div>
        <p>Soutien : ${x.types.map(t => esc(TYPES_FR[t] || t)).join(", ")}. ${since(x)}Statut : ${esc(STATUS_FR[x.status] || x.status)} ; ${esc(CONF_FR[x.confidence] || x.confidence)}.</p>
        ${x.why ? `<p>Pourquoi : ${esc(x.why)}</p>` : ""}${tail(x)}`}); });
  D.mediations.forEach(m => { if(!m.between.every(b => S.has(b))) return;
    const out = !S.has(m.mediator);   // médiateur hors sélection : pas de nœud en plus, le fait reste listé et signalé sous le schéma
    F.push({group: "mediation", out, links: out ? [] : m.between.map(b => [m.mediator, b]), color: "var(--graphite)", width: 1.6, dash: "3 5", arrow: false,
      nodes: out ? m.between : [m.mediator, ...m.between], mediator: m.mediator,
      html: `<div class="who">${who(m.mediator)}<span class="k">médiation entre</span>${who(m.between[0])}<span class="k">et</span>${who(m.between[1])}</div>
        <p>${since(m)}${m.why ? "Pourquoi : " + esc(m.why) : ""}</p>${tail(m)}`}); });
  D.dependencies.forEach(x => { if(!S.has(x.from) || !S.has(x.supplier)) return;
    F.push({group: "lever", links: [[x.supplier, x.from]], color: DEP, width: 1 + x.share / 14, dash: "1.5 6", round: true, arrow: true,
      nodes: [x.from, x.supplier], value: pct(x), dep: x.type, tip: `${(D.actors[x.from] || {}).name} dépend de ${(D.actors[x.supplier] || {}).name} : ${depShort(x)}`,
      html: `<div class="who">${who(x.from)}<span class="k">dépend de</span>${who(x.supplier)}</div>
        <p>${depIcon(x.type, 15)} ${depText(x)}.</p>${tail(x)}`}); });
  F.forEach((f, i) => f.id = i);
  return {F, extra}; }

// ---------- Schéma : acteurs sur une ellipse, fixes ; plusieurs faits entre deux acteurs = traits écartés ----------
// écran étroit : cadre plus étroit et plus haut, pour que les noms restent lisibles
const NARROW = innerWidth < 600, W = NARROW ? 400 : 760, H = 470, CX = W / 2, CY = H / 2 - 4, R = 27;
function draw(ids, extra, F){ const all = [...ids, ...extra], n = all.length, P = {};
  const rx = NARROW ? 125 : n === 2 ? 230 : 285, ry = n === 2 ? 0 : NARROW ? 180 : 165, a0 = n % 2 === 0 ? -90 - 180 / n : -90;
  all.forEach((id, i) => { const a = (a0 + 360 * i / n) * Math.PI / 180; P[id] = [CX + rx * Math.cos(a), CY + ry * Math.sin(a)]; });
  const byPair = {}; F.forEach(f => f.links.forEach(l => { const k = [...l].sort().join("|"); (byPair[k] = byPair[k] || []).push([f, l]); }));
  const cols = [...new Set(F.filter(f => f.arrow).map(f => f.color))];
  let s = `<defs>${cols.map((c, i) => `<marker id="mk${i}" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="7" markerHeight="7" markerUnits="userSpaceOnUse" orient="auto"><path d="M0 0L10 5L0 10z" fill="${c}"/></marker>`).join("")}
    <clipPath id="cp"><circle r="${R - 3}"/></clipPath></defs>`;
  Object.entries(byPair).forEach(([k, list]) => { const [u, v] = k.split("|"), [x1, y1] = P[u], [x2, y2] = P[v];
    const dx = x2 - x1, dy = y2 - y1, len = Math.hypot(dx, dy), nx = -dy / len, ny = dx / len;
    list.forEach(([f, l], i) => { const off = (i - (list.length - 1) / 2) * 38;
      const mx = (x1 + x2) / 2 + nx * off * 2, my = (y1 + y2) / 2 + ny * off * 2;      // point de contrôle
      const end = (px, py) => { const ex = mx - px, ey = my - py, d = Math.hypot(ex, ey) || 1; return [px + ex / d * (R + 5), py + ey / d * (R + 5)]; };
      const [fa, fb] = l[0] === u ? [end(x1, y1), end(x2, y2)] : [end(x2, y2), end(x1, y1)];
      const path = `M${fa[0].toFixed(1)} ${fa[1].toFixed(1)}Q${mx.toFixed(1)} ${my.toFixed(1)} ${fb[0].toFixed(1)} ${fb[1].toFixed(1)}`;
      s += `<g class="rel" data-f="${f.id}"><path d="${path}" fill="none" stroke="${f.color}" stroke-width="${f.width.toFixed(1)}"${f.dash ? ` stroke-dasharray="${f.dash}"` : ""}${f.round ? ' stroke-linecap="round"' : ""}${f.arrow ? ` marker-end="url(#mk${cols.indexOf(f.color)})"` : ""}/>
        ${f.value ? (() => { const w = f.value.length * 6.4 + 30, lx = (x1 + x2) / 2 + nx * off, ly = (y1 + y2) / 2 + ny * off;
          return `<g transform="translate(${(lx - w / 2).toFixed(1)} ${(ly - 10).toFixed(1)})"><title>${esc(f.tip)}</title><rect class="pill" width="${w.toFixed(1)}" height="20" rx="10"/>
            <svg x="7" y="3" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="${DEP}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">${DEP_ICON[f.dep] || ""}</svg>
            <text class="val" x="25" y="14.2">${esc(f.value)}</text></g>`; })() : ""}
        <path class="hit" d="${path}"/></g>`; }); });
  all.forEach(id => { const [x, y] = P[id], up = y < CY - 1, name = (D.actors[id] || {}).name || id;
    s += `<g class="node${extra.includes(id) ? " extra" : ""}" data-n="${esc(id)}" transform="translate(${x.toFixed(1)} ${y.toFixed(1)})" tabindex="0" role="button" aria-label="${esc(name)}">
      <circle class="ring" r="${R}"/>${pic(id) ? `<image href="${esc(pic(id))}" x="${-R + 3}" y="${-R + 3}" width="${2 * R - 6}" height="${2 * R - 6}" clip-path="url(#cp)" preserveAspectRatio="xMidYMid slice"/>`
        : `<circle r="${R - 3}" fill="var(--graphite)"/><text class="ini" text-anchor="middle" y="4.5">${esc(name.slice(0, 2).toUpperCase())}</text>`}
      <text class="lab" text-anchor="middle" y="${up ? -R - 9 : R + 20}">${esc(name)}${extra.includes(id) ? " (hors sélection)" : ""}</text></g>`; });
  const svg = $("#schema"); svg.setAttribute("viewBox", `0 ${n === 2 ? 130 : -14} ${W} ${n === 2 ? 200 : H + 6}`); svg.innerHTML = s; }

// ---------- Suggestions : les entités qui apportent le plus de faits RELIÉS à la sélection (comptés, jamais choisis à la main) ----------
function suggest(ids){ const old = new Set(ids), out = [];
  [...Object.keys(DOS), ...Object.keys(D.actors)].forEach(t => { if(SEL.includes(t)) return;
    const add = (DOS[t] ? DOS[t].sides.flat() : [t]).filter(id => D.actors[id] && !old.has(id)); if(!add.length) return;
    const fresh = new Set(add), n = facts([...ids, ...add]).F.filter(f => f.nodes.some(x => fresh.has(x)) && f.nodes.some(x => old.has(x))).length;
    if(n) out.push({t, n, dos: !!DOS[t]}); });
  const dos = out.filter(x => x.dos).sort((a, b) => b.n - a.n), covered = new Set(dos.flatMap(x => DOS[x.t].sides.flat()));
  // un acteur déjà apporté par un conflit suggéré n'est pas proposé en double
  return [...dos, ...out.filter(x => !x.dos && !covered.has(x.t)).sort((a, b) => b.n - a.n).slice(0, 3)].slice(0, 5); }

const stroke = (c, o = {}) => `<svg width="30" height="8" aria-hidden="true"><path d="M1 4H29" stroke="${c}" stroke-width="${o.w || 2.5}"${o.dash ? ` stroke-dasharray="${o.dash}"` : ""} stroke-linecap="${o.round ? "round" : "butt"}"/></svg>`;
const GROUPS = [["tension", "Qui s'affronte"], ["support", "Qui soutient qui, et pourquoi"], ["mediation", "Qui négocie"], ["lever", "Qui dépend de qui"]];
const card = f => `<div class="fact">${f.html}</div>`;

function render(){ const ids = scope(), ok = SEL.length >= 2 && ids.length >= 2;
  $("#chips").innerHTML = SEL.map((t, i) => `<span class="chip">${DOS[t] ? "" : img(t)}${label(t)}<button type="button" data-rm="${i}" aria-label="Retirer ${label(t)}">×</button></span>`).join("");
  panel();
  const dos = SEL.filter(t => DOS[t]);
  $("#scope").innerHTML = (dos.length ? dos.map(t => `${label(t)} apporte ses camps : ${DOS[t].sides.flat().map(nm).join(", ")}. `).join("") : "")
    + (ok ? '<button type="button" id="copy">Copier le lien</button>' : "");
  const sug = ids.length ? suggest(ids) : [];
  $("#sug").innerHTML = sug.length ? "À croiser aussi : " + sug.map(x => `<button type="button" data-add="${esc(x.t)}">${DOS[x.t] ? "" : img(x.t)}${label(x.t)} <small>${x.n} lien${x.n > 1 ? "s" : ""}</small></button>`).join("") : "";
  $("#empty").hidden = ok; $("#out").hidden = !ok;
  history.replaceState(null, "", location.pathname + (SEL.length ? "?e=" + SEL.join(",") : ""));
  if(!ok) return;
  const {F, extra} = facts(ids); draw(ids, extra, F);
  const outs = F.filter(f => f.out);
  $("#aside").innerHTML = outs.length ? "Hors sélection : " + outs.map(f => `<button type="button" data-fact="${f.id}">${nm(f.mediator)}, médiateur entre ${nm(f.nodes[0])} et ${nm(f.nodes[1])}</button>`).join(" ; ") + "." : "";
  const has = g => F.some(f => f.group === g && !f.out), sup = [...new Set(F.filter(f => f.group === "support").map(f => f.color))];
  $("#legend").innerHTML = [has("tension") && [...new Set(F.filter(f => f.group === "tension").map(f => f.color))].map(c => { const t = Object.values(TENSION).find(x => x.color === c);
      return `<span>${stroke(c, {w: Math.min(t.width, 3), dash: t.dash})}${t.label.toLowerCase()}</span>`; }).join(""),
    has("support") && `<span>${sup.map(c => stroke(c)).join("")}__SOUTIEN__ (tirets : en baisse ou allégué)</span>`,
    has("mediation") && `<span>${stroke("var(--graphite)", {w: 1.6, dash: "3 5"})}__MEDIATION__</span>`,
    has("lever") && `<span>${stroke(DEP, {w: 3, dash: "1.5 6", round: true})}__LEVIER__ (épaisseur : part mesurée)</span>`
      + [...new Set(F.filter(f => f.dep).map(f => f.dep))].map(t => `<span>${depIcon(t)}${DEP_NAME[t] || t}</span>`).join("")].filter(Boolean).join("");
  const pairs = []; ids.forEach((a, i) => ids.slice(i + 1).forEach(b => { if(!F.some(f => f.nodes.includes(a) && f.nodes.includes(b))) pairs.push(`${nm(a)} et ${nm(b)}`); }));
  $("#none").innerHTML = pairs.length ? `Ce que le graphe ne contient pas : aucune relation documentée entre ${pairs.join(" ; ")}. Cela ne prouve pas qu'il n'y en a pas, seulement qu'aucune n'est sourcée ici.` : "";
  $("#all").innerHTML = `<summary>Tous les faits (${F.length}) et leurs sources</summary>` + (F.length ? GROUPS.filter(([g]) => F.some(f => f.group === g)).map(([g, t]) =>
    `<h3>${t}</h3>` + F.filter(f => f.group === g).map(card).join("")).join("") : '<p class="none">Aucun fait entre ces acteurs dans le graphe.</p>');
  window.FACTS = F; if(PICK && !(PICK.f != null ? F[PICK.f] : ids.concat(extra).includes(PICK.n))) PICK = null;
  detail(); }

function detail(){ const F = window.FACTS, svg = $("#schema"), box = $("#detail");
  const on = PICK ? F.filter(f => PICK.f != null ? f.id === PICK.f : f.nodes.includes(PICK.n)) : [];
  svg.classList.toggle("focus", !!PICK);
  svg.querySelectorAll(".rel").forEach(g => g.classList.toggle("on", on.some(f => f.id === +g.dataset.f)));
  const near = new Set(on.flatMap(f => f.nodes)); if(PICK && PICK.n) near.add(PICK.n);
  svg.querySelectorAll(".node").forEach(g => g.classList.toggle("on", near.has(g.dataset.n)));
  if(!PICK){ box.innerHTML = `<p class="none" style="margin:0">${F.length ? "Cliquez un trait ou un acteur pour lire le fait, sa date et ses sources." : "Aucun fait entre ces acteurs dans le graphe."}</p>`; return; }
  box.innerHTML = (on.length ? on.map(card).join("") : `<p class="none" style="margin:0 0 12px">Aucun fait entre ${nm(PICK.n)} et les autres acteurs choisis.</p>`)
    + (PICK.n ? `<p class="fact m"><a href="explorer.html#graphe:${esc(PICK.n)}">Voir toutes les relations de ${nm(PICK.n)} dans Carte &amp; graphe</a></p>` : ""); }

// ---------- Panneau de choix : catégories visibles d'un coup, champ qui filtre (sans accents ni casse) ----------
const flat = v => String(v).normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
const byName = ks => ks.sort((a, b) => D.actors[a].name.localeCompare(D.actors[b].name, "fr"));
const kindIs = (...k) => byName(Object.keys(D.actors).filter(id => k.includes(D.actors[id].kind)));
const CATS = [["Conflits", Object.keys(DOS)], ["Pays et blocs", kindIs("state", "bloc")], ["Groupes armés", kindIs("non_state")], ["Partis et personnalités", kindIs("party", "person")]];
function panel(){ const q = flat($("#q").value.trim()); let shown = 0;
  $("#groups").innerHTML = CATS.map(([t, items]) => { const hit = items.filter(k => !q || flat(DOS[k] ? DOS[k].title : D.actors[k].name).includes(q)); shown += hit.length;
    return hit.length ? `<h3>${t}</h3><div class="g">${hit.map(k => `<button type="button" data-add="${esc(k)}"${SEL.includes(k) ? " disabled" : ""}>${DOS[k] ? "" : img(k)}${label(k)}</button>`).join("")}</div>` : ""; }).join("");
  $("#noq").hidden = shown > 0; }
function toggle(open){ $("#panel").hidden = !open; $("#veil").hidden = !open; $("#addbtn").setAttribute("aria-expanded", open); if(open){ $("#q").value = ""; panel(); $("#q").focus(); } }
$("#addbtn").addEventListener("click", () => toggle($("#panel").hidden));
$("#q").addEventListener("input", panel);
$("#q").addEventListener("keydown", ev => { if(ev.key === "Escape"){ toggle(false); $("#addbtn").focus(); }
  if(ev.key === "Enter"){ const b = $("#groups button:not(:disabled)"); if(b && $("#q").value.trim()){ b.click(); $("#q").value = ""; panel(); } } });
document.addEventListener("click", ev => { const t = ev.target;
  if(t.dataset && t.dataset.rm != null){ SEL.splice(+t.dataset.rm, 1); PICK = null; return render(); }
  const add = t.closest && t.closest("[data-add]"); if(add){ if(!SEL.includes(add.dataset.add)) SEL.push(add.dataset.add); PICK = null; return render(); }
  if(!$("#panel").hidden && !(t.closest && (t.closest("#panel") || t.closest("#addbtn") || t.closest(".pick") || t.closest("#sug")))) toggle(false);
  if(t.id === "copy"){ navigator.clipboard && navigator.clipboard.writeText(location.href).then(() => t.textContent = "Lien copié"); return; }
  const ex = t.closest && t.closest("[data-ex]"); if(ex){ ev.preventDefault(); SEL = ex.dataset.ex.split(","); PICK = null; return render(); }
  if(t.dataset && t.dataset.fact != null){ PICK = {f: +t.dataset.fact}; return detail(); }
  const rel = t.closest && t.closest(".rel"), node = t.closest && t.closest(".node");
  if(rel){ PICK = PICK && PICK.f === +rel.dataset.f ? null : {f: +rel.dataset.f}; return detail(); }
  if(node){ PICK = PICK && PICK.n === node.dataset.n ? null : {n: node.dataset.n}; return detail(); }
  if(t.closest && t.closest("#schema") && PICK){ PICK = null; detail(); } });
document.addEventListener("keydown", ev => { const node = ev.target.closest && ev.target.closest(".node");
  if(node && (ev.key === "Enter" || ev.key === " ")){ ev.preventDefault(); node.dispatchEvent(new MouseEvent("click", {bubbles: true})); } });
render();
</script>"""

EXAMPLES = [("US,d:ukraine,CN", "Les États-Unis, la Chine et la guerre en Ukraine"),
            ("d:iran,RU,CN", "La Russie, la Chine et la guerre avec l'Iran"),
            ("EU,RU,US", "L'Union européenne, la Russie et les États-Unis")]

def page(d):
    x = data(d)
    valid = set(x["actors"]) | {"d:" + t["id"] for t in x["dossiers"]}
    examples = "".join(f'<a href="croiser.html?e={e(q)}" data-ex="{e(q)}">{e(t)}</a>' for q, t in EXAMPLES
                       if all(tok in valid for tok in q.split(",")))
    script = (SCRIPT.replace("__DATA__", json.dumps(x, ensure_ascii=False, default=str).replace("</", "<\\/"))
              .replace("__DEP_ICONS__", json.dumps(style.DEP_ICONS))
              .replace("__SOUTIEN__", glossary.term("soutien", "soutien")).replace("__MEDIATION__", glossary.term("mediation", "médiation"))
              .replace("__LEVIER__", glossary.term("levier", "dépendance")))
    body = f"""<main class="cross">
<h1>Croiser des acteurs</h1>
<p class="lede">Choisissez au moins deux pays, groupes ou conflits : le schéma montre ce qui les relie, fait par fait.</p>
<div class="picker"><div id="veil" hidden></div><div class="pick"><span id="chips" style="display:contents"></span>
<button type="button" id="addbtn" aria-expanded="false" aria-controls="panel">Ajouter</button></div>
<div id="panel" hidden><input type="search" id="q" placeholder="Filtrer : un pays, un groupe, un conflit" aria-label="Filtrer la liste" autocomplete="off">
<div id="groups"></div><p class="none" id="noq" hidden>Aucun acteur ne correspond.</p></div></div>
<p class="scope" id="scope"></p>
<p class="sug" id="sug"></p>
<div id="empty"><div class="ex"><span class="quiet">Pour commencer :</span>{examples}</div></div>
<div id="out" hidden>
<svg id="schema" role="group" aria-label="Schéma des relations entre les acteurs choisis"></svg>
<div class="legend" id="legend"></div>
<p class="scope" id="aside"></p>
<div id="detail" aria-live="polite"></div>
<p class="none" id="none"></p>
<details class="all" id="all"></details>
</div>
</main>"""
    title = f"Croiser des acteurs — {brand.NAME}"
    return (style.head(title, "Choisissez des pays, des groupes ou un conflit : ce qui les relie, fait par fait, avec les sources.",
                       f"<style>{CSS}</style>")
            + f'<body><div class="wrap">{style.top("croiser.html")}\n{body}</div>{style.foot(page="Croiser des acteurs")}{script}</body></html>')

def write(out, d):
    (out / "croiser.html").write_text(page(d), encoding="utf-8")
