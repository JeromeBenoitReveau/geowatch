"""Pages éditoriales : accueil (site/index.html) et manifeste (site/manifeste.html).
Chiffres et liste des conflits calculés à partir des mêmes données que le reste du site ; mise en forme commune
dans style.py (style.css)."""
from html import escape as e
import json
import brand, dossier, style

CSS = """
.hero{padding:72px 0 40px;max-width:780px}.hero h1{font-size:48px;line-height:1.08}
.hero p{font-size:19px;color:var(--graphite);margin:0;max-width:34em}
.conflicts{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}
.conflict{display:flex;flex-direction:column;padding:0;overflow:hidden}
.conflict .wm{display:block;width:100%;aspect-ratio:2/1;background:var(--ocean);border-bottom:1px solid var(--mist)}
.conflict .wm path{stroke:var(--mist);stroke-width:.5}
.conflict .body{padding:20px 22px 22px;display:flex;flex-direction:column;flex:1}
.conflict h3{font-size:25px;margin:0 0 6px}
.conflict .vs{margin:0 0 10px;font-size:15px}.conflict .vs span{display:inline-block;width:9px;height:9px;border-radius:50%;margin:0 6px 0 0}
.conflict p{margin:0;max-width:40em}.conflict .go{margin-top:14px;font-size:15px;text-decoration:underline;text-decoration-color:var(--peach);text-decoration-thickness:1.5px;text-underline-offset:3px;width:max-content}
.odds{padding:12px 14px;margin-top:16px;display:flex;align-items:center;gap:12px}
.odds b{font:400 34px/1 var(--serif);font-variant-numeric:tabular-nums}
.odds span{font-size:14px;line-height:1.35}.odds small{display:block;font-size:13px;color:var(--graphite)}
.conflict .key{font-size:12.5px;color:var(--graphite);margin:8px 0 0}.conflict .go{margin-top:auto;padding-top:14px}
.explore{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}
.explore .card{padding:22px}.explore .ico{display:block;margin-bottom:12px}
.explore p.use{margin:0 0 14px;font-size:16px;color:var(--ink)}.explore .count{font-size:13px;color:var(--graphite)}
.cta{display:flex;align-items:center;gap:18px;flex-wrap:wrap;margin-top:26px}
.btn{display:inline-block;background:var(--ink);color:var(--paper);padding:11px 18px;border-radius:6px;text-decoration:none;font-weight:500}
.btn:hover{background:color-mix(in srgb,var(--ink) 85%,var(--peach))}.cta .alt{color:var(--graphite);font-size:15px}
.hero .updated{margin-top:18px;font-size:14px}
.page{padding:64px 0 0}.page h2{margin-top:40px}.page ol li,.page ul li{margin-bottom:10px}
@media (max-width:760px){.hero{padding:48px 0 28px}.hero h1{font-size:34px}.conflicts{grid-template-columns:1fr}
  .explore{grid-template-columns:1fr}}
"""

svg = lambda k: style.icon(k, 28)

