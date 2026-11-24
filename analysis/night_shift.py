"""Night Shift: how much AI-RAN GPU can be lent out, with the radio always first?

Uses Yövahti's real-data world (Slovak live-RAN counters) and its calibrated P10/P50/P90
forecasts for the validation weeks (26 Oct - 8 Nov 2025). Nothing here is fitted on that window.

Model (assumptions, all stated in the output):
- One GPU per site (AirScale plug-in card / ARC-Pro), shared by all of the site's sectors.
- RAN GPU demand = FLOOR + (1 - FLOOR) * site traffic / site capacity, where capacity is the
  site's 99.5th-percentile traffic on the training weeks (the GPU is sized for the busy hour).
  Layer-1 compute tracks PRB load (Weaver, AITRAS); FLOOR covers always-on processing.
- Every hour the planner leases whole 1/8 GPU slices for the next hour, using the forecast
  issued at that hour: lease = floor((1 - max demand at Pq - reserve) * 8) / 8.
- Reality check per quarter-hour: if real RAN demand + leased share > 1, the watchdog evicts
  the tenant for that quarter-hour (the radio wins). We count evicted slice-time.

Run:  uv run --project ../ericsson python analysis/night_shift.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

from yovahti.energy.model import SPLITS
from yovahti.paths import PROCESSED
from yovahti.world.data import load_world, time_slice

OUT = Path(__file__).resolve().parent.parent / "results"
TARGETS = {"mid": ["LTE_1800", "NR_2100"], "nr": ["NR_3500"], "low": ["LTE_700", "LTE_800"]}
SLICES = 8
H = 4  # lease for one hour = 4 quarter-hours, re-decided every hour


def main() -> None:
    t0 = time.time()
    full = load_world("all")
    lo = int(np.searchsorted(full.times, pd.Timestamp(SPLITS["validation"][0], tz="UTC")))
    hi = int(np.searchsorted(full.times, pd.Timestamp(SPLITS["test"][0], tz="UTC")))
    vol = sum(full.vol[c] for cs in TARGETS.values() for c in cs)          # [T,S] MB / QH
    sites = np.array([s.split("/")[0] for s in full.sectors])
    usites, sidx = np.unique(sites, return_inverse=True)
    n_sites = len(usites)
    onehot = np.zeros((full.S, n_sites))
    onehot[np.arange(full.S), sidx] = 1.0
    site_vol = vol @ onehot                                                # [T,N]
    cap = np.percentile(site_vol[:lo], 99.5, axis=0)                       # train weeks only
    cap = np.maximum(cap, 1e-6)
    real = site_vol[lo:hi] / cap                                           # [Tv,N]
    times = full.times[lo:hi].tz_convert("Europe/Bratislava")
    print(f"world ready {time.time() - t0:.0f}s: {full.S} sectors, {n_sites} sites, "
          f"{hi - lo} quarter-hours", file=sys.stderr)

    fc = {}
    for t in TARGETS:
        z = np.load(PROCESSED / "forecasts" / f"validation_{t}.npz")
        fc[t] = z
    issues = fc["mid"]["issues"] - lo                                      # world-relative
    def site_fc(q):  # [n_issues, 40, N] site traffic forecast at quantile q (sum of sectors)
        tot = sum(fc[t][q] for t in TARGETS)                               # [n,40,S]
        return np.einsum("nhs,sk->nhk", tot, onehot) / cap

    fq = {"P90": site_fc("q90"), "P50": site_fc("q50")}

    def run(q: str, floor: float, reserve: float) -> dict:
        f = fq[q]
        leased = np.zeros_like(real)
        for k, i in enumerate(issues):
            if i < 0 or i + H > real.shape[0]:
                continue
            dem = floor + (1 - floor) * np.clip(f[k, :H], 0, None)          # [H,N]
            free = 1.0 - dem.max(axis=0) - reserve
            share = np.floor(np.clip(free, 0, 1) * SLICES) / SLICES
            leased[i:i + H] = share
        dem_real = floor + (1 - floor) * real
        evicted = (dem_real + leased > 1.0) & (leased > 0)
        kept = np.where(evicted, 0.0, leased)
        days = real.shape[0] / 96
        night = np.asarray((times.hour >= 22) | (times.hour < 6))
        gpu_h = kept.sum(axis=0) / 4                                       # GPU-hours per site
        return {
            "forecast": q, "floor": floor, "reserve": reserve,
            "gpu_hours_per_site_day": float(gpu_h.mean() / days),
            "night_gpu_hours_per_site_night": float(kept[night].sum(axis=0).mean() / 4 / days),
            "mean_lent_share": float(kept.mean()),
            "night_lent_share": float(kept[night].mean()),
            "eviction_rate_pct": float(100 * evicted.sum() / max((leased > 0).sum(), 1)),
            "evicted_gpu_hours_per_site_day": float((leased * evicted).sum(axis=0).mean() / 4 / days),
            "ran_only_utilisation_pct": float(100 * np.clip(dem_real, 0, 1).mean()),
            "with_tenants_utilisation_pct": float(100 * np.clip(dem_real + kept, 0, 1).mean()),
        }

    rows = []
    for floor in (0.1, 0.2, 0.3):
        for reserve in (0.0, 0.125, 0.25):
            rows.append(run("P90", floor, reserve))
        rows.append(run("P50", floor, 0.0))
    # Hour-of-day profile at the headline setting
    head = dict(q="P90", floor=0.2, reserve=0.0)
    f = fq["P90"]
    prof = {}
    leased = np.zeros_like(real)
    for k, i in enumerate(issues):
        if 0 <= i and i + H <= real.shape[0]:
            dem = 0.2 + 0.8 * np.clip(f[k, :H], 0, None)
            leased[i:i + H] = np.floor(np.clip(1 - dem.max(0) - head["reserve"], 0, 1) * SLICES) / SLICES
    for h in range(24):
        m = np.asarray(times.hour == h)
        prof[h] = {"ran_demand_pct": float(100 * (0.2 + 0.8 * real[m]).clip(0, 1).mean()),
                   "lent_pct": float(100 * leased[m].mean())}

    out = {"assumptions": {
        "sites": n_sites, "sectors": full.S, "window": "validation 26 Oct - 8 Nov 2025",
        "gpu": "one per site, sized for the site's 99.5th-pct training-week traffic",
        "demand": "floor + (1-floor) * traffic/capacity", "slices": SLICES,
        "lease": "hourly, from the forecast issued that hour", "headline": head},
        "rows": rows, "hour_profile": prof}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "night_shift.json").write_text(json.dumps(out, indent=1))
    df = pd.DataFrame(rows)
    with pd.option_context("display.width", 200, "display.max_columns", 20):
        print(df.round(2).to_string(index=False))
    print("\nhour  RAN%  lent%")
    for h, v in prof.items():
        print(f"{h:4d} {v['ran_demand_pct']:5.1f} {v['lent_pct']:5.1f}")


if __name__ == "__main__":
    main()
