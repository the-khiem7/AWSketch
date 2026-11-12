"""Render the slowly swaying banner as GIF, the README banner (1200x420), light and dark.
Run from the repo root: uvx --from playwright --with pillow python -I assets/source/spin.py . assets
The rings sway +-AMP degrees on a sine, so the loop is seamless with few frames."""
import functools, http.server, math, sys, threading
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(sys.argv[1]).resolve()
OUT = Path(sys.argv[2]).resolve()
FRAMES, FPS, AMP = 90, 10, 30  # 9 s per loop, peak speed about 21 deg/s

h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT))
h.log_message = lambda *a, **k: None
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h)
threading.Thread(target=srv.serve_forever, daemon=True).start()
port = srv.server_address[1]

def save(frames, path, size, colors):
    pal = frames[0].resize(size, Image.LANCZOS).convert("P", palette=Image.ADAPTIVE, colors=colors)
    out = [f.resize(size, Image.LANCZOS).quantize(palette=pal, dither=Image.NONE) for f in frames]
    out[0].save(path, save_all=True, append_images=out[1:], duration=1000 // FPS, loop=0, optimize=True, disposal=1)
    print(path, round(Path(path).stat().st_size / 1e6, 2), "MB")

with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge")
    for theme in ("light", "dark"):
        sfx = "" if theme == "light" else "-dark"
        pg = b.new_page(viewport={"width": 1500, "height": 800})
        pg.goto(f"http://127.0.0.1:{port}/assets/source/readme.html?theme={theme}", wait_until="networkidle")
        pg.evaluate("document.fonts.ready")
        el = pg.query_selector("#banner")
        raws = []
        for i in range(FRAMES):
            pg.evaluate(f"drawHero({AMP * math.sin(2 * math.pi * i / FRAMES)})")
            pg.wait_for_timeout(150 if i == 0 else 40)
            f = OUT / "_f.png"
            el.screenshot(path=str(f), scale="css")
            raws.append(Image.open(f).convert("RGB").copy())
        f.unlink()
        save(raws, OUT / f"banner{sfx}.gif", (1200, 420), 128)
        pg.close()
    b.close()
