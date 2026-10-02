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
/* dossiers : cartes horizontales compactes ; miniature cadrée sur la région, camps identifiés par leurs drapeaux */
.conflict{display:grid;grid-template-columns:150px minmax(0,1fr);padding:0;overflow:hidden;min-height:118px}
.conflict .wm{display:block;width:150px;height:100%;background:var(--ocean);border-right:1px solid var(--mist)}
.conflict .wm path{stroke:var(--mist);stroke-width:.6}
.conflict .body{padding:14px 16px;display:flex;flex-direction:column;gap:5px;min-width:0}
.conflict h3{font-size:19px;margin:0}
.conflict .vs{margin:0;font-size:13.5px;display:flex;align-items:center;flex-wrap:wrap;gap:4px 6px}
.conflict .vs img,.conflict .vs .ns{width:16px;height:16px;border-radius:50%;object-fit:cover;flex:none;box-shadow:0 0 0 1px var(--mist)}
.conflict .vs .ns{display:inline-flex;align-items:center;justify-content:center;background:var(--graphite);color:var(--paper)}
.conflict .vs .vs-x{color:var(--graphite)}
.conflict p.lede1{margin:0;font-size:14px;line-height:1.45;color:var(--graphite)}  /* jamais coupé : le résumé est écrit pour tenir */
.crossq{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}
.crossq .card{padding:16px 18px}.crossq h3{font-size:17px;margin:0}.crossq p{margin:4px 0 0;font-size:14px;color:var(--graphite)}
.crossq .marks{display:flex;align-items:center;gap:6px;margin:0 0 10px;min-height:20px}
.crossq .marks img,.crossq .marks .ns{width:20px;height:20px;border-radius:50%;object-fit:cover;flex:none;box-shadow:0 0 0 1px var(--mist)}
.crossq .marks .ns{display:inline-flex;align-items:center;justify-content:center;background:var(--graphite);color:var(--paper)}
.crossq .pick{border-style:dashed}
.explore{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}
/* vue d'ensemble : trois liens compacts sur une ligne (les blocs conflits et « Croiser » passent avant) */
.explore .card{padding:14px 16px;display:grid;grid-template-columns:auto 1fr;gap:0 12px;align-items:center}
.explore .card{align-items:start;align-content:start}.explore .ico{grid-row:1 / 3;width:22px;height:22px;margin-top:2px}.explore h3{font-size:17px;margin:0}
.explore p.use{grid-column:2;margin:4px 0 0;font-size:14px;line-height:1.45;color:var(--graphite)}
/* étiquette discrète (date de mise à jour) : filet fin, coins à peine arrondis */
.hero .updated{margin:22px 0 0}
.tag{display:inline-flex;align-items:center;gap:7px;padding:3px 9px;border:1px solid var(--mist);border-radius:3px;
  background:var(--land);font-size:12.5px;letter-spacing:.01em;color:var(--graphite);font-variant-numeric:tabular-nums}
.tag::before{content:"";width:6px;height:6px;border-radius:50%;background:var(--peach)}
.page{padding:64px 0 0}.page h2{margin-top:40px}.page ol li,.page ul li{margin-bottom:10px}
@media (max-width:760px){.hero{padding:48px 0 28px}.hero h1{font-size:34px}.conflicts{grid-template-columns:1fr}
  .explore,.crossq{grid-template-columns:1fr}}
