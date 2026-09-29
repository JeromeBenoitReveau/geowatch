"""Pages éditoriales : accueil (site/index.html) et manifeste (site/manifeste.html).
Chiffres et cartes de conflits calculés à partir des mêmes données que le reste du site."""
from html import escape as e
import yaml
import brand, dossier

CSS = """
:root{--bg:#fafaf8;--fg:#1c1c1c;--mute:#6b6b6b;--line:#e3e3df;--card:#fff;--accent:#2b6cb0;--hover:#f1f0ea}
@media (prefers-color-scheme:dark){:root{--bg:#141414;--fg:#eee;--mute:#9a9a9a;--line:#2c2c2c;--card:#1d1d1d;--accent:#7aa7e0;--hover:#242424}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.6 system-ui,sans-serif}
a{color:var(--accent)}main{max-width:1040px;margin:0 auto;padding:0 16px 64px}
header{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;padding:18px 0;border-bottom:1px solid var(--line)}
.logo{font-weight:700;font-size:18px;color:var(--fg);text-decoration:none;letter-spacing:-.01em}
nav a{color:var(--fg);text-decoration:none;margin-left:18px;font-size:14px}nav a:hover{color:var(--accent)}
.hero{padding:56px 0 40px;max-width:760px}.hero h1{font-size:40px;line-height:1.15;margin:0 0 14px;letter-spacing:-.02em}
.hero p{font-size:19px;color:var(--mute);margin:0}
h2{font-size:22px;margin:40px 0 6px}.sub{color:var(--mute);margin:0 0 16px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px}
.card{display:block;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px;color:var(--fg);text-decoration:none}
a.card:hover{border-color:var(--accent)}.card h3{font-size:19px;margin:0 0 6px}.card p{margin:0 0 10px}
.tag{display:inline-block;font-size:12px;padding:2px 8px;border-radius:10px;border:1px solid var(--line);color:var(--mute)}
.tag.live{border-color:var(--accent);color:var(--accent)}
.vs{font-weight:600;margin:8px 0}.odds{font-size:14px;color:var(--mute);border-top:1px solid var(--line);padding-top:10px;margin-top:10px}
.odds b{color:var(--fg);font-variant-numeric:tabular-nums}
.soon{background:transparent;padding:14px}.soon h3{font-size:16px;margin:0 0 4px}.soon .more{font-size:13px}
.grid.featured{grid-template-columns:repeat(auto-fit,minmax(300px,1fr))}.featured .card p,.featured .card .vs{max-width:640px}
.grid.small{grid-template-columns:repeat(auto-fill,minmax(220px,1fr));align-items:start}.soon-title{font-size:16px;margin:28px 0 2px}
.explore{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:14px}
.explore .card svg{width:40px;height:40px;stroke:var(--accent);margin-bottom:8px}
.explore .go{font-size:14px;color:var(--accent)}
.mute{color:var(--mute);font-size:14px}footer{margin-top:56px;padding-top:16px;border-top:1px solid var(--line)}
.prose{max-width:720px}.prose h1{font-size:34px;line-height:1.2;margin:40px 0 10px}.prose h2{font-size:21px}
.prose ol li,.prose ul li{margin-bottom:8px}
@media (max-width:600px){.hero h1{font-size:30px}.hero{padding:32px 0 24px}nav a{margin:0 14px 0 0}}
"""

ICON = {  # Lucide (ISC) ; « orgs » : deux cercles qui se recoupent, dessiné pour le site
    "orgs": '<circle cx="9" cy="12" r="6"/><circle cx="15" cy="12" r="6"/>',
    "map": '<circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/>',
    "graph": '<circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" x2="15.42" y1="13.51" y2="17.49"/><line x1="15.41" x2="8.59" y1="6.51" y2="10.49"/>',
}
svg = lambda k: (f'<svg viewBox="0 0 24 24" fill="none" stroke-width="1.6" stroke-linecap="round" '
                 f'stroke-linejoin="round" aria-hidden="true">{ICON[k]}</svg>')

def shell(title, body, desc=brand.BASELINE):
    return f"""<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title><meta name="description" content="{e(desc)}"><style>{CSS}</style></head><body><main>
<header><a class="logo" href="index.html">{e(brand.NAME)}</a>
<nav><a href="index.html#conflits">Conflits</a><a href="explorer.html">Explorer</a><a href="manifeste.html">Manifeste</a><a href="methode.html">Méthode</a></nav></header>
{body}
<footer class="mute">{e(brand.NAME)} — projet indépendant et open source. Code MIT, données CC BY 4.0 ·
<a href="{brand.REPO}">GitHub</a> · <a href="methode.html">méthode et sources</a></footer>
</main></body></html>"""

