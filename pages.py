"""Pages éditoriales : accueil (site/index.html) et manifeste (site/manifeste.html).
Chiffres et liste des conflits calculés à partir des mêmes données que le reste du site ; mise en forme commune
dans style.py (style.css)."""
from html import escape as e
import brand, dossier, style

CSS = """
.hero{padding:88px 0 40px;max-width:780px}.hero h1{font-size:48px;line-height:1.08}
.hero p{font-size:19px;color:var(--graphite);margin:0;max-width:34em}
.conflicts{display:grid;gap:16px}
.conflict{display:grid;grid-template-columns:minmax(0,1fr) 240px;gap:24px;padding:24px}
.conflict h3{font-size:25px;margin:0 0 6px}
.conflict .vs{margin:0 0 10px;font-size:15px}.conflict .vs span{display:inline-block;width:9px;height:9px;border-radius:50%;margin:0 6px 0 0}
.conflict p{margin:0;max-width:40em}.conflict .go{margin-top:14px;font-size:15px;text-decoration:underline;text-decoration-color:var(--peach);text-decoration-thickness:1.5px;text-underline-offset:3px;width:max-content}
.odds{padding:18px 18px 16px;align-self:stretch;display:flex;flex-direction:column;justify-content:center}
.odds b{font:400 44px/1 var(--serif);font-variant-numeric:tabular-nums;margin-bottom:8px}
.odds span{font-size:14.5px;line-height:1.4}.odds small{margin-top:8px;font-size:13px;color:var(--graphite)}
.explore{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}
.explore .card{padding:22px}.explore .ico{display:block;margin-bottom:12px}
.explore p{margin:0 0 14px;font-size:15.5px;color:var(--graphite)}.explore .count{font-size:14px;color:var(--ink)}
.page{padding:64px 0 0}.page h2{margin-top:40px}.page ol li,.page ul li{margin-bottom:10px}
@media (max-width:760px){.hero{padding:48px 0 28px}.hero h1{font-size:34px}.conflict{grid-template-columns:1fr;padding:20px}
  .explore{grid-template-columns:1fr}}
"""

svg = lambda k: style.icon(k, 28)

def page(title, body, current, desc=brand.BASELINE):
    return style.head(title, desc, f"<style>{CSS}</style>") + f"""<body><div class="wrap">{style.top(current)}
{body}</div>{style.foot()}</body></html>"""

def conflict_row(x, d):
    names = [s["name"] for s in x["sides"]]
    # encart : les soutiens étrangers de chaque camp, lus dans le graphe (pas de cote ni de probabilité)
    ids = [set(sd["actors"]) for sd in x["sides"]]
    per_side = [len({ed["from"] for ed in d["edges"] if ed["to"] in i and ed["from"] not in i and ed["status"] != "ended"}) for i in ids]
    short = lambda n: n[:1].lower() + n[1:]
    odds = (f'<div class="odds tint"><b>{sum(per_side)}</b><span>puissances étrangères impliquées</span>'
            f'<small>{per_side[0]} {"soutient" if per_side[0] == 1 else "soutiennent"} {e(short(names[0]))}, {per_side[1]} {e(short(names[1]))}</small></div>')
    first = " ".join(x["lede"].split()).split(". ")[0].rstrip(".") + "."
    return f"""<a class="card conflict" href="{e(x['id'])}.html"><div><h3>{e(x['title'])}</h3>
<p class="vs"><span style="background:var(--a)"></span>{e(names[0])} contre <span style="background:var(--b);margin-left:4px"></span>{e(names[1][:1].lower() + names[1][1:])}</p>
<p>{e(first)}</p><p class="go">Lire le dossier</p></div>{odds}</a>"""

def home(d, dossiers):
    groups = d["align"]["groups"]
    body = f"""<section class="hero"><h1>{e(brand.BASELINE)}</h1>
<p>Guerres, alliances, sanctions, rivalités : qui s'oppose à qui, qui soutient qui, et pour quelles raisons.
Les rapports de force du monde rendus lisibles, sans prérequis. Chaque affirmation est sourcée.</p></section>

<section id="conflits"><h2>Comprendre les conflits en cours</h2>
<div class="conflicts">{"".join(conflict_row(x, d) for x in dossiers)}</div>
</section>

<section class="s"><h2>Explorer les rapports de force</h2>
<div class="explore">
<a class="card" href="explorer.html#organisations">{svg("orgs")}<h3>Comprendre les organisations</h3>
<p>OTAN, BRICS, Union européenne, OCS : qui appartient à quoi, et quels pays sont à la croisée de plusieurs camps.</p>
<span class="count">{len(groups)} organisations et alliances</span></a>
<a class="card" href="explorer.html#carte">{svg("map")}<h3>La carte du monde</h3>
<p>Les camps qui structurent le monde, pays par pays : blocs d'influence, votes à l'ONU, évolution depuis 2014.</p>
<span class="count">{len(d["geo"])} pays</span></a>
<a class="card" href="explorer.html#graphe">{svg("graph")}<h3>Le graphe des soutiens</h3>
<p>Qui arme, finance ou soutient qui, et qui s'affronte : États, groupes armés, partis et personnalités.</p>
<span class="count">{len(d["actors"])} acteurs, {len(d["edges"])} relations</span></a>
</div></section>
<p class="quiet" style="margin-top:56px">Pourquoi vulgariser la géopolitique, et comment ce site est fait : <a href="manifeste.html">le manifeste</a>.</p>"""
    return page(f"{brand.NAME} — {brand.BASELINE}", body, "")

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
correction <a href="{brand.REPO}">sur GitHub</a>.</li>
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