"""

svg = lambda k: style.icon(k, 22)

WORLD_MAP = """<script src="https://cdn.jsdelivr.net/npm/d3-array@3/dist/d3-array.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/d3-geo@3/dist/d3-geo.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/topojson-client@3/dist/topojson-client.min.js"></script>
<script>
// Miniatures des dossiers, cadrées sur la région (cadre de la carte d'ouverture du dossier). Une seule couleur de
// conflit : pays en guerre en encre, soutiens étrangers en gris clair ; les camps se distinguent par leurs drapeaux,
// les couleurs de camp (bleu / orange) restent réservées aux pages des dossiers. Fond Natural Earth (domaine public).
fetch("https://cdn.jsdelivr.net/npm/world-atlas@2/countries-50m.json").then(r => r.json()).then(world => {
  const land = topojson.feature(world, world.objects.countries).features.filter(f => f.id !== "010");  // sans l'Antarctique
  const war = "color-mix(in srgb,var(--ink) 72%,var(--land))", ally = "color-mix(in srgb,var(--ink) 24%,var(--land))";
  document.querySelectorAll("svg.wm").forEach(svg => { const m = JSON.parse(svg.dataset.map), has = (k, id) => m[k].includes(String(+id));
    const [[s, w], [n, e]] = m.bounds, W = 150, H = 150;
    const proj = d3.geoMercator().fitExtent([[4, 4], [W - 4, H - 4]], {type: "MultiPoint", coordinates: [[w, s], [e, n]]}), path = d3.geoPath(proj);
    svg.setAttribute("viewBox", `0 0 ${W} ${H}`); svg.setAttribute("preserveAspectRatio", "xMidYMid slice");
    const fill = id => has("war", id) ? war : has("ally", id) ? ally : "var(--land)";
    svg.innerHTML = land.map(f => `<path d="${path(f)}" style="fill:${fill(f.id)}"/>`).join("")
      + m.dots.map(p => { const [x, y] = proj(p); return `<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="3" style="fill:var(--paper);stroke:var(--ink)" stroke-width="1.5"/>`; }).join(""); });
});
</script>"""

def page(title, body, current, desc=brand.BASELINE, extra="", ld=None):
    return style.head(title, desc, f"<style>{CSS}</style>", path=current or "index.html", ld=ld) + f"""<body><div class="wrap">{style.top(current)}
{body}</div>{style.foot(page=title.split(" — ")[0])}{extra}</body></html>"""

def conflict_map(x, d):
    """Données de la miniature : cadre (carte d'ouverture du dossier, sinon le monde), pays en guerre, pays des soutiens
    étrangers (codes numériques ISO de Natural Earth) et lieux repères (ancres de la carte du dossier)."""
    sides = [set(sd["actors"]) for sd in x["sides"]]
    backers = [{ed["from"] for ed in d["edges"] if ed["to"] in sd and ed["from"] not in sd and ed["status"] != "ended"} for sd in sides]
    num = lambda isos: sorted(str(int(d["geo"][i]["iso_numeric"])) for i in isos if d["geo"].get(i, {}).get("iso_numeric"))
    mp = x.get("map") or {}
    fixed = mp.get("countries")   # pays précisés dans le dossier (Gaza n'est pas la Cisjordanie)
    war = set().union(*fixed) if fixed else dossier.side_countries(sides[0], d) | dossier.side_countries(sides[1], d)
    ally = (dossier.side_countries(backers[0], d) | dossier.side_countries(backers[1], d)) - war
    return {"war": num(war), "ally": num(ally), "bounds": mp.get("bounds", [[-55, -170], [75, 180]]),
            "dots": [[lon, lat] for lat, lon in mp.get("anchors", [])]}

SWORDS = ('<svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" '
          'stroke-linejoin="round"><path d="M14.5 17.5 3 6V3h3l11.5 11.5M13 19l6-6M16 16l4 4M19 21l2-2"/></svg>')

def camp_marks(side, d):
    """Drapeaux d'un camp (ses États, deux au plus) ; un groupe armé ou un parti : un pictogramme."""
    states = [a for a in side["actors"] if d["actors"].get(a, {}).get("kind") == "state"][:2]
    if states:
        return "".join(f'<img src="{e(style.flag_url(a, d["actors"][a]))}" alt="">' for a in states)
    return f'<span class="ns" aria-hidden="true">{SWORDS}</span>'

def conflict_row(x, d):
    names = [s["name"] for s in x["sides"]]
    # résumé court rédigé pour la carte (champ card) ; à défaut, la première phrase du dossier
    first = x.get("card") or " ".join(x["lede"].split()).split(". ")[0].rstrip(".") + "."
    return f"""<a class="card conflict" href="{e(x['id'])}.html">
<svg class="wm" role="img" aria-label="Carte de la région : pays en guerre et soutiens étrangers" data-map='{e(json.dumps(conflict_map(x, d)))}'></svg>
<div class="body"><h3>{e(x['title'])}</h3>
<p class="vs">{camp_marks(x["sides"][0], d)}<span>{e(names[0])}</span><span class="vs-x">contre</span>{camp_marks(x["sides"][1], d)}<span>{e(style.mid(names[1]))}</span></p>
<p class="lede1">{e(first)}</p></div></a>"""

def cross_links(d):
    """Questions d'exemple de la page Relations (cross.EXAMPLES), avec les drapeaux des pays cités."""
    import cross
    out = []
    for q, title in cross.EXAMPLES:
        toks = q.split(",")
        flags = "".join(f'<img src="{e(style.flag_url(t, d["actors"][t]))}" alt="">'
                        for t in toks if d["actors"].get(t, {}).get("kind") in ("state", "bloc"))
        marks = flags + "".join(f'<span class="ns">{SWORDS}</span>' for t in toks if t.startswith("d:")) \
            + "".join(style.dep_icon(t[2:], 16) for t in toks if t.startswith("r:"))
        out.append(f'<a class="card" href="relations.html?e={e(q)}"><div class="marks">{marks}</div><h3>{e(title)}</h3></a>')
    return "".join(out)

def home(d, dossiers):
    built = "/".join(reversed(d["built"][:10].split("-")))
    body = f"""<section class="hero"><h1>{e(brand.BASELINE)}</h1>
<p>Guerres, alliances, sanctions, rivalités : qui s'oppose à qui, qui soutient qui, et pour quelles raisons.
Les rapports de force du monde rendus lisibles, sans prérequis.</p>
<p class="updated"><span class="tag">Mis à jour le {built}</span></p></section>

<section id="conflits"><h2>Comprendre les conflits en cours</h2>
<div class="conflicts">{"".join(conflict_row(x, d) for x in dossiers)}</div>
</section>

<section class="s"><h2>Croiser des acteurs</h2>
<p class="quiet" style="margin:-8px 0 18px">Choisissez des pays, un conflit ou une ressource : un schéma montre ce qui les relie, fait par fait.</p>
<div class="crossq">{cross_links(d)}
<a class="card pick" href="relations.html"><h3>Choisir moi-même</h3><p>Pays, groupes armés, conflits, ressources.</p></a></div></section>

<section class="s"><h2>La vue d'ensemble</h2>
<p class="quiet" style="margin:-8px 0 18px">Tous les acteurs d'un coup : alliances, soutiens et dépendances, pays par pays.</p>
<div class="explore">
<a class="card" href="vue-d-ensemble.html#organisations">{svg("orgs")}<h3>Les organisations</h3>
<p class="use">Voir qui appartient à quoi (OTAN, BRICS, Union européenne…), et quels pays sont à la croisée de plusieurs camps.</p></a>
<a class="card" href="vue-d-ensemble.html#carte">{svg("map")}<h3>La carte du monde</h3>
<p class="use">Voir de quel côté penche chaque pays, et depuis quand.</p></a>
<a class="card" href="vue-d-ensemble.html#graphe">{svg("graph")}<h3>Le graphe des soutiens</h3>
<p class="use">Suivre qui arme, qui finance et qui affronte qui.</p></a>
</div></section>
<p class="quiet" style="margin-top:56px">Pourquoi vulgariser la géopolitique, et comment ce site est fait : <a href="manifeste.html">le manifeste</a>.
Les mots du site sont définis dans le <a href="glossaire.html">glossaire</a>.</p>"""
    ld = {"@context": "https://schema.org", "@type": "WebSite", "name": brand.NAME, "url": brand.SITE, "inLanguage": "fr",
          "description": brand.DESCRIPTION, "license": "https://creativecommons.org/licenses/by/4.0/"}
    return page(f"{brand.NAME} — {brand.BASELINE}", body, "", desc=brand.DESCRIPTION, extra=WORLD_MAP, ld=ld)

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
    return page(f"Manifeste — {brand.NAME}", body, "manifeste.html", "Pourquoi vulgariser la géopolitique, et les règles du site : tout est sourcé, les faits sont séparés des analyses, aucune prédiction.")

def write(out, data):
    dossiers = dossier.load()
    (out / "index.html").write_text(home(data, dossiers), encoding="utf-8")
    (out / "manifeste.html").write_text(manifesto(data), encoding="utf-8")
