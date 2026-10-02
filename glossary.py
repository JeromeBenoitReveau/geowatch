"""Glossaire du site (glossaire.yaml) : une seule définition par terme, pour tout le site.
- Glosser : balise la première occurrence de chaque terme dans les textes d'une page (dossiers)
- term()  : balise un terme choisi explicitement (libellés, légendes)
- for_js(): les définitions pour l'explorateur, qui construit ses textes en JavaScript
- write() : la page glossaire.html
Le rendu (souligné pointillé, infobulle au survol ou au focus, clic vers glossaire.html) est commun : style.py."""
import re
from functools import lru_cache
from html import escape as e
from pathlib import Path
import yaml

FILE = Path(__file__).with_name("glossaire.yaml")

@lru_cache(maxsize=1)
def load():
    return yaml.safe_load(FILE.read_text(encoding="utf-8"))["terms"]

def by_id():
    return {t["id"]: t for t in load()}

def definition(t):
    return t["definition"] + (f" Exemple : {t['example']}" if t.get("example") else "")

def link(t, text, new_tab=False):
    """Terme souligné : définition au survol (style.py), clic vers son ancre dans glossaire.html."""
    tab = ' target="_blank" rel="noopener"' if new_tab else ""
    return (f'<a class="term" href="glossaire.html#{e(t["id"])}" data-term="{e(t["term"])}" '
            f'data-def="{e(definition(t))}"{tab}>{text}</a>')

def term(tid, text=None):
    t = by_id()[tid]
    return link(t, e(text if text is not None else t["term"]))

class Glosser:
    """Texte échappé ; la première occurrence de chaque terme de la page est expliquée. Une seule passe : une
    définition n'est jamais re-balisée. Termes « auto: false » (mots trop courants) exclus."""
    def __init__(self):
        self.seen = set()
        forms = {}
        for t in load():
            if t.get("auto", True):
                for f in [t["term"], *t.get("aliases", [])]:
                    forms[f] = t
        self.forms = forms
        terms = sorted(forms, key=len, reverse=True)
        self.by_escaped = {e(f): forms[f] for f in terms}
        self.pattern = re.compile(r"(?<![\w-])(" + "|".join(re.escape(e(f)) for f in terms) + r")(?![\w-])")

    def __call__(self, text):
        h = e(" ".join(str(text).split()))
        def tag(m):
            t = self.by_escaped[m.group()]
            if t["id"] in self.seen:
                return m.group()
            self.seen.add(t["id"])
            return link(t, m.group())
        return self.pattern.sub(tag, h)

def for_js():
    return {t["id"]: {"term": t["term"], "def": definition(t)} for t in load()}

def page():
    import brand, style
    import unicodedata
    # tri alphabétique français : les accents ne comptent pas (« défense » avant « double »)
    plain = lambda s: "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")
    items = sorted(load(), key=lambda t: plain(t["term"]))
    rows = "".join(f"""<div class="gl" id="{e(t['id'])}"><dt>{e(t['term'])}{f' <span class="quiet">({e(", ".join(t["aliases"]))})</span>' if t.get("aliases") else ""}</dt>
<dd>{e(t['definition'])}{f'<br><span class="quiet">Exemple : {e(t["example"])}</span>' if t.get("example") else ""}</dd></div>""" for t in items)
    css = """.page{padding:64px 0 0}.gl{padding:14px 0;border-bottom:1px solid var(--mist);scroll-margin-top:20px}
.gl dt{font:500 19px/1.3 var(--serif);margin:0 0 4px}.gl dd{margin:0;max-width:44em}.gl:target{background:color-mix(in srgb,var(--peach) 14%,transparent)}
dl{margin:28px 0 0}"""
    body = f"""<article class="page"><h1>Glossaire</h1>
<p class="lede">Les mots de la géopolitique et ceux du site, expliqués simplement. Partout sur le site, un mot souligné en
pointillés renvoie ici ; survolez-le pour lire sa définition.</p>
<p class="meta">Les échelles et les indices (niveau d'alignement, indice de vote à l'ONU) sont détaillés dans la
<a href="methode.html">méthode</a>.</p>
<dl>{rows}</dl></article>"""
    return (style.head(f"Glossaire — {brand.NAME}", "Alliance, sanctions, cessez-le-feu, levier… Les mots de la géopolitique et du site, chacun défini en une phrase avec un exemple.", f"<style>{css}</style>", path="glossaire.html")
            + f'<body><div class="wrap">{style.top("glossaire.html")}{body}</div>{style.foot(page="Glossaire")}</body></html>')

def write(out):
    (out / "glossaire.html").write_text(page(), encoding="utf-8")