WORLD_MAP = """<script src="https://cdn.jsdelivr.net/npm/d3-array@3/dist/d3-array.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/d3-geo@3/dist/d3-geo.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/topojson-client@3/dist/topojson-client.min.js"></script>
<script>
// Petites cartes des conflits : camps en couleur pleine, soutiens étrangers en teinte claire, rayures si un pays
// est dans les deux (guerre civile) ; un point marque le lieu du conflit. Fond Natural Earth (domaine public).
fetch("https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json").then(r => r.json()).then(world => {
  const land = topojson.feature(world, world.objects.countries).features.filter(f => f.id !== "010");  // sans l'Antarctique
  const proj = d3.geoNaturalEarth1().fitExtent([[6, 6], [594, 294]], {type: "FeatureCollection", features: land});
  const path = d3.geoPath(proj), light = c => `color-mix(in srgb,var(${c}) 55%,var(--land))`;
  document.querySelectorAll("svg.wm").forEach((svg, n) => { const m = JSON.parse(svg.dataset.map), has = (k, id) => m[k].includes(String(+id));
    const defs = `<defs><pattern id="ab${n}" patternUnits="userSpaceOnUse" width="6" height="6" patternTransform="rotate(45)">
      <rect width="3" height="6" style="fill:var(--a)"/><rect x="3" width="3" height="6" style="fill:var(--b)"/></pattern>
      <pattern id="lab${n}" patternUnits="userSpaceOnUse" width="6" height="6" patternTransform="rotate(45)">
      <rect width="3" height="6" style="fill:${light("--a")}"/><rect x="3" width="3" height="6" style="fill:${light("--b")}"/></pattern></defs>`;
    const fill = id => has("a", id) && has("b", id) ? `url(#ab${n})` : has("a", id) ? "var(--a)" : has("b", id) ? "var(--b)"
      : has("ba", id) && has("bb", id) ? `url(#lab${n})` : has("ba", id) ? light("--a") : has("bb", id) ? light("--b") : "var(--land)";
    const pin = m.pin[0] != null ? proj(m.pin) : null;
    svg.innerHTML = defs + land.map(f => `<path d="${path(f)}" style="fill:${fill(f.id)}"/>`).join("")
      + (pin ? `<circle cx="${pin[0].toFixed(1)}" cy="${pin[1].toFixed(1)}" r="9" fill="none" style="stroke:var(--ink)" stroke-width="1.6"/>` : ""); });
});
</script>"""

def page(title, body, current, desc=brand.BASELINE, extra=""):
    return style.head(title, desc, f"<style>{CSS}</style>") + f"""<body><div class="wrap">{style.top(current)}
{body}</div>{style.foot(page=title.split(" — ")[0])}{extra}</body></html>"""

def countries(ids, d):
    """Pays d'un ensemble d'acteurs : l'État lui-même, le pays d'ancrage d'un groupe ou d'une personne,
    les membres d'un bloc (groupe d'alignments.yaml rattaché au bloc, le plus haut niveau)."""
    out = set()
    for i in ids:
        a = d["actors"].get(i, {})
        if a.get("kind") == "state":
            out.add(i)
        elif a.get("kind") == "bloc":
            gs = [g for g in d["align"]["groups"] if g.get("entity") == i]
            if gs:
                out |= set(max(gs, key=lambda g: g.get("level") or 0)["members"])
        elif a.get("base"):
            out.add(a["base"])
    return out

def conflict_map(x, d):
    """Données de la petite carte du monde : codes numériques ISO (ceux de Natural Earth) par rôle, et le lieu du conflit."""
    sides = [set(sd["actors"]) for sd in x["sides"]]
    backers = [{ed["from"] for ed in d["edges"] if ed["to"] in sd and ed["from"] not in sd and ed["status"] != "ended"} for sd in sides]
    num = lambda isos: sorted(str(int(d["geo"][i]["iso_numeric"])) for i in isos if d["geo"].get(i, {}).get("iso_numeric"))
    a, b = countries(sides[0], d), countries(sides[1], d)
    ba, bb = countries(backers[0], d) - a - b, countries(backers[1], d) - a - b
    where = d["geo"].get(sorted(a)[0] if a else "", {})
    return {"a": num(a), "b": num(b), "ba": num(ba), "bb": num(bb), "pin": [where.get("lon"), where.get("lat")]}

