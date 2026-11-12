"""Render the GitHub social preview: assets/banner-social.png and banner-social-dark.png, 1280x640.
Run from the repo root: uvx --from playwright --with pillow python -I assets/source/social.py . assets
Only the wordmark on the left and the orbit on the right: a tagline cannot be read in a chat thumbnail. Keep the wordmark 80 px inside every edge."""
import functools, http.server, sys, threading
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(sys.argv[1]).resolve()
OUT = Path(sys.argv[2]).resolve()

h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT))
h.log_message = lambda *a, **k: None
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h)
threading.Thread(target=srv.serve_forever, daemon=True).start()
port = srv.server_address[1]

SOCIAL = """
const h = document.getElementById('hero'); h.style.width = '1280px'; h.style.height = '640px';
const a = document.getElementById('orbit'); a.setAttribute('viewBox', '130 -46 1024 512'); a.style.width = '1280px';
const w = h.querySelector('.word'); w.style.left = '90px';
w.querySelector('p').remove();
w.querySelector('h1').style.fontSize = '138px';
"""

with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge")
    for theme in ("light", "dark"):
        pg = b.new_page(viewport={"width": 1500, "height": 800})
        pg.goto(f"http://127.0.0.1:{port}/assets/source/readme.html?theme={theme}", wait_until="networkidle")
        pg.evaluate("document.fonts.ready")
        pg.evaluate(SOCIAL)
        pg.wait_for_timeout(300)
        raw = OUT / "_s.png"
        pg.query_selector("#hero").screenshot(path=str(raw), scale="css")
        dst = OUT / ("banner-social.png" if theme == "light" else "banner-social-dark.png")
        Image.open(raw).convert("RGB").resize((1280, 640), Image.LANCZOS).save(dst, optimize=True)
        raw.unlink()
        print(dst.name, round(dst.stat().st_size / 1000), "KB")
        pg.close()
    b.close()
