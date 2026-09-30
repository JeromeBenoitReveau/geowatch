"""Page « Méthode & sources » (site/methode.html), générée à chaque build à partir des mêmes données
que le site : chiffres, versions et dates ne peuvent pas dériver de ce qui est affiché."""
from collections import Counter
from html import escape as e
from urllib.parse import urlparse
import re
import brand, style
from sources.profiles import INDICATORS

URL = re.compile(r"https?://\S+")

def _src(s):
    """Texte de source → HTML, URL cliquable."""
    out, last = [], 0
    for m in URL.finditer(s):
        out += [e(s[last:m.start()]), f'<a href="{e(m.group())}">{e(urlparse(m.group()).netloc)}</a>']
        last = m.end()
    return "".join(out + [e(s[last:])])

def _date(s):
    return (s or "")[:10] or "n/d"

def page(d):
    actors, edges, al, unga = d["actors"], d["edges"], d["align"], d["unga"] or {}
    kinds = Counter(a["kind"] for a in actors.values())
    urls = [u for x in edges for s in x["sources"] for u in URL.findall(s)]
    domains = Counter(urlparse(u).netloc for u in urls)
    prof_dates = sorted(p["fetched_at"] for p in d["profiles"].values() if p.get("fetched_at"))
    roles = Counter(v["role"] for k, v in d["influence"].items() if k in actors)
    src = unga.get("source", {})
    formal = [g for g in al["groups"] if g.get("kind") != "forum"]
    forums = [g for g in al["groups"] if g.get("kind") == "forum"]
    blocs = al["blocs"]
    drift = unga.get("drift") or []

    def moves(g):
        m = [f"création {e(g['since'])}"] if g.get("since") else []
        m += [f"{e(k)} +{e(v)}" for k, v in sorted((g.get("joined") or {}).items(), key=lambda x: x[1]) if v != g.get("since")]
        m += [f"{e(k)} −{e(v)}" for k, v in sorted((g.get("left") or {}).items(), key=lambda x: x[1])]
        return "<br>".join(m) or "—"

    def group_rows(gs):
        return "".join(
            f"<tr><td>{e(g['name'])}</td><td>{e(blocs[g['bloc']]['name']) if g.get('bloc') else 'forum'}</td>"
            f"<td>{g['level'] if g.get('kind') != 'forum' else '—'}</td><td>{len(g['members'])}</td>"
            f"<td>{moves(g)}</td>"
            f"<td>{'<br>'.join(_src(s) for s in g['sources'])}</td></tr>" for g in gs)

    kind_fr = {"state": ("État", "États"), "bloc": ("bloc", "blocs"),
               "non_state": ("groupe armé non étatique", "groupes armés non étatiques"),
               "party": ("parti", "partis"), "person": ("personnalité", "personnalités")}
    role_fr = {"member": ("membre", "membres"), "satellite": ("satellite", "satellites"),
               "contested": ("disputé", "disputés"), "none": ("non classé", "non classés")}
    fr = lambda table, k, n: table.get(k, (k, k))[n > 1]
    extra = """<style>
main.m{max-width:820px;padding:56px 0 0}main.m h2{margin:52px 0 12px}main.m h3{font:500 18px/1.3 var(--serif);margin:24px 0 6px}
main.m p,main.m li{max-width:44em}.mute{color:var(--graphite);font-size:14px}
table{width:100%;border-collapse:collapse;font-size:14px;margin:10px 0}th,td{text-align:left;padding:8px 10px 8px 0;border-bottom:1px solid var(--mist);vertical-align:top}
th{color:var(--graphite);font-weight:500}.scroll{overflow-x:auto}code{font-size:13.5px}
.flow{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:20px 28px;margin:16px 0}
.flow div{font-size:14.5px}.flow b{display:block;font-family:var(--serif);font-weight:500;font-size:17px;margin-bottom:2px}
nav.toc{display:flex;flex-wrap:wrap;gap:4px 18px;font-size:14px;color:var(--graphite);margin:18px 0 0}nav.toc a{text-decoration:none}nav.toc a:hover{text-decoration:underline}
.kpi{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:20px;margin:28px 0 0}
.kpi b{display:block;font:400 32px/1 var(--serif);font-variant-numeric:tabular-nums;margin-bottom:4px}.kpi span{font-size:14px;color:var(--graphite)}
</style>"""
    return style.head(f"Méthode et sources — {brand.NAME}", "Comment les données sont construites, et d'où elles viennent.", extra) + f"""<body><div class="wrap">{style.top("methode.html")}<main class="m">
<h1>Méthode et sources</h1>
<p class="meta">Page générée automatiquement le {_date(d["built"])} à partir des données publiées. Code sous licence MIT,
données du graphe sous CC BY 4.0 — <a href="{brand.REPO}">dépôt GitHub</a>.</p>
<nav class="toc"><a href="#principe">Principe</a><a href="#chaine">Chaîne de données</a><a href="#graphe">Graphe</a>
<a href="#dossiers">Dossiers</a><a href="#tensions">Tensions</a><a href="#blocs">Blocs</a><a href="#onu">Votes ONU</a><a href="#taille">Taille</a>
<a href="#profils">Profils</a><a href="#carte">Carte</a><a href="#explorateur">Explorateur</a><a href="#glossaire">Glossaire</a><a href="#limites">Limites</a><a href="#contribuer">Contribuer</a></nav>

<div class="kpi">
  <div><b>{len(actors)}</b><span class="mute">acteurs</span></div>
  <div><b>{len(edges)}</b><span class="mute">relations de soutien</span></div>
  <div><b>{len(urls)}</b><span class="mute">sources citées ({len(domains)} sites)</span></div>
  <div><b>{len(d["geo"])}</b><span class="mute">pays sur la carte</span></div>
  <div><b>{len(unga.get("countries", {}))}</b><span class="mute">pays avec votes ONU</span></div>
</div>

<h2 id="principe">Principe</h2>
<p>{e(brand.NAME)} montre <b>qui soutient qui</b> dans les conflits en cours, sous forme d'un graphe dont chaque relation est
sourcée, datée et relue à la main, et le relie à ce qui se mesure : liens formels entre États, votes à l'ONU,
dépenses militaires.</p>
<p><b>Règle non négociable : aucune probabilité.</b> {e(brand.NAME)} ne prédit rien et n'affiche aucune cote de paris ni
de marché de prédiction : c'est un site d'information, pas de pronostic. Les pourcentages affichés sont des mesures
(part des votes identiques à l'ONU, part du territoire occupé, part du PIB…), avec leur source.</p>
<p>Deux règles de conception : rien n'est pondéré à la main (tailles, couleurs et classements découlent de données
publiées ou de règles écrites ici) ; rien n'entre dans le graphe sans source et sans relecture humaine.</p>

<h2 id="chaine">Chaîne de données</h2>
<div class="flow">
  <div><b>1. Curation</b><code>network.yaml</code> (relations de soutien) et <code>alignments.yaml</code> (traités, adhésions,
  forums), édités à la main, contrôlés par <code>validate.py</code> à chaque changement.</div>
  <div><b>2. Collecte automatique</b>GitHub Actions : profils pays, coordonnées, photos et votes ONU le 1er du mois.</div>
  <div><b>3. Stockage ouvert</b>Tout est versionné dans le dépôt, dossier <code>data/</code> : CSV et JSON lisibles,
  historique complet dans git.</div>
  <div><b>4. Calculs</b><code>network.influence()</code> (blocs), et <code>sources/unga.py</code> (votes) —
  règles détaillées ci-dessous.</div>
  <div><b>5. Publication</b><code>build.py</code> génère ce site statique et les exports
  <a href="network.json">network.json</a> / <a href="network.csv">network.csv</a> ; GitHub Pages le publie.</div>
</div>
<div class="scroll"><table>
<tr><th>Source</th><th>Ce qu'on en tire</th><th>Fréquence</th><th>Dernière mise à jour</th><th>Licence</th></tr>
<tr><td>Relecture humaine, {len(domains)} sites cités (ONU, Trésor américain, Conseil de l'UE, SIPRI, Kremlin, presse…)</td>
  <td>Relations de soutien</td><td>à la main</td><td>vérifications de {min((x["verified"] for x in edges), default="n/d")} à {max((x["verified"] for x in edges), default="n/d")}</td><td>CC BY 4.0 (notre travail)</td></tr>
<tr><td><a href="https://data.worldbank.org">Banque mondiale</a> (WDI)</td><td>Démographie, économie, ressources, défense</td>
  <td>mensuelle</td><td>{_date(prof_dates[-1] if prof_dates else None)}</td><td>CC BY 4.0</td></tr>
<tr><td><a href="https://www.wikidata.org">Wikidata</a></td><td>Régime, chef d'État, coordonnées, codes pays</td>
  <td>mensuelle</td><td>{_date(prof_dates[-1] if prof_dates else None)}</td><td>CC0</td></tr>
<tr><td><a href="{e(src.get("url", "#"))}">{e(src.get("name", "Voeten, UNGA"))}</a></td><td>Accord de vote à l'ONU, dérive transatlantique</td>
  <td>si nouvelle version</td><td>version {e(src.get("version", "n/d"))} du {_date(src.get("published"))}</td><td>{e(src.get("license", "CC0"))}</td></tr>
<tr><td><a href="https://commons.wikimedia.org">Wikimedia Commons</a></td><td>Photos des personnalités</td><td>mensuelle</td><td>—</td>
  <td>{", ".join(sorted({e(p["license"]) for p in d["people"].values()})) or "—"} ; auteur crédité dans chaque fiche</td></tr>
<tr><td><a href="https://www.naturalearthdata.com">Natural Earth</a> via <a href="https://github.com/topojson/world-atlas">world-atlas</a></td>
  <td>Contours des pays</td><td>—</td><td>—</td><td>domaine public</td></tr>
<tr><td><a href="https://lucide.dev">Lucide</a>, <a href="https://flagicons.lipis.dev">flag-icons</a></td><td>Icônes, drapeaux</td><td>—</td><td>—</td><td>ISC, MIT</td></tr>
</table></div>

<h2 id="graphe">Le graphe des soutiens</h2>
<p>{", ".join(f"{n} {fr(kind_fr, k, n)}" for k, n in kinds.most_common())}. Chaque relation a :</p>
<ul>
<li><b>types</b> : armes, financement, formation, troupes, renseignement, politique, économique, double usage ;</li>
<li><b>statut</b> : actif, réduit, terminé, allégué ; <b>confiance</b> : élevée (documenté officiellement), moyenne
(sources concordantes), faible (allégations) ;</li>
<li><b>lecture sur le graphe et la carte</b> : deux dimensions, deux codages. Le <b>statut</b> se lit au tracé (plein =
actif, tirets = en baisse ou allégué), la <b>confiance</b> à l'épaisseur (épais = élevée, moyen = moyenne, fin = faible) ;</li>
<li><b>sources</b> : au moins une, avec URL ouverte et relue ; <b>verified</b> : mois de la dernière vérification
(signalée au-delà de 6 mois).</li>
</ul>
<p>Sites les plus cités : {", ".join(f"{e(dom)} ({n})" for dom, n in domains.most_common(8))}.</p>
<p><b>Dates</b> : <code>since</code> est la plus ancienne date documentée par les sources citées — pas forcément le vrai
début d'une relation (l'aide américaine à l'Ukraine est datée de 2022 car la source couvre la période depuis l'invasion) ;
<code>until</code> marque une fin. Le curseur « Année » du site n'affiche que les relations actives l'année choisie ;
{sum(1 for x in edges if not x.get("since"))} relation(s) sans date restent affichées toutes les années.</p>
<p><code>validate.py</code> refuse une relation sans source, avec un acteur inconnu ou une valeur hors liste, et tourne sur
GitHub à chaque modification. <code>update_network.py</code> peut proposer des mises à jour (Claude + recherche web) dans un
fichier séparé : rien n'entre dans le graphe sans relecture.</p>
<p>Partis et personnalités forment un calque « détail » : ils sont rattachés à leur pays et ne sont jamais classés dans un bloc.</p>
<p><b>Qui est une « personnalité » ?</b> Seulement une personne qui a au moins une relation sourcée <i>qui lui est propre</i>,
distincte de l'institution qu'elle dirige : Elon Musk, ou Donald Trump et JD Vance pour leurs soutiens personnels à des partis
étrangers. Un chef d'État ou de groupe armé qui n'agit qu'à travers son institution (le général al-Burhan pour l'armée
soudanaise, Hemedti pour les FSR) n'est pas un nœud : il apparaît comme <b>dirigeant</b> sur la fiche de l'acteur et dans
les dossiers, pour ne pas dédoubler l'acteur. {sum(1 for a in actors.values() if a.get("leader"))} acteur(s) ont un dirigeant renseigné.</p>

<h2 id="dossiers">Dossiers et « pourquoi »</h2>
<p>Un dossier (<code>dossiers.yaml</code>) explique un conflit à quelqu'un qui n'y connaît rien : les deux camps, leurs
soutiens étrangers, les enjeux, le coût humain, la chronologie et la situation actuelle.
Les camps et les soutiens sont <b>lus dans le graphe</b> : un dossier ne peut pas contredire <code>network.yaml</code>.</p>
<p>Chaque soutien peut porter un <b>« pourquoi »</b> (champ <code>why</code>) : la motivation de l'acteur en une phrase.
C'est une <b>analyse, pas un fait</b> : elle est attribuée à qui la formule (« selon Crisis Group… ») et couverte par une
source de la relation. Quand les analyses divergent, le dossier doit le dire plutôt que trancher. Dans la chronologie,
« premier soutien documenté » renvoie à la date <code>since</code>, la plus ancienne attestée par les sources.</p>
<p>Dossiers publiés : {", ".join(f'<a href="{e(x["id"])}.html">{e(x["title"])}</a>' for x in d.get("dossiers", [])) or "aucun"}.
{sum(1 for x in edges if x.get("why"))} relation(s) sur {len(edges)} ont un « pourquoi ».</p>

<h2 id="tensions">Tensions</h2>
<p>À côté des soutiens, le graphe recense des <b>tensions</b> (clé <code>tensions</code> de <code>network.yaml</code>) :
guerre ouverte, sanctions, revendication territoriale, rivalité stratégique sans guerre. Elles sont sourcées et datées
comme les soutiens, mais tenues à part : elles <b>n'entrent pas</b> dans le calcul des blocs d'influence ni dans la
liste des soutiens d'un dossier, et ne modifient pas la disposition du graphe. Une tension en trêve ou cessez-le-feu
est affichée atténuée. {len(d.get("tensions", []))} tension(s) recensée(s).</p>

<h2 id="blocs">Blocs d'influence</h2>
<p>Deux blocs : {" et ".join(f'<b style="color:{b["color"]}">{e(b["name"])}</b>' for b in blocs.values())}.
Seuls les <b>liens formels</b> (traités, adhésions) sont déclarés, avec un niveau :</p>
<ul><li><b>3</b> défense mutuelle · <b>2</b> partenariat stratégique sans défense mutuelle · <b>1</b> candidature ou
participation gelée · <b>0</b> intégration sans effet sur l'alignement (zone euro, Schengen).</li></ul>
<p>Sur le site, le niveau s'affiche en clair : « défense mutuelle (niveau 3 sur 3) », « partenariat stratégique (niveau 2
sur 3) », « lien formel partiel (niveau 1 sur 3) », avec la définition au survol (glossaire).</p>
<div class="scroll"><table><tr><th>Groupe</th><th>Bloc</th><th>Niveau</th><th>Pays</th><th>Depuis 2014</th><th>Sources</th></tr>{group_rows(formal)}</table></div>
<h3>Règles de calcul (<code>network.influence()</code>)</h3>
<ol>
<li><b>Membre</b> : un pays reçoit le niveau le plus élevé de ses liens formels. À niveau égal avec les deux blocs, il est « disputé ».</li>
<li><b>Satellite</b> : un acteur sans lien formel dont <i>tous</i> les soutiens actifs viennent de membres (niveau ≥ 2) d'un même bloc.
Exemple : les Houthis, soutenus uniquement par l'Iran.</li>
<li><b>Disputé</b> : soutiens actifs venant des deux blocs (ex. Inde : Russie et France).</li>
<li>Seuls les soutiens <i>actifs</i> comptent ; les soutiens réduits ou terminés sont affichés mais ignorés.</li>
</ol>
<p>Résultat actuel pour les acteurs du graphe : {", ".join(f"{n} {fr(role_fr, r, n)}" for r, n in roles.most_common())}.
La carte colore chaque pays selon son bloc, plus ou moins intensément selon le niveau.</p>
<h3>Forums économiques et politiques</h3>
<p>BRICS, OCS, G7… sont des cadres de coopération, pas des alliances (les BRICS réunissent l'Inde et la Chine). Ils sont
affichés (vue « Organisations » de l'explorateur, fiches pays) mais <b>n'entrent pas dans le calcul des blocs</b>.</p>
<h3>Adhésions et départs datés</h3>
<p>Chaque groupe peut dater ses adhésions (<code>joined</code>, ex. « FI +2023-04 ») et ses départs (<code>left</code>, anciens
membres, ex. « GB −2020-01 ») depuis 2014, début du curseur « Année ». Un membre sans date l'était déjà en 2014. Chaque
date est couverte par une source du groupe. Un pays compte comme membre une année donnée s'il y est entré cette année-là
ou avant, et n'en est pas sorti cette année-là ou avant. Ces dates animent les calques de la carte ; le calcul des blocs
d'influence, lui, reste fondé sur la composition actuelle.</p>
<div class="scroll"><table><tr><th>Forum</th><th></th><th></th><th>Pays</th><th>Depuis 2014</th><th>Sources</th></tr>{group_rows(forums)}</table></div>

<h2 id="onu">Votes à l'Assemblée générale de l'ONU</h2>
<p>Source : {e(src.get("name", ""))}, version {e(src.get("version", "n/d"))} — {e(src.get("cite", ""))}.</p>
<p><b>Placement des pays</b> ({unga.get("agreement_year", "n/d")}, dernière année disponible pour les taux d'accord) :
pour chaque pays, part des votes enregistrés identiques à ceux de la France et de l'Allemagne (moyenne des deux), et à ceux
de la Russie et de la Chine. <code>penchant = accord(France, Allemagne) − accord(Russie, Chine)</code>, entre −1 et +1.
Un pays de référence n'est comparé qu'à l'autre membre de son groupe. Le site ne montre pas ce nombre brut : il l'exprime
en <b>points d'écart</b> (×100, de −100 à +100) : « penche vers Russie/Chine (écart de 36 points) » ; entre −5 et +5
points, le pays est « entre les deux » (<code>sources/unga.py</code>, <code>build.py</code>).</p>
<p><b>Dérive transatlantique</b> : écart entre les États-Unis et la moyenne France/Allemagne sur l'« axe idéal » de Voeten,
jusqu'à {drift[-1]["year"] if drift else "n/d"} ({" → ".join(f'{x["us_gap"]} en {x["year"]}' for x in drift[-2:])} ;
France ↔ Allemagne : {drift[-1]["fr_de_gap"] if drift else "n/d"}). Cet axe unique mesure bien l'écart entre deux pays, mais
il ne sert pas à placer un pays entre deux blocs : en 2025, des votes communs États-Unis/Russie y font artificiellement
« remonter » la Russie vers l'Occident.</p>
<p><b>À lire avec prudence</b> : voter ensemble à l'ONU est un alignement diplomatique, pas militaire. Beaucoup de votes du
Sud global (développement, décolonisation) coïncident avec ceux de la Chine : pencher vers Russie/Chine n'est pas appartenir
à l'axe. Les votes adoptés par consensus, sans scrutin, ne sont pas comptés.</p>

<h2 id="taille">Taille des acteurs</h2>
<p>Sur le graphe et dans la vue Organisations, au choix : dépenses militaires en dollars (Banque mondiale <code>MS.MIL.XPND.CD</code>), PIB en dollars
(<code>NY.GDP.MKTP.CD</code>), population (<code>SP.POP.TOTL</code>), nombre de soutiens accordés dans le graphe, ou même taille pour tous. Dans la vue Organisations,
la taille est relative au plus grand pays affiché, et le panneau donne le total de chaque organisation et la part de ses trois premiers membres. Échelle en racine carrée ; l'UE utilise l'agrégat
Banque mondiale « EUU ». Sur la carte : dépenses militaires. Sans donnée (Taïwan, que la Banque mondiale ne couvre pas ; groupes armés) : taille minimale.</p>

<h2 id="profils">Profils pays</h2>
<p>Banque mondiale (dernière année disponible, souvent avec 1 à 2 ans de retard) : {", ".join(f"<code>{c}</code>" for c in INDICATORS.values())}.
Wikidata : forme de gouvernement (P122), chef d'État (P35), coordonnées (P625), codes ISO (P297, P298, P299).
La « forme de gouvernement » Wikidata est la forme officielle, pas le fonctionnement réel.</p>

<h2 id="carte">Carte</h2>
<p>Contours Natural Earth (domaine public), sans serveur de tuiles. Chaque acteur est placé dans son pays d'ancrage
(coordonnées Wikidata) ; plusieurs acteurs d'un même pays sont disposés en couronne. Un groupe armé reste dans son pays
d'origine même s'il agit ailleurs. Seule l'UE a une position fixée à la main (Bruxelles).</p>

<h2 id="explorateur">Explorateur (carte, graphe, organisations)</h2>
<p><b>Vue simplifiée</b> : au premier chargement, le graphe et la carte n'affichent que les guerres et les troupes engagées
(moins de 15 relations), pour être lisibles sans rien toucher. « Tout afficher » rétablit toutes les relations ; la légende,
dans les filtres, sert aussi de filtre. Un acteur sans aucune relation affichée est masqué.</p>
<p><b>Questions pour commencer</b> (<code>presets.yaml</code>) : chacune appartient à un onglet et ne s'affiche que dans celui-ci (elle ne change jamais d'onglet) ; changer d'onglet revient à la vue simplifiée. Elle fixe un état complet (vue, filtres, acteur
sélectionné, cadrage) et a sa propre adresse, partageable : {", ".join(f'<a href="explorer.html?vue={e(x["id"])}#{e(x["view"])}">{e(x["question"])}</a>' for x in d.get("presets", []))}.
Une question qui porte sur un conflit prend ses acteurs dans les camps du dossier, eux-mêmes lus dans le graphe : elle ne
peut pas contredire les données. <code>validate.py</code> contrôle les vues, acteurs, types et organisations cités.</p>
<p><b>Recherche</b> : un champ en haut de la vue retrouve un pays, un groupe, une organisation ou une question de l'onglet ouvert (sans accents ni majuscules), et met l'élément en avant dans la vue ouverte, sans changer d'onglet. Tout est calculé dans la page, sans serveur.</p>
<p><b>Vue Organisations</b> : chaque pays est placé dans la zone exacte de ses appartenances (cercle privé de ses
intersections), en occupant toute la surface de cette zone (échantillonnage puis relaxation de Lloyd). Une zone trop serrée
réduit ses drapeaux ; au-delà de 24 pays, les plus petits sont regroupés en une pastille « +N ». Zoom et déplacement : les
textes gardent une taille constante, et un nom qui chevaucherait un drapeau n'est affiché qu'au survol.</p>

<h2 id="glossaire">Glossaire</h2>
<p><code>glossaire.yaml</code> donne une seule définition par terme, utilisée partout : infobulles des dossiers et de
l'explorateur, page <a href="glossaire.html">glossaire</a>. Les définitions d'échelles et d'indices décrivent le code qui les
calcule (<code>network.influence()</code>, <code>sources/unga.py</code>). <code>validate.py</code> refuse un terme en double
ou un terme cité dans le code mais absent du glossaire. {len(d.get("glossary", {}))} termes définis.</p>

<h2 id="limites">Limites connues</h2>
<ul>
<li>Le graphe ne couvre que ce qui a été sourcé : l'absence d'une relation ne prouve pas l'absence de soutien.</li>
<li>Les liens formels disent ce qui est signé, pas ce qui est pratiqué ; les votes à l'ONU ont environ un an de retard.</li>
<li>Les sources de presse (France 24, Euronews, NPR…) servent pour les soutiens politiques de personnalités ; le reste
s'appuie autant que possible sur des sources officielles.</li>
<li>Certains sites officiels bloquent la lecture automatique (state.gov, congress.gov) : leurs pages n'ont pas pu être revérifiées.</li>
<li>Les photos sont affichées depuis Wikimedia Commons : si un fichier y est renommé, il disparaît jusqu'au rafraîchissement mensuel.</li>
</ul>

<h2 id="contribuer">Contribuer</h2>
<p>Sans connaître le code : <a href="{style.correction_url("Méthode et sources")}">proposer une correction</a> via un
formulaire guidé (compte GitHub gratuit). Pour les contributeurs : modifier <code>network.yaml</code> ou
<code>alignments.yaml</code>, lancer <code>python validate.py</code>, puis ouvrir une pull request avec les sources. Les données brutes sont réutilisables : <a href="network.json">network.json</a>,
<a href="network.csv">network.csv</a> (CC BY 4.0), profils pays dans le dossier
<a href="{brand.REPO}/tree/main/data">data/</a> du dépôt.</p>
</main></div>{style.foot(page="Méthode et sources")}</body></html>"""

def write(out, data):
    (out / "methode.html").write_text(page(data), encoding="utf-8")