def conflict_row(x, d):
    names = [s["name"] for s in x["sides"]]
    # encart : les soutiens étrangers de chaque camp, lus dans le graphe (pas de cote ni de probabilité)
    ids = [set(sd["actors"]) for sd in x["sides"]]
    per_side = [len({ed["from"] for ed in d["edges"] if ed["to"] in i and ed["from"] not in i and ed["status"] != "ended"}) for i in ids]
    short = lambda n: n[:1].lower() + n[1:]
    odds = (f'<div class="odds tint"><b>{sum(per_side)}</b><span>puissances étrangères impliquées'
            f'<small>{per_side[0]} {"soutient" if per_side[0] == 1 else "soutiennent"} {e(short(names[0]))}, {per_side[1]} {e(short(names[1]))}</small></span></div>')
    first = " ".join(x["lede"].split()).split(". ")[0].rstrip(".") + "."
    return f"""<a class="card conflict" href="{e(x['id'])}.html">
<svg class="wm" viewBox="0 0 600 300" role="img" aria-label="Carte : pays des deux camps et de leurs soutiens étrangers" data-map='{e(json.dumps(conflict_map(x, d)))}'></svg>
<div class="body"><h3>{e(x['title'])}</h3>
<p class="vs"><span style="background:var(--a)"></span>{e(names[0])} contre <span style="background:var(--b);margin-left:4px"></span>{e(names[1][:1].lower() + names[1][1:])}</p>
<p>{e(first)}</p><p class="key">Sur la carte, en teinte claire : leurs soutiens étrangers.</p>{odds}<p class="go">Lire le dossier</p></div></a>"""

def home(d, dossiers):
    groups = d["align"]["groups"]
    first = dossiers[0]
    built = "/".join(reversed(d["built"][:10].split("-")))
    body = f"""<section class="hero"><h1>{e(brand.BASELINE)}</h1>
<p>Guerres, alliances, sanctions, rivalités : qui s'oppose à qui, qui soutient qui, et pour quelles raisons.
Les rapports de force du monde rendus lisibles, sans prérequis. Chaque affirmation est sourcée.</p>
<div class="cta"><a class="btn" href="{e(first['id'])}.html">Commencer par une guerre : {e(first['title'][:1].lower() + first['title'][1:])}</a>
<a class="alt" href="explorer.html">ou explorer la carte et le graphe</a></div>
<p class="meta updated">Mis à jour le {built}</p></section>

<section id="conflits"><h2>Comprendre les conflits en cours</h2>
<div class="conflicts">{"".join(conflict_row(x, d) for x in dossiers)}</div>
</section>

<section class="s"><h2>Aller plus loin : explorer les données</h2>
<div class="explore">
<a class="card" href="explorer.html#organisations">{svg("orgs")}<h3>Les organisations</h3>
<p class="use">Voir qui appartient à quoi (OTAN, BRICS, Union européenne…), et quels pays sont à la croisée de plusieurs camps.</p>
<span class="count">{len(groups)} organisations et alliances</span></a>
<a class="card" href="explorer.html#carte">{svg("map")}<h3>La carte du monde</h3>
<p class="use">Voir de quel côté penche chaque pays, et depuis quand.</p>
<span class="count">{len(d["geo"])} pays</span></a>
<a class="card" href="explorer.html#graphe">{svg("graph")}<h3>Le graphe des soutiens</h3>
<p class="use">Suivre qui arme, qui finance et qui affronte qui.</p>
<span class="count">{len(d["actors"])} acteurs, {len(d["edges"])} relations</span></a>
</div></section>
<p class="quiet" style="margin-top:56px">Pourquoi vulgariser la géopolitique, et comment ce site est fait : <a href="manifeste.html">le manifeste</a>.
Les mots du site sont définis dans le <a href="glossaire.html">glossaire</a>.</p>"""
    return page(f"{brand.NAME} — {brand.BASELINE}", body, "", extra=WORLD_MAP)