def upcoming():
    return (yaml.safe_load(dossier.PATH.read_text(encoding="utf-8")) or {}).get("upcoming", [])

def dossier_card(x, d):
    names = [s["name"] for s in x["sides"]]
    ids = [set(s["actors"]) for s in x["sides"]]
    backers = {ed["from"] for ed in d["edges"] for i in ids
               if ed["to"] in i and ed["from"] not in i and ed["status"] != "ended"}
    ms = [m for m in (d["markets"].get(x.get("dyad"), {}) or {}).get("markets", []) if not m["stale"]]
    labels = x.get("market_labels") or {}
    odds = (f'<div class="odds">{e(labels.get(ms[0]["question"], ms[0]["question"]))} '
            f'<b>{round(ms[0]["prob"] * 100)} %</b> selon les parieurs de {e(ms[0]["source"].capitalize())}</div>') if ms else ""
    first = " ".join(x["lede"].split()).split(". ")[0].rstrip(".") + "."
    return f"""<a class="card" href="{e(x['id'])}.html"><span class="tag live">Dossier · depuis {e(dossier.fr_date(x['since']))}</span>
<h3 style="margin-top:10px">{e(x['title'])}</h3><div class="vs">{e(names[0])} contre {e(names[1][:1].lower() + names[1][1:])}</div>
<p>{e(first)}</p><div class="mute">{len(backers)} puissances étrangères impliquées · lire le dossier →</div>{odds}</a>"""

def soon_card(u, d):
    ids = set(u["actors"])
    n = sum(1 for ed in d["edges"] if ed["to"] in ids and ed["from"] not in ids and ed["status"] != "ended")  # soutiens reçus
    return f"""<a class="card soon" href="explorer.html#graphe:{e(u['actors'][0])}">
<h3>{e(u['title'])}</h3><div class="more mute">{n} soutien{"s" if n > 1 else ""} étranger{"s" if n > 1 else ""} documenté{"s" if n > 1 else ""} · explorer →</div></a>"""

def home(d, dossiers):
    groups = d["align"]["groups"]
    body = f"""<section class="hero"><h1>{e(brand.BASELINE)}</h1>
<p>Les conflits expliqués simplement : les camps, leurs soutiens étrangers, ce qu'ils y cherchent et ce qui est en jeu.
Chaque affirmation est sourcée.</p></section>

<h2 id="conflits">Les conflits en cours</h2><p class="sub">Un dossier se lit en quelques minutes, sans connaissance préalable.</p>
<div class="grid featured">{"".join(dossier_card(x, d) for x in dossiers)}</div>
<h3 class="soon-title">En préparation</h3><p class="sub">Déjà dans le graphe, bientôt racontés.</p>
<div class="grid small">{"".join(soon_card(u, d) for u in upcoming())}</div>

<h2>Explorer par soi-même</h2><p class="sub">Pour aller plus loin que les dossiers.</p>
<div class="explore">
<a class="card" href="explorer.html#organisations">{svg("orgs")}<h3>Comprendre les organisations</h3>
<p>OTAN, BRICS, Union européenne, OCS… Qui appartient à quoi, et quels pays sont à la croisée de plusieurs camps.</p>
<span class="go">{len(groups)} organisations et alliances →</span></a>
<a class="card" href="explorer.html#carte">{svg("map")}<h3>La carte du monde</h3>
<p>Les blocs d'influence, les votes à l'ONU et les organisations, pays par pays, avec leur évolution depuis 2014.</p>
<span class="go">{len(d["geo"])} pays →</span></a>
<a class="card" href="explorer.html#graphe">{svg("graph")}<h3>Le graphe des soutiens</h3>
<p>Qui arme, finance ou soutient qui : États, groupes armés, partis et personnalités, relation par relation.</p>
<span class="go">{len(d["actors"])} acteurs, {len(d["edges"])} relations →</span></a>
</div>
<p class="mute" style="margin-top:28px">Pourquoi ce site, et comment il est fait : <a href="manifeste.html">le manifeste</a>.</p>"""
    return shell(f"{brand.NAME} — {brand.BASELINE}", body)

