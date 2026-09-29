"""Feuille de style commune (site/style.css) et gabarit des pages éditoriales : un seul endroit pour les couleurs,
la typographie et l'en-tête. La couleur est réservée aux données (camps, soutiens, tensions) ; l'interface reste
en encre et gris, et l'espace sépare les sections plutôt que des cadres."""
from html import escape as e
import brand

FONTS = ("https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,400;6..72,500"
         "&family=Public+Sans:wght@400;500;600&display=swap")

CSS = """
:root{--paper:#f7f8f7;--ink:#16181d;--graphite:#5f6670;--mist:#e3e6e9;--ocean:#e6ebef;--land:#fdfdfc;
  --a:#2a78d6;--b:#eb6834;--line:var(--mist);--card:var(--land);--fg:var(--ink);--bg:var(--paper);--mute:var(--graphite);
  --serif:"Newsreader",Georgia,serif;--sans:"Public Sans",system-ui,sans-serif}
@media (prefers-color-scheme:dark){:root{--paper:#15171a;--ink:#e8eaed;--graphite:#9aa1ab;--mist:#2a2e34;
  --ocean:#0f1316;--land:#1e2226;--a:#3987e5;--b:#d95926}}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font:17px/1.6 var(--sans);-webkit-font-smoothing:antialiased}
a{color:inherit;text-decoration-thickness:1px;text-underline-offset:3px}
a:focus-visible,summary:focus-visible,button:focus-visible,input:focus-visible,select:focus-visible{outline:2px solid var(--ink);outline-offset:3px;border-radius:2px}
.wrap{max-width:1080px;margin:0 auto;padding:0 20px}
.top{display:flex;justify-content:space-between;align-items:baseline;gap:12px;flex-wrap:wrap;padding:22px 0 0;font-size:15px}
.top a{text-decoration:none}.top nav a{margin-left:22px;color:var(--graphite)}.top nav a:hover,.top nav a[aria-current]{color:var(--ink)}
.brand{font-family:var(--serif);font-size:20px}
h1{font:400 44px/1.1 var(--serif);letter-spacing:-.01em;margin:0 0 14px}
h2{font:400 26px/1.25 var(--serif);margin:0 0 18px}
h3{font:500 19px/1.3 var(--serif);margin:0 0 4px}
.meta,.quiet{color:var(--graphite);font-size:15px}
.lede{font:400 21px/1.5 var(--serif);margin:0;max-width:40em}
.prose{max-width:40em}.prose p{margin:0 0 14px}
section.s{padding:56px 0 0}
/* cartes : bordure fine, pas d'ombre ; encart teinté pour un chiffre ou une donnée mise en avant */
.card{display:block;border:1px solid var(--mist);border-radius:6px;background:var(--land);padding:22px 24px;text-decoration:none}
a.card{transition:border-color .15s}a.card:hover{border-color:var(--ink)}
.tint{background:color-mix(in srgb,var(--ink) 5%,var(--land));border-radius:4px}
sup.fns{font:500 11px/1 var(--sans);color:var(--graphite);margin-left:1px;white-space:nowrap}
sup.fns a{text-decoration:none;padding:0 1px}sup.fns a:hover{color:var(--ink);text-decoration:underline}
abbr{text-decoration:underline dotted var(--graphite);text-underline-offset:3px;cursor:help}
.notes{padding:64px 0 72px;font-size:13.5px;color:var(--graphite)}
.notes h2{font-size:21px;color:var(--ink)}.notes ol{margin:0;padding-left:22px;columns:2;column-gap:48px}
.notes li{break-inside:avoid;margin:0 0 6px}.notes li:target{color:var(--ink)}
footer{border-top:1px solid var(--mist);margin-top:64px;padding:20px 0 40px;font-size:13.5px;color:var(--graphite)}
@media (max-width:760px){h1{font-size:34px}.lede{font-size:19px}.notes ol{columns:1}.top nav a{margin:0 16px 0 0}}
@media (prefers-reduced-motion:reduce){*{scroll-behavior:auto!important;transition:none!important}}
"""

NAV = [("index.html#conflits", "Conflits"), ("explorer.html", "Explorer"), ("manifeste.html", "Manifeste"), ("methode.html", "Méthode")]

def head(title, desc=brand.BASELINE, extra=""):
    return f"""<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link rel="stylesheet" href="{FONTS}">
<link rel="stylesheet" href="style.css">{extra}</head>"""

def top(current=""):
    links = "".join(f'<a href="{h}"{" aria-current=\"page\"" if h.split("#")[0] == current else ""}>{t}</a>' for h, t in NAV)
    return f'<div class="top"><a class="brand" href="index.html">{e(brand.NAME)}</a><nav>{links}</nav></div>'

def foot(extra=""):
    return f"""<footer><div class="wrap">{extra}{e(brand.NAME)} est un projet indépendant et open source. Code sous licence MIT,
textes et données sous licence CC BY 4.0. <a href="{brand.REPO}">Proposer une correction</a>.</div></footer>"""

def write(out):
    (out / "style.css").write_text(CSS.strip() + "\n", encoding="utf-8")
