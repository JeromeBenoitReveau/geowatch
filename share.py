"""python share.py → assets/partage.png (site) et assets/partage-<dossier>.png : images de partage 1200×630 (og:image).
Produites avec Chrome sans interface, donc à lancer à la main sur un poste qui a Chrome — pas dans la CI ; les PNG sont
versionnés et build.py les copie dans site/. À relancer quand la baseline, le logo ou un titre de dossier change."""
import subprocess, tempfile
from html import escape as e
from pathlib import Path
import brand, dossier, style

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
OUT = Path("assets")
MOTIF = """<svg class="g" width="520" height="630" viewBox="0 0 520 630" fill="none">
 <g stroke-linecap="round">
  <path d="M150 150 L370 235" stroke="#b91c1c" stroke-width="7"/>
  <path d="M150 150 Q120 330 235 440" stroke="#3a6fd8" stroke-width="5"/>
  <path d="M370 235 L235 440" stroke="#1f9aa5" stroke-width="5" stroke-dasharray="16 10"/>
  <path d="M370 235 Q470 370 400 520" stroke="#b08968" stroke-width="7" stroke-dasharray="2 13"/>
  <path d="M235 440 L400 520" stroke="#9ba3b0" stroke-width="3" stroke-dasharray="5 9"/>
 </g>
 <g fill="#1b212b" stroke="#29303b" stroke-width="3">
  <circle cx="150" cy="150" r="40"/><circle cx="370" cy="235" r="48"/><circle cx="235" cy="440" r="36"/><circle cx="400" cy="520" r="30"/>
 </g>
 <g fill="#f4b393"><circle cx="150" cy="150" r="9"/><circle cx="370" cy="235" r="11"/><circle cx="235" cy="440" r="8"/><circle cx="400" cy="520" r="7"/></g>
</svg>"""

def card(title, line, kicker=""):
    """Carte sombre : logo et nom du site, un titre (corps réduit s'il est long), une ligne de précision."""
    size = 76 if len(title) <= 40 else 60
    return f"""<!doctype html><html lang="fr"><head><meta charset="utf-8"><link rel="stylesheet" href="{style.FONTS}">
<style>html,body{{margin:0;width:1200px;height:630px;overflow:hidden}}
body{{background:#141821;color:#e8ebf0;font-family:"Public Sans",system-ui,sans-serif;position:relative}}
.txt{{position:absolute;left:84px;top:0;bottom:0;width:650px;display:flex;flex-direction:column;justify-content:center}}
.brand{{display:flex;align-items:center;gap:20px;font:400 40px/1 "Newsreader",Georgia,serif;margin-bottom:48px}}
.k{{font-size:24px;color:#f4b393;margin:0 0 14px}}
h1{{font:400 {size}px/1.06 "Newsreader",Georgia,serif;letter-spacing:-.01em;margin:0 0 28px}}
p{{font-size:27px;line-height:1.4;color:#9ba3b0;margin:0}}svg.g{{position:absolute;right:0;top:0}}</style></head><body>
{MOTIF}<div class="txt"><div class="brand"><svg viewBox="0 0 205 205" width="64" height="64" fill="none">{style._MARK}</svg>{e(brand.NAME)}</div>
{f'<p class="k">{e(kicker)}</p>' if kicker else ""}<h1>{e(title)}</h1><p>{e(line)}</p></div></body></html>"""

def shoot(html, png):
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(html)
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
                    "--window-size=1200,630", "--virtual-time-budget=6000", f"--screenshot={png.resolve()}", f"file://{f.name}"],
                   check=True, capture_output=True)
    Path(f.name).unlink()
    print("→", png)

if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    shoot(card(brand.BASELINE, "Qui s'oppose à qui, qui soutient qui, et pourquoi."), OUT / "partage.png")
    for x in dossier.load():
        a, b = (s["name"] for s in x["sides"])
        shoot(card(x["title"], f"{a} contre {style.mid(b)} : qui les soutient, et pourquoi.", "Dossier"), OUT / f"partage-{x['id']}.png")
