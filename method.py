"""Page « Méthode & sources » (site/methode.html), générée à chaque build à partir des mêmes données
que le site : chiffres, versions et dates ne peuvent pas dériver de ce qui est affiché."""
from collections import Counter
from html import escape as e
from urllib.parse import urlparse
import re
import history
from config import DYADS, MOVE_ALERT_PTS
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
    odds = history._read("odds.csv")
    readings = sorted({r["fetched_at"] for r in odds})
    n_markets = len(history._read("markets.csv"))
    prof_dates = sorted(p["fetched_at"] for p in d["profiles"].values() if p.get("fetched_at"))
    roles = Counter(v["role"] for k, v in d["influence"].items() if k in actors)
    src = unga.get("source", {})
    formal = [g for g in al["groups"] if g.get("kind") != "forum"]
    forums = [g for g in al["groups"] if g.get("kind") == "forum"]
    blocs = al["blocs"]
    drift = unga.get("drift") or []

    def group_rows(gs):
        return "".join(
            f"<tr><td>{e(g['name'])}</td><td>{e(blocs[g['bloc']]['name']) if g.get('bloc') else 'forum'}</td>"
            f"<td>{g['level'] if g.get('kind') != 'forum' else '—'}</td><td>{len(g['members'])}</td>"
            f"<td>{'<br>'.join(_src(s) for s in g['sources'])}</td></tr>" for g in gs)

    kind_fr = {"state": ("État", "États"), "bloc": ("bloc", "blocs"),
               "non_state": ("groupe armé non étatique", "groupes armés non étatiques"),
               "party": ("parti", "partis"), "person": ("personnalité", "personnalités")}
    role_fr = {"member": ("membre", "membres"), "satellite": ("satellite", "satellites"),
               "contested": ("disputé", "disputés"), "none": ("non classé", "non classés")}
    fr = lambda table, k, n: table.get(k, (k, k))[n > 1]
    return f"""<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>geowatch — méthode et sources</title>
<style>
:root{{--bg:#fafaf8;--fg:#1c1c1c;--mute:#6b6b6b;--line:#e3e3df;--card:#fff;--accent:#2b6cb0}}
@media (prefers-color-scheme:dark){{:root{{--bg:#141414;--fg:#eee;--mute:#9a9a9a;--line:#2c2c2c;--card:#1d1d1d;--accent:#7aa7e0}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--fg);font:15px/1.6 system-ui,sans-serif}}
main{{max-width:860px;margin:0 auto;padding:24px 16px 64px}}
h1{{font-size:26px;margin:8px 0 4px}}h2{{font-size:19px;margin:36px 0 8px;padding-top:8px;border-top:1px solid var(--line)}}
h3{{font-size:15px;margin:20px 0 6px}}a{{color:var(--accent)}}.mute{{color:var(--mute);font-size:13px}}
table{{width:100%;border-collapse:collapse;font-size:13px;margin:8px 0}}th,td{{text-align:left;padding:6px 8px;border-bottom:1px solid var(--line);vertical-align:top}}
th{{color:var(--mute);font-weight:600}}.wrap{{overflow-x:auto}}code{{font-size:13px;background:var(--card);padding:1px 4px;border-radius:4px}}
.flow{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:8px;margin:12px 0}}
.flow div{{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:10px;font-size:13px}}
.flow b{{display:block;margin-bottom:4px}}nav a{{margin-right:12px;white-space:nowrap}}
.kpi{{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:8px;margin:12px 0}}
.kpi div{{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:10px}}.kpi b{{display:block;font-size:22px}}
</style></head><body><main>
<p><a href="index.html">← Retour à la carte et au graphe</a></p>
<h1>Méthode et sources</h1>
<p class="mute">Page générée automatiquement le {_date(d["built"])} à partir des données publiées. Code sous licence MIT,
données du graphe sous CC BY 4.0 — <a href="https://github.com/JeromeBenoitReveau/geowatch">dépôt GitHub</a>.</p>
<nav class="mute"><a href="#principe">Principe</a><a href="#chaine">Chaîne de données</a><a href="#graphe">Graphe</a>
<a href="#blocs">Blocs</a><a href="#onu">Votes ONU</a><a href="#taille">Taille</a><a href="#marches">Marchés</a>
<a href="#profils">Profils</a><a href="#carte">Carte</a><a href="#limites">Limites</a><a href="#contribuer">Contribuer</a></nav>

<div class="kpi">
  <div><b>{len(actors)}</b><span class="mute">acteurs</span></div>
  <div><b>{len(edges)}</b><span class="mute">relations de soutien</span></div>
  <div><b>{len(urls)}</b><span class="mute">sources citées ({len(domains)} sites)</span></div>
  <div><b>{len(d["geo"])}</b><span class="mute">pays sur la carte</span></div>
  <div><b>{len(unga.get("countries", {}))}</b><span class="mute">pays avec votes ONU</span></div>
  <div><b>{n_markets}</b><span class="mute">marchés suivis</span></div>
</div>

<h2 id="principe">Principe</h2>
<p>geowatch montre <b>qui soutient qui</b> dans les conflits en cours, sous forme d'un graphe dont chaque relation est
sourcée, datée et relue à la main, et le relie à ce qui se mesure : liens formels entre États, votes à l'ONU,
dépenses militaires, cotes des marchés de prédiction.</p>
<p><b>Règle non négociable : aucun pourcentage sans cote de marché réelle derrière.</b> geowatch ne calcule ni n'estime
aucune probabilité. Les seuls pourcentages de probabilité affichés sont des prix de marchés (Polymarket, Kalshi), avec leur
source. Les autres pourcentages sont des mesures (part des votes identiques à l'ONU, part du PIB…).</p>
<p>Deux règles de conception : rien n'est pondéré à la main (tailles, couleurs et classements découlent de données
publiées ou de règles écrites ici) ; rien n'entre dans le graphe sans source et sans relecture humaine.</p>

<h2 id="chaine">Chaîne de données</h2>
<div class="flow">
  <div><b>1. Curation</b><code>network.yaml</code> (relations de soutien) et <code>alignments.yaml</code> (traités, adhésions,
  forums), édités à la main, contrôlés par <code>validate.py</code> à chaque changement.</div>
  <div><b>2. Collecte automatique</b>GitHub Actions : cotes des marchés toutes les 6 h ; profils pays, coordonnées, photos
  et votes ONU le 1er du mois.</div>
  <div><b>3. Stockage ouvert</b>Tout est versionné dans le dépôt, dossier <code>data/</code> : CSV et JSON lisibles,
  historique complet dans git.</div>
  <div><b>4. Calculs</b><code>network.influence()</code> (blocs), <code>sources/unga.py</code> (votes),
  <code>track.py</code> (variations de cotes) — règles détaillées ci-dessous.</div>
  <div><b>5. Publication</b><code>build.py</code> génère ce site statique et les exports
  <a href="network.json">network.json</a> / <a href="network.csv">network.csv</a> ; GitHub Pages le publie.</div>
</div>
<div class="wrap"><table>
<tr><th>Source</th><th>Ce qu'on en tire</th><th>Fréquence</th><th>Dernière mise à jour</th><th>Licence</th></tr>
<tr><td>Relecture humaine, {len(domains)} sites cités (ONU, Trésor américain, Conseil de l'UE, SIPRI, Kremlin, presse…)</td>
  <td>Relations de soutien</td><td>à la main</td><td>vérifications de {min((x["verified"] for x in edges), default="n/d")} à {max((x["verified"] for x in edges), default="n/d")}</td><td>CC BY 4.0 (notre travail)</td></tr>
<tr><td><a href="https://polymarket.com">Polymarket</a>, <a href="https://kalshi.com">Kalshi</a></td><td>Cotes des marchés de prédiction</td>
  <td>6 h</td><td>{_date(readings[-1] if readings else None)} ({len(readings)} relevés)</td><td>données publiques des API</td></tr>
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
<li><b>sources</b> : au moins une, avec URL ouverte et relue ; <b>verified</b> : mois de la dernière vérification
(signalée au-delà de 6 mois).</li>
</ul>
<p>Sites les plus cités : {", ".join(f"{e(dom)} ({n})" for dom, n in domains.most_common(8))}.</p>
<p><code>validate.py</code> refuse une relation sans source, avec un acteur inconnu ou une valeur hors liste, et tourne sur
GitHub à chaque modification. <code>update_network.py</code> peut proposer des mises à jour (Claude + recherche web) dans un
fichier séparé : rien n'entre dans le graphe sans relecture.</p>
<p>Partis et personnalités forment un calque « détail » : ils sont rattachés à leur pays et ne sont jamais classés dans un bloc.</p>

<h2 id="blocs">Blocs d'influence</h2>
<p>Deux blocs : {" et ".join(f'<b style="color:{b["color"]}">{e(b["name"])}</b>' for b in blocs.values())}.
Seuls les <b>liens formels</b> (traités, adhésions) sont déclarés, avec un niveau :</p>
<ul><li><b>3</b> défense mutuelle · <b>2</b> partenariat stratégique sans défense mutuelle · <b>1</b> candidature ou
participation gelée · <b>0</b> intégration sans effet sur l'alignement (zone euro, Schengen).</li></ul>
<div class="wrap"><table><tr><th>Groupe</th><th>Bloc</th><th>Niveau</th><th>Pays</th><th>Sources</th></tr>{group_rows(formal)}</table></div>
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
affichés (sélecteur « Organisation » de la carte, fiches pays) mais <b>n'entrent pas dans le calcul des blocs</b>.</p>
<div class="wrap"><table><tr><th>Forum</th><th></th><th></th><th>Pays</th><th>Sources</th></tr>{group_rows(forums)}</table></div>

<h2 id="onu">Votes à l'Assemblée générale de l'ONU</h2>
<p>Source : {e(src.get("name", ""))}, version {e(src.get("version", "n/d"))} — {e(src.get("cite", ""))}.</p>
<p><b>Placement des pays</b> ({unga.get("agreement_year", "n/d")}, dernière année disponible pour les taux d'accord) :
pour chaque pays, part des votes enregistrés identiques à ceux de la France et de l'Allemagne (moyenne des deux), et à ceux
de la Russie et de la Chine. <code>penchant = accord(France, Allemagne) − accord(Russie, Chine)</code>, entre −1 et +1.
Un pays de référence n'est comparé qu'à l'autre membre de son groupe.</p>
<p><b>Dérive transatlantique</b> : écart entre les États-Unis et la moyenne France/Allemagne sur l'« axe idéal » de Voeten,
jusqu'à {drift[-1]["year"] if drift else "n/d"} ({" → ".join(f'{x["us_gap"]} en {x["year"]}' for x in drift[-2:])} ;
France ↔ Allemagne : {drift[-1]["fr_de_gap"] if drift else "n/d"}). Cet axe unique mesure bien l'écart entre deux pays, mais
il ne sert pas à placer un pays entre deux blocs : en 2025, des votes communs États-Unis/Russie y font artificiellement
« remonter » la Russie vers l'Occident.</p>
<p><b>À lire avec prudence</b> : voter ensemble à l'ONU est un alignement diplomatique, pas militaire. Beaucoup de votes du
Sud global (développement, décolonisation) coïncident avec ceux de la Chine : pencher vers Russie/Chine n'est pas appartenir
à l'axe. Les votes adoptés par consensus, sans scrutin, ne sont pas comptés.</p>

<h2 id="taille">Taille des acteurs</h2>
<p>Au choix : dépenses militaires en dollars (Banque mondiale <code>MS.MIL.XPND.CD</code>), PIB en dollars
(<code>NY.GDP.MKTP.CD</code>), ou nombre de soutiens accordés dans le graphe. Échelle en racine carrée ; l'UE utilise l'agrégat
Banque mondiale « EUU ». Sans donnée (Taïwan, que la Banque mondiale ne couvre pas ; groupes armés) : taille minimale.</p>

<h2 id="marches">Marchés de prédiction</h2>
<p>{len(DYADS)} paires suivies ({", ".join(e(k) for k in DYADS)}). Un marché est retenu si tous les mots-clés de la paire
apparaissent dans son titre. Polymarket : recherche publique ; Kalshi : événements ouverts des catégories World et Politics.
Chaque relevé est ajouté à <code>data/odds.csv</code> ; la variation affichée compare la cote actuelle au dernier relevé
d'il y a 7 jours, signalée au-delà de {MOVE_ALERT_PTS} points. Le prix d'un marché reflète les paris de ses participants,
pas une probabilité objective.</p>

<h2 id="profils">Profils pays</h2>
<p>Banque mondiale (dernière année disponible, souvent avec 1 à 2 ans de retard) : {", ".join(f"<code>{c}</code>" for c in INDICATORS.values())}.
Wikidata : forme de gouvernement (P122), chef d'État (P35), coordonnées (P625), codes ISO (P297, P298, P299).
La « forme de gouvernement » Wikidata est la forme officielle, pas le fonctionnement réel.</p>

<h2 id="carte">Carte</h2>
<p>Contours Natural Earth (domaine public), sans serveur de tuiles. Chaque acteur est placé dans son pays d'ancrage
(coordonnées Wikidata) ; plusieurs acteurs d'un même pays sont disposés en couronne. Un groupe armé reste dans son pays
d'origine même s'il agit ailleurs. Seule l'UE a une position fixée à la main (Bruxelles).</p>

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
<p>Modifier <code>network.yaml</code> ou <code>alignments.yaml</code>, lancer <code>python validate.py</code>, puis ouvrir une
pull request avec les sources. Les données brutes sont réutilisables : <a href="network.json">network.json</a>,
<a href="network.csv">network.csv</a> (CC BY 4.0), historique des cotes et profils dans le dossier
<a href="https://github.com/JeromeBenoitReveau/geowatch/tree/main/data">data/</a> du dépôt.</p>
</main></body></html>"""

def write(out, data):
    (out / "methode.html").write_text(page(data), encoding="utf-8")
