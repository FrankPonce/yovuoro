"""Backup PDF of the pitch site: one page per scene, at its last step.

Needs the site served on :8779 (launch config "site") and Microsoft Edge.
Run:  uv run --no-project --with pillow python tools/export_pdf.py
"""

import re
import subprocess
import tempfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
URL = "http://localhost:8779/site/index.html"
OUT = ROOT / "Yovuoro_pitch.pdf"

html = (ROOT / "site" / "index.html").read_text(encoding="utf-8")
scenes = [(m.group(1), int(m.group(3))) for m in
          re.finditer(r'<section class="[^"]*" id="([^"]+)"( data-skip)? data-steps="(\d+)"', html)
          if not m.group(2)]
pages = []
with tempfile.TemporaryDirectory() as tmp:
    for sid, n in scenes:
        png = Path(tmp) / f"{sid}.png"
        subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                        "--window-size=1600,900", "--virtual-time-budget=6000",
                        f"--screenshot={png}", f"{URL}?at={sid}:{n - 1}"],
                       check=True, capture_output=True, timeout=120)
        pages.append(Image.open(png).convert("RGB"))
        print(sid, pages[-1].size)
    pages[0].save(OUT, save_all=True, append_images=pages[1:], resolution=150)
    # contact sheet for a quick visual check
    cols, w, h = 3, 640, 360
    sheet = Image.new("RGB", (cols * w, -(-len(pages) // cols) * h), "white")
    for k, im in enumerate(pages):
        sheet.paste(im.resize((w, h)), ((k % cols) * w, (k // cols) * h))
    sheet.save(ROOT / "results" / "pitch_contact_sheet.png")
print("wrote", OUT, len(pages), "pages")
