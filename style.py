"""Feuille de style commune (site/style.css) et gabarit des pages éditoriales : un seul endroit pour les couleurs,
la typographie et l'en-tête. La couleur est réservée aux données (camps, soutiens, tensions) ; l'interface reste
en encre et gris, et l'espace sépare les sections plutôt que des cadres."""
from html import escape as e
import brand

FONTS = ("https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,400;6..72,500"
         "&family=Public+Sans:wght@400;500;600&display=swap")

CSS = """
:root{--paper:#f7f8f7;--ink:#16181d;--graphite:#5f6670;--mist:#e3e6e9;--ocean:#e6ebef;--land:#fdfdfc;
  --peach:#e3936c;--a:#2a78d6;--b:#eb6834;--line:var(--mist);--card:var(--land);--fg:var(--ink);--bg:var(--paper);--mute:var(--graphite);
  --serif:"Newsreader",Georgia,serif;--sans:"Public Sans",system-ui,sans-serif}
/* sombre : gris très légèrement bleutés ; la pêche s'éclaircit pour rester lisible */
@media (prefers-color-scheme:dark){:root{--paper:#141821;--ink:#e8ebf0;--graphite:#9ba3b0;--mist:#29303b;
  --ocean:#0d131b;--land:#1b212b;--peach:#f4b393;--a:#3987e5;--b:#d95926}}
/* la pêche est l'accent de l'interface (liens, onglet actif, survol, focus, logo) ; jamais une couleur de données */
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font:17px/1.6 var(--sans);-webkit-font-smoothing:antialiased}
a{color:inherit;text-decoration-thickness:1.5px;text-underline-offset:3px;text-decoration-color:var(--peach)}
a:hover{text-decoration-thickness:2px}
a:focus-visible,summary:focus-visible,button:focus-visible,input:focus-visible,select:focus-visible{outline:2px solid var(--peach);outline-offset:3px;border-radius:2px}
.wrap{max-width:1080px;margin:0 auto;padding:0 20px}
.top{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;padding:22px 0 0;font-size:15px}
.top a{text-decoration:none}
/* menus déroulants de l'en-tête */
.menus{display:flex;gap:26px}.menu{position:relative}
.menu summary{list-style:none;cursor:pointer;color:var(--graphite);padding:4px 0;border-bottom:2px solid transparent;display:flex;align-items:center;gap:6px}
.menu summary::-webkit-details-marker{display:none}
.menu summary::after{content:"";width:6px;height:6px;border:solid currentColor;border-width:0 1.5px 1.5px 0;transform:translateY(-2px) rotate(45deg);opacity:.7}
.menu[open] summary::after{transform:translateY(1px) rotate(-135deg)}
.menu summary:hover,.menu[open] summary,.menu[data-active] summary{color:var(--ink)}.menu[data-active] summary{border-bottom-color:var(--peach)}
.dd{position:absolute;right:0;top:calc(100% + 10px);z-index:2000;min-width:230px;background:var(--land);border:1px solid var(--mist);
  border-radius:6px;padding:6px;box-shadow:0 8px 24px #0000001a;display:flex;flex-direction:column}
.dd a{display:flex;align-items:center;gap:10px;padding:8px 10px;border-radius:4px;color:var(--ink);white-space:nowrap}
.dd a:hover,.dd a:focus-visible{background:color-mix(in srgb,var(--ink) 6%,var(--land))}.dd a[aria-current]{box-shadow:inset 2px 0 0 var(--peach)}
.dd .ico,.explore .ico{color:var(--peach);flex:none}
.brand{font-family:var(--serif);font-size:20px;display:inline-flex;align-items:center;gap:9px}.brand .logo{flex:none}
h1{font:400 44px/1.1 var(--serif);letter-spacing:-.01em;margin:0 0 14px}
h2{font:400 26px/1.25 var(--serif);margin:0 0 18px}
h3{font:500 19px/1.3 var(--serif);margin:0 0 4px}
.meta,.quiet{color:var(--graphite);font-size:15px}
.lede{font:400 21px/1.5 var(--serif);margin:0;max-width:40em}
.prose{max-width:40em}.prose p{margin:0 0 14px}
section.s{padding:56px 0 0}
/* cartes : bordure fine, pas d'ombre ; encart teinté pour un chiffre ou une donnée mise en avant */
.card{display:block;border:1px solid var(--mist);border-radius:6px;background:var(--land);padding:22px 24px;text-decoration:none}
a.card{transition:border-color .15s}a.card:hover{border-color:var(--peach)}
.tint{background:color-mix(in srgb,var(--ink) 5%,var(--land));border-radius:4px}
sup.fns{font:500 11px/1 var(--sans);color:var(--graphite);margin-left:1px;white-space:nowrap}
sup.fns a{text-decoration:none;padding:0 1px}sup.fns a:hover{color:var(--ink);text-decoration:underline}
abbr{text-decoration:underline dotted var(--graphite);text-underline-offset:3px;cursor:help}
.notes{padding:64px 0 72px;font-size:13.5px;color:var(--graphite)}
.notes h2{font-size:21px;color:var(--ink)}.notes ol{margin:0;padding-left:22px;columns:2;column-gap:48px}
.notes li{break-inside:avoid;margin:0 0 6px}.notes li:target{color:var(--ink)}
footer{border-top:1px solid var(--mist);margin-top:64px;padding:20px 0 40px;font-size:13.5px;color:var(--graphite)}
@media (max-width:760px){h1{font-size:34px}.lede{font-size:19px}.notes ol{columns:1}.menus{gap:18px}}
@media (prefers-reduced-motion:reduce){*{scroll-behavior:auto!important;transition:none!important}}
"""

