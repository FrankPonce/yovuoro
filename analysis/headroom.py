"""Sensitivity: what if the radio never fills the GPU (as measured: Weaver <= ~35 %, Nvidia PoC 40 %)?

RAN GPU demand = peak_share * (floor + (1 - floor) * traffic / capacity). peak_share = 1.0 is the
headline (peak traffic fills the GPU); 0.6 and 0.4 follow published measurements.
Run:  uv run --project ../ericsson python analysis/headroom.py
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from yovahti.energy.model import SPLITS
from yovahti.paths import PROCESSED
from yovahti.world.data import load_world

TARGETS = {"mid": ["LTE_1800", "NR_2100"], "nr": ["NR_3500"], "low": ["LTE_700", "LTE_800"]}
full = load_world("all")
lo = int(np.searchsorted(full.times, pd.Timestamp(SPLITS["validation"][0], tz="UTC")))
hi = int(np.searchsorted(full.times, pd.Timestamp(SPLITS["test"][0], tz="UTC")))
vol = sum(full.vol[c] for cs in TARGETS.values() for c in cs)
sites = np.array([s.split("/")[0] for s in full.sectors])
us, sidx = np.unique(sites, return_inverse=True)
oh = np.zeros((full.S, len(us))); oh[np.arange(full.S), sidx] = 1
sv = vol @ oh
cap = np.maximum(np.percentile(sv[:lo], 99.5, axis=0), 1e-6)
real = sv[lo:hi] / cap
iss = np.load(PROCESSED / "forecasts" / "validation_mid.npz")["issues"] - lo
fq = {q: np.einsum("nhs,sk->nhk", sum(np.load(PROCESSED / "forecasts" / f"validation_{t}.npz")[q]
                                      for t in TARGETS), oh) / cap for q in ("q90", "q50")}
rows = []
for ps in (1.0, 0.6, 0.4):
    for q in ("q90", "q50"):
        leased = np.zeros_like(real)
        for k, i in enumerate(iss):
            if 0 <= i and i + 4 <= real.shape[0]:
                dem = ps * (0.2 + 0.8 * np.clip(fq[q][k, :4], 0, None))
                leased[i:i + 4] = np.floor(np.clip(1 - dem.max(0), 0, 1) * 8) / 8
        dr = ps * (0.2 + 0.8 * real)
        ev = (dr + leased > 1) & (leased > 0)
        kept = np.where(ev, 0, leased)
        days = real.shape[0] / 96
        rows.append({"peak_share": ps, "forecast": q.upper().replace("Q", "P"),
                     "gpu_h_per_site_day": float(kept.sum(0).mean() / 4 / days),
                     "eviction_pct": float(100 * ev.sum() / max((leased > 0).sum(), 1))})
out = Path(__file__).resolve().parent.parent / "results" / "headroom.json"
out.write_text(json.dumps(rows, indent=1))
for r in rows:
    print(r)
