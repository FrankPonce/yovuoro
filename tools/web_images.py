"""Turn the Blender renders (web/img/*.png, git-ignored) into trimmed web WebPs.

Run: uv run --with pillow python tools/web_images.py
- Day/night pairs share one crop box so they line up exactly when cross-faded.
- The shadow catcher also records a little bounced light: light, semi-transparent pixels show
  as a pale rectangle on a coloured background. Those are dropped; real (dark) shadows stay.
"""

from pathlib import Path

from PIL import Image

IMG = Path(__file__).resolve().parents[1] / "site" / "img" / "src"
GROUPS = [["site_on", "site_off", "site_on_night", "site_lend_night"], ["bb_radio", "bb_lent_night"]]


def clean(im: Image.Image) -> Image.Image:
    px = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if 0 < a < 235 and (0.299 * r + 0.587 * g + 0.114 * b) > 150:
                px[x, y] = (r, g, b, 0)
    return im


def bbox(im: Image.Image):
    return im.getchannel("A").point(lambda a: 255 if a > 8 else 0).getbbox()


for group in GROUPS:
    ims = {n: clean(Image.open(IMG / f"{n}.png").convert("RGBA")) for n in group
           if (IMG / f"{n}.png").exists()}
    boxes = [bbox(im) for im in ims.values()]
    bb = (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes),
          max(b[3] for b in boxes))
    for n, im in ims.items():
        pad = 12
        box = (max(0, bb[0] - pad), max(0, bb[1] - pad), min(im.width, bb[2] + pad),
               min(im.height, bb[3] + pad))
        c = im.crop(box)
        s = min(1.0, 1000 / max(c.size))
        c = c.resize((round(c.width * s), round(c.height * s)), Image.LANCZOS)
        c.save(IMG.parent / f"{n}.webp", "WEBP", quality=88, method=6)
        print(n, c.size)