def manifesto(d):
    body = f"""<article class="prose page">
<h1>Manifeste</h1>
<p class="meta">Pourquoi {e(brand.NAME)} existe, et comment il est fait.</p>

<h2>Le constat</h2>
<p>La géopolitique s'invite partout : dans le prix de l'énergie, dans les élections, dans les guerres dont on parle
chaque soir. Pourtant, elle reste réservée aux initiés. Les dépêches supposent qu'on connaît déjà les acteurs, les
alliances et l'histoire ; les analyses spécialisées, qu'on maîtrise leur vocabulaire. Entre les deux, beaucoup
décrochent. Et l'information répond surtout à « que se passe-t-il ? », rarement à la question qui permet vraiment de
comprendre : <b>qui est derrière qui, et pourquoi ?</b></p>
<p>La <a href="soudan.html">guerre au Soudan</a>, par exemple, oppose deux généraux, mais c'est aussi une rivalité entre
puissances régionales, une course à l'or et une bataille pour la mer Rouge. Sans ces relations, l'actualité reste
incompréhensible.</p>

<h2>Notre objectif</h2>
<p>Rendre la géopolitique accessible à tous, sans prérequis. Expliquer simplement les rapports de force du monde :
les conflits, mais aussi les alliances, les organisations, les sanctions et les rivalités qui les entourent. Vulgariser
sans simplifier à tort : chaque notion est définie, chaque affirmation est sourcée.</p>
<p>En quelques minutes, un dossier doit permettre de répondre à quatre questions : qui s'affronte ? qui les soutient ?
qu'y cherchent-ils ? qu'est-ce qui est en jeu ? Et l'explorateur permet d'élargir : à quel camp appartient tel pays, avec
qui il vote à l'ONU, de quelles organisations il est membre.</p>

<h2>Notre démarche</h2>
<ol>
<li><b>Tout est sourcé.</b> Chaque relation, chaque phrase d'un dossier renvoie à ses sources : organisations
internationales, centres de recherche, presse de référence. Aujourd'hui : {len(d["edges"])} relations, toutes sourcées.</li>
<li><b>Les faits d'un côté, l'analyse de l'autre.</b> « L'Égypte arme l'armée soudanaise » est un fait documenté.
« Pour protéger ses intérêts sur le Nil » est une analyse : elle est toujours attribuée à qui la formule. Quand les
analyses divergent, on le dit plutôt que de trancher.</li>
<li><b>Montrer le doute.</b> Un soutien démenti ou non prouvé est marqué « allégué », avec un niveau de confiance.
Une relation sans date connue le reste, plutôt que de lui en inventer une.</li>
<li><b>Aucune prédiction.</b> Le site explique ce qui se passe et pourquoi ; il ne dit pas ce qui va arriver.
Aucune probabilité, aucune cote de paris : les seuls chiffres sont des mesures sourcées.</li>
<li><b>Tous les camps, avec la même exigence.</b> On montre les soutiens de chaque côté, qu'ils viennent de
démocraties ou de dictatures, d'alliés ou de rivaux de la France.</li>
<li><b>Relu par un humain.</b> Des outils automatiques peuvent proposer des mises à jour, mais rien n'entre dans le
graphe sans relecture.</li>
<li><b>Ouvert.</b> Le code est libre (MIT), les données sont réutilisables (CC BY 4.0), et chacun peut proposer une
correction <a href="{style.correction_url()}">via un formulaire guidé</a>.</li>
</ol>

<h2>Ce que ce site n'est pas</h2>
<ul>
<li><b>Pas un site de spécialistes.</b> On écrit pour quelqu'un qui découvre le sujet : pas de jargon sans
explication, pas de sous-entendu.</li>
<li><b>Pas un fil d'actualité.</b> Les dossiers sont revus régulièrement, pas en temps réel. Pour suivre les événements
heure par heure, les médias et les tableaux de bord spécialisés restent indispensables.</li>
<li><b>Pas exhaustif.</b> Un conflit ou une relation n'est ajouté que lorsqu'il peut être sourcé sérieusement.</li>
<li><b>Pas un outil de pronostic.</b> On ne parie pas sur l'issue d'une guerre, et on n'affiche pas les paris des autres.</li>
</ul>

<h2>Comment c'est fait</h2>
<p>Un graphe de relations tenu à la main, des alliances formelles datées, les votes à l'Assemblée générale de l'ONU, des
données de la Banque mondiale et de Wikidata.
Le détail, source par source et règle par règle : <a href="methode.html">méthode et sources</a>.</p>
</article>"""
    return page(f"Manifeste — {brand.NAME}", body, "manifeste.html", "Pourquoi ce site existe, et comment il est fait.")

def write(out, data):
    dossiers = dossier.load()
    (out / "index.html").write_text(home(data, dossiers), encoding="utf-8")
    (out / "manifeste.html").write_text(manifesto(data), encoding="utf-8")