def manifesto(d):
    body = f"""<article class="prose">
<h1>Manifeste</h1>
<p class="mute">Pourquoi {e(brand.NAME)} existe, et comment il est fait.</p>

<h2>Le constat</h2>
<p>On n'a jamais eu autant d'informations sur les conflits : dépêches en continu, tableaux de bord, cartes des combats,
indicateurs de tension. Mais ces outils répondent surtout à la question « que se passe-t-il ? ». Ils laissent de côté
celle qui permet vraiment de comprendre : <b>qui est derrière qui, et pourquoi ?</b></p>
<p>La <a href="soudan.html">guerre au Soudan</a>, par exemple, oppose deux généraux, mais c'est aussi une rivalité entre
puissances régionales, une course à l'or et une bataille pour la mer Rouge. Sans ces relations, les chiffres restent
froids et l'actualité incompréhensible.</p>

<h2>Notre objectif</h2>
<p>Rendre lisibles les relations qui font la géopolitique (entre États, alliances, groupes armés, partis et
personnalités), pour quelqu'un qui n'y connaît rien. En quelques minutes, un dossier doit permettre de répondre à
quatre questions : qui s'affronte ? qui les soutient ? qu'y cherchent-ils ? qu'est-ce qui est en jeu ?</p>

<h2>Notre démarche</h2>
<ol>
<li><b>Tout est sourcé.</b> Chaque relation, chaque phrase d'un dossier renvoie à ses sources : organisations
internationales, centres de recherche, presse de référence. Aujourd'hui : {len(d["edges"])} relations, toutes sourcées.</li>
<li><b>Les faits d'un côté, l'analyse de l'autre.</b> « L'Égypte arme l'armée soudanaise » est un fait documenté.
« Pour protéger ses intérêts sur le Nil » est une analyse : elle est toujours attribuée à qui la formule. Quand les
analyses divergent, on le dit plutôt que de trancher.</li>
<li><b>Montrer le doute.</b> Un soutien démenti ou non prouvé est marqué « allégué », avec un niveau de confiance.
Une relation sans date connue le reste, plutôt que de lui en inventer une.</li>
<li><b>Aucune probabilité inventée.</b> Le site ne prédit rien. Les seuls pourcentages de probabilité affichés sont
des cotes de marchés de prédiction réels, avec leur source : ce qu'anticipent des parieurs, pas une vérité.</li>
<li><b>Tous les camps, avec la même exigence.</b> On montre les soutiens de chaque côté, qu'ils viennent de
démocraties ou de dictatures, d'alliés ou de rivaux de la France.</li>
<li><b>Relu par un humain.</b> Des outils automatiques peuvent proposer des mises à jour, mais rien n'entre dans le
graphe sans relecture.</li>
<li><b>Ouvert.</b> Le code est libre (MIT), les données sont réutilisables (CC BY 4.0), et chacun peut proposer une
correction <a href="{brand.REPO}">sur GitHub</a>.</li>
</ol>

<h2>Ce que ce site n'est pas</h2>
<ul>
<li><b>Pas un fil d'actualité.</b> Les dossiers sont revus régulièrement, pas en temps réel. Pour suivre les événements
heure par heure, les médias et les tableaux de bord spécialisés restent indispensables.</li>
<li><b>Pas exhaustif.</b> Un conflit n'est ajouté que lorsque ses relations peuvent être sourcées sérieusement.</li>
<li><b>Pas un outil de prédiction.</b> Les cotes des marchés sont montrées pour ce qu'elles sont, et leur fiabilité
passée est mesurée publiquement (voir la <a href="methode.html#marches">méthode</a>).</li>
</ul>

<h2>Comment c'est fait</h2>
<p>Un graphe de relations tenu à la main, des alliances formelles datées, les votes à l'Assemblée générale de l'ONU, des
données de la Banque mondiale et de Wikidata, et les cotes de Polymarket et Kalshi relevées toutes les six heures.
Le détail, source par source et règle par règle : <a href="methode.html">méthode et sources</a>.</p>
</article>"""
    return shell(f"Manifeste — {brand.NAME}", body, "Pourquoi ce site existe, et comment il est fait.")

def write(out, data):
    dossiers = dossier.load()
    (out / "index.html").write_text(home(data, dossiers), encoding="utf-8")
    (out / "manifeste.html").write_text(manifesto(data), encoding="utf-8")