# Logo « le méridien » : un globe traversé d'une ligne tendue (la géopolitique en cartes, et le fil qui relie)
LOGO = ('<svg class="logo" viewBox="0 0 32 32" width="26" height="26" aria-hidden="true">'
        '<circle cx="16" cy="16" r="11" stroke="currentColor" stroke-width="1.8" fill="none"/>'
        '<path d="M5.5 19C11 12 21 12 26.5 13" stroke="var(--peach)" stroke-width="2.2" fill="none" stroke-linecap="round"/></svg>')
# icône d'onglet : mêmes tracés, couleurs fixes adaptées au thème du navigateur
FAVICON = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
<style>circle{stroke:#16181d}path{stroke:#e3936c}@media (prefers-color-scheme:dark){circle{stroke:#e8ebf0}path{stroke:#f4b393}}</style>
<circle cx="16" cy="16" r="11" stroke-width="2.4" fill="none"/>
<path d="M5.5 19C11 12 21 12 26.5 13" stroke-width="2.8" fill="none" stroke-linecap="round"/></svg>
"""

# Icônes des trois vues de l'explorateur (Lucide, ISC ; « orgs » dessiné pour le site : deux cercles qui se recoupent)
ICONS = {
    "orgs": '<circle cx="9" cy="12" r="6"/><circle cx="15" cy="12" r="6"/>',
    "map": '<circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/>',
    "graph": '<circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" x2="15.42" y1="13.51" y2="17.49"/><line x1="15.41" x2="8.59" y1="6.51" y2="10.49"/>',
}
def icon(k, size=18):
    return (f'<svg class="ico" viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" stroke="currentColor" '
            f'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICONS[k]}</svg>')
# les trois vues de l'explorateur : (ancre, icône, libellé) — mêmes entrées dans le menu, l'explorateur et l'accueil
VIEWS = [("organisations", "orgs", "Organisations"), ("carte", "map", "Carte du monde"), ("graphe", "graph", "Graphe des soutiens")]

def head(title, desc=brand.BASELINE, extra=""):
    return f"""<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link rel="stylesheet" href="{FONTS}">
<link rel="stylesheet" href="style.css"><link rel="icon" href="favicon.svg" type="image/svg+xml">{extra}</head>"""

def top(current=""):
    """En-tête commun : trois menus déroulants (Conflits, Explorer, À propos), identiques sur toutes les pages.
    current = nom du fichier de la page, pour signaler la rubrique et la page actives."""
    import dossier  # import tardif : dossier importe style
    conflicts = [(f"{x['id']}.html", x["title"]) for x in dossier.load()]
    about = [("manifeste.html", "Manifeste"), ("methode.html", "Méthode et sources")]
    here = lambda h: ' aria-current="page"' if h == current else ""
    def menu(label, items, active):
        links = "".join(f'<a href="{h}"{here(h)}>{t}</a>' for h, t in items)
        return f'<details class="menu"{" data-active" if active else ""}><summary>{label}</summary><div class="dd">{links}</div></details>'
    explore = "".join(f'<a href="explorer.html#{a}" data-view="{a}">{icon(k)}{t}</a>' for a, k, t in VIEWS)
    return f"""<div class="top"><a class="brand" href="index.html">{LOGO}{e(brand.NAME)}</a><nav class="menus">
{menu("Conflits", conflicts, current in dict(conflicts))}
<details class="menu"{" data-active" if current == "explorer.html" else ""}><summary>Explorer</summary><div class="dd">{explore}</div></details>
{menu("À propos", about, current in dict(about))}</nav></div>
<script>
// un seul menu ouvert à la fois ; un clic ailleurs ou Échap les ferme
document.addEventListener("click", ev => document.querySelectorAll("details.menu[open]").forEach(d => {{ if(!d.contains(ev.target) || ev.target.closest(".dd a")) d.open = false; }}));
document.addEventListener("keydown", ev => {{ if(ev.key === "Escape") document.querySelectorAll("details.menu[open]").forEach(d => d.open = false); }});
// à l'ouverture : on ferme les autres menus et on garde la liste dans l'écran, quelle que soit sa largeur
document.querySelectorAll("details.menu").forEach(d => d.addEventListener("toggle", () => {{ if(!d.open) return;
  document.querySelectorAll("details.menu[open]").forEach(o => {{ if(o !== d) o.open = false; }});
  const dd = d.querySelector(".dd"); dd.style.left = "auto"; dd.style.right = "0";
  if(dd.getBoundingClientRect().left < 8){{ dd.style.left = "0"; dd.style.right = "auto"; }}
  const r = dd.getBoundingClientRect(); if(r.right > innerWidth - 8) dd.style.left = (innerWidth - 8 - r.width - d.getBoundingClientRect().left) + "px"; }}));
</script>"""

def foot(extra=""):
    return f"""<footer><div class="wrap">{extra}{e(brand.NAME)} est un projet indépendant et open source. Code sous licence MIT,
textes et données sous licence CC BY 4.0. <a href="{brand.REPO}">Proposer une correction</a>.</div></footer>"""

def write(out):
    (out / "style.css").write_text(CSS.strip() + "\n", encoding="utf-8")
    (out / "favicon.svg").write_text(FAVICON, encoding="utf-8")
