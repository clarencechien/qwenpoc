#!/usr/bin/env python3
"""Build the slide deck into one self-contained HTML file and a PDF.

    python3 report/build_slides.py            -> report/slides.html (arrow keys / click to page; images embedded)
                                                 report/slides.pdf  (one 1920x1080 page per slide; needs Node.js + playwright)

Source: report/slides/ = the deck as kept in the Claude Slides artifact (deck.json, deck.css, slides/<id>.html);
images/blob_map.json maps the artifact's uploaded-image ids to the files in images/.
"""
from __future__ import annotations

import base64
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE / "slides"

deck = json.loads((SRC / "deck.json").read_text())
css = (SRC / "deck.css").read_text()
blob = json.loads((SRC / "images" / "blob_map.json").read_text())


def data_uri(name: str) -> str:
    return "data:image/jpeg;base64," + base64.b64encode((SRC / "images" / name).read_bytes()).decode()


uris = {k: data_uri(v) for k, v in blob.items()}
sections = []
for sid in deck["order"]:
    s = (SRC / "slides" / f"{sid}.html").read_text()
    s = re.sub(r"/_blob/([0-9a-f]{32})", lambda m: uris[m.group(1)], s)
    sections.append(s)
fonts = sorted({f["href"] for f in deck["faces"].values() if "href" in f})

VIEWER = """
html,body{margin:0;background:#0d1419;height:100%;overflow:hidden}
#stage{position:absolute;left:50%;top:50%;width:1920px;height:1080px;transform-origin:center center}
#stage>section{position:absolute;inset:0;width:1920px;height:1080px;overflow:hidden;display:none}
#stage>section.on{display:flex}
section aside{display:none}
#hud{position:fixed;right:16px;bottom:12px;font:14px system-ui,sans-serif;color:#9fb0bd}
@media print{
  @page{size:1920px 1080px;margin:0}
  html,body{height:auto;overflow:visible;background:none}
  #stage{position:static;transform:none!important}
  #stage>section{display:flex!important;position:relative;page-break-after:always;break-after:page}
  #hud{display:none}
  *{animation:none!important}
}
"""
JS = """
const S=[...document.querySelectorAll('#stage>section')];let i=0;
function fit(){const k=Math.min(innerWidth/1920,innerHeight/1080);document.getElementById('stage').style.transform=`translate(-50%,-50%) scale(${k})`}
function show(n){i=Math.max(0,Math.min(S.length-1,n));S.forEach((s,j)=>s.classList.toggle('on',j===i));document.getElementById('hud').textContent=`${i+1} / ${S.length}  ← →`;history.replaceState(null,'','#'+(i+1))}
addEventListener('keydown',e=>{if(['ArrowRight','PageDown',' '].includes(e.key))show(i+1);if(['ArrowLeft','PageUp'].includes(e.key))show(i-1);if(e.key==='Home')show(0);if(e.key==='End')show(S.length-1)});
addEventListener('click',e=>show(e.clientX>innerWidth/2?i+1:i-1));addEventListener('resize',fit);
fit();show((parseInt(location.hash.slice(1))||1)-1);
"""
html = ("<!doctype html>\n<html lang=\"zh-Hant\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
        f"<title>{deck['title']}</title>"
        + "".join(f'<link rel="stylesheet" href="{h}">' for h in fonts)
        + f"<style>{css}\n{VIEWER}</style></head><body><div id=\"stage\">\n"
        + "\n".join(sections)
        + f"\n</div><div id=\"hud\"></div><script>{JS}</script></body></html>\n")
out = HERE / "slides.html"
out.write_text(html)
print(f"{out.name}: {len(sections)} slides, {len(html) / 1e6:.2f} MB")

if "--no-pdf" in sys.argv:
    sys.exit(0)
NODE = r"""
const { chromium } = require('playwright');
const [html, pdf, shots] = process.argv.slice(1);  // node -e: argv = [node, ...args]
(async () => {
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  await pg.goto('file://' + html, { waitUntil: 'networkidle' });
  await pg.waitForTimeout(500);
  await pg.pdf({ path: pdf, width: '1920px', height: '1080px', printBackground: true });
  if (shots) {
    await pg.addStyleTag({ content: '*{animation:none!important}' });
    const n = await pg.evaluate(() => S.length);
    for (let k = 0; k < n; k++) {
      await pg.evaluate(k => show(k), k);
      await pg.screenshot({ path: `${shots}/${String(k + 1).padStart(2, '0')}.png` });
    }
  }
  await b.close();
})();
"""
import subprocess  # noqa: E402

shots = ""
if "--shots" in sys.argv:  # one PNG per slide, to check the layout
    shots = str(HERE / "slides_png")
    pathlib.Path(shots).mkdir(exist_ok=True)
r = subprocess.run(["node", "-e", NODE, str(out), str(HERE / "slides.pdf"), shots], capture_output=True, text=True)
if r.returncode:
    sys.exit("PDF step failed (needs Node.js with the playwright package and its Chromium):\n" + r.stderr[-800:])
print("slides.pdf written")
