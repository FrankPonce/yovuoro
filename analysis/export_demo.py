"""Export real per-site data for the pitch site's live console and site map.

For every site, quarter-hour by quarter-hour over one window: the radio's real GPU demand, the
P90 plan, the slices lent (hourly, 1/8 slices) and evictions, using exactly the Night Shift rules
(floor 20 %, no extra reserve). Also per-site traffic and lendable GPU-hours for the map scene.

Run:  uv run --project ../ericsson python analysis/export_demo.py [validation|test]
Writes site/data/demo.json and site/data/sites.json.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from yovahti.energy.model import SPLITS
from yovahti.paths import PROCESSED
from yovahti.world.data import load_world

ROOT = Path(__file__).resolve().parent.parent
TARGETS = {"mid": ["LTE_1800", "NR_2100"], "nr": ["NR_3500"], "low": ["LTE_700", "LTE_800"]}
FLOOR, SLICES, H = 0.2, 8, 4


def main(window: str = "validation") -> None:
    full = load_world("all")
    lo = int(np.searchsorted(full.times, pd.Timestamp(SPLITS["validation"][0], tz="UTC")))
    if window == "validation":
        a, b = lo, int(np.searchsorted(full.times, pd.Timestamp(SPLITS["test"][0], tz="UTC")))
        fdir, pre = PROCESSED / "forecasts", "validation_"
    else:
        a, b = int(np.searchsorted(full.times, pd.Timestamp(SPLITS["test"][0], tz="UTC"))), full.T
        fdir, pre = ROOT / "results" / "forecasts", "test_"
    vol = sum(full.vol[c] for cs in TARGETS.values() for c in cs)
    sites = np.array([s.split("/")[0] for s in full.sectors])
    us, sidx = np.unique(sites, return_inverse=True)
    oh = np.zeros((full.S, len(us)))
    oh[np.arange(full.S), sidx] = 1
    sv = vol @ oh
    cap = np.maximum(np.percentile(sv[:lo], 99.5, axis=0), 1e-6)   # sized on training weeks only
    real = sv[a:b] / cap
    times = full.times[a:b].tz_convert("Europe/Bratislava")
    fz = {t: np.load(fdir / f"{pre}{t}.npz") for t in TARGETS}
    issues = fz["mid"]["issues"] - a
    q90 = np.einsum("nhs,sk->nhk", sum(fz[t]["q90"][:, :H] for t in TARGETS), oh) / cap
    dem_real = np.clip(FLOOR + (1 - FLOOR) * real, 0, 1)
    plan = np.zeros_like(real)
    lent = np.zeros_like(real)
    for k, i in enumerate(issues):
        if 0 <= i and i + H <= real.shape[0]:
            d = FLOOR + (1 - FLOOR) * np.clip(q90[k], 0, None)
            plan[i:i + H] = np.clip(d, 0, 1)
            lent[i:i + H] = np.floor(np.clip(1 - d.max(axis=0), 0, 1) * SLICES) / SLICES
    evicted = (dem_real + lent > 1) & (lent > 0)
    days = real.shape[0] / 96
    gpu_h = np.where(evicted, 0, lent).sum(axis=0) / 4 / days
    traffic = sv[a:b].sum(axis=0)                                     # real MB carried, not load share
    share = traffic / traffic.sum()
    order = np.argsort(-traffic)
    # demo sites: busiest, a busy one with evictions, median, quiet
    ev_count = evicted.sum(axis=0)
    busy = [int(s) for s in order[:53] if gpu_h[s] > 3]                  # top-20 % that still lends
    surprise = [int(s) for s in order[:132] if ev_count[s] >= 6 and gpu_h[s] > 3 and int(s) != busy[0]]
    picks = {"Busy town-centre site": busy[0], "Median site": int(order[len(order) // 2]),
             "Quiet site": int(order[int(len(order) * 0.9)])}
    if surprise:
        picks["Site with surprises"] = surprise[0]
    demo = {"window": window, "start": str(times[0]), "qh": int(real.shape[0]), "sites": []}
    for label, s in picks.items():
        demo["sites"].append({
            "label": label, "id": str(us[s]),
            "radio": [round(float(x), 3) for x in dem_real[:, s]],
            "plan": [round(float(x), 3) for x in plan[:, s]],
            "lent": [int(round(x * SLICES)) for x in lent[:, s]],
            "evicted": [int(x) for x in np.nonzero(evicted[:, s])[0]],
            "gpu_h_per_day": round(float(gpu_h[s]), 2),
        })
    (ROOT / "site" / "data").mkdir(parents=True, exist_ok=True)
    (ROOT / "site" / "data" / "demo.json").write_text(json.dumps(demo, separators=(",", ":")))
    top20 = np.zeros(len(us), bool)
    top20[order[: int(np.ceil(len(us) * 0.2))]] = True
    sites_out = {"window": window, "sites": [
        {"share_pct": round(float(100 * share[s]), 3), "gpu_h": round(float(gpu_h[s]), 2),
         "top20": bool(top20[s])} for s in range(len(us))]}
    (ROOT / "site" / "data" / "sites.json").write_text(json.dumps(sites_out, separators=(",", ":")))
    print(window, {k: (us[v], round(float(gpu_h[v]), 2), int(ev_count[v])) for k, v in picks.items()},
          "mean gpu_h", round(float(gpu_h.mean()), 2))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "validation")
