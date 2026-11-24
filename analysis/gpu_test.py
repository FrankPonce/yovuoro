"""Night Shift GPU lending on the locked test weeks (9-22 Nov 2025), same rules as validation.

Run once, after analysis/fit_test.py:  uv run --project ../ericsson python analysis/gpu_test.py
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from yovahti.energy.model import SPLITS
from yovahti.world.data import load_world

ROOT = Path(__file__).resolve().parent.parent
TARGETS = {"mid": ["LTE_1800", "NR_2100"], "nr": ["NR_3500"], "low": ["LTE_700", "LTE_800"]}

full = load_world("all")
lo = int(np.searchsorted(full.times, pd.Timestamp(SPLITS["validation"][0], tz="UTC")))
a = int(np.searchsorted(full.times, pd.Timestamp(SPLITS["test"][0], tz="UTC")))
vol = sum(full.vol[c] for cs in TARGETS.values() for c in cs)
sites = np.array([s.split("/")[0] for s in full.sectors])
us, sidx = np.unique(sites, return_inverse=True)
oh = np.zeros((full.S, len(us))); oh[np.arange(full.S), sidx] = 1
sv = vol @ oh
cap = np.maximum(np.percentile(sv[:lo], 99.5, axis=0), 1e-6)       # same sizing as validation
real = sv[a:] / cap
fz = {t: np.load(ROOT / "results" / "forecasts" / f"test_{t}.npz") for t in TARGETS}
iss = fz["mid"]["issues"] - a
rows = []
for peak in (1.0, 0.4):
    for q in ("q90", "q50"):
        f = np.einsum("nhs,sk->nhk", sum(fz[t][q][:, :4] for t in TARGETS), oh) / cap
        leased = np.zeros_like(real)
        for k, i in enumerate(iss):
            if 0 <= i and i + 4 <= real.shape[0]:
                d = peak * (0.2 + 0.8 * np.clip(f[k], 0, None))
                leased[i:i + 4] = np.floor(np.clip(1 - d.max(0), 0, 1) * 8) / 8
        dr = peak * (0.2 + 0.8 * real)
        ev = (dr + leased > 1) & (leased > 0)
        kept = np.where(ev, 0, leased)
        days = real.shape[0] / 96
        rows.append({"peak_share": peak, "forecast": q.upper().replace("Q", "P"),
                     "gpu_h_per_site_day": round(float(kept.sum(0).mean() / 4 / days), 2),
                     "eviction_pct": round(float(100 * ev.sum() / max((leased > 0).sum(), 1)), 2)})
(ROOT / "results" / "gpu_test.json").write_text(json.dumps(rows, indent=1))
for r in rows:
    print(r)
