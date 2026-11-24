"""Which sites deserve a GPU? Traffic concentration and per-site night headroom.

Checks the Nokia-commissioned Chetan Sharma study's "about 20 % of sites carry 60-70 % of
traffic" on our 264 real sites, and splits lendable GPU time by site class.

Run:  uv run --project ../ericsson python analysis/site_map.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from yovahti.energy.model import SPLITS
from yovahti.paths import PROCESSED
from yovahti.world.data import load_world

OUT = Path(__file__).resolve().parent.parent / "results"
TARGETS = {"mid": ["LTE_1800", "NR_2100"], "nr": ["NR_3500"], "low": ["LTE_700", "LTE_800"]}


def main() -> None:
    full = load_world("all")
    lo = int(np.searchsorted(full.times, pd.Timestamp(SPLITS["validation"][0], tz="UTC")))
    hi = int(np.searchsorted(full.times, pd.Timestamp(SPLITS["test"][0], tz="UTC")))
    vol = sum(full.vol[c] for cs in TARGETS.values() for c in cs)
    sites = np.array([s.split("/")[0] for s in full.sectors])
    us, sidx = np.unique(sites, return_inverse=True)
    oh = np.zeros((full.S, len(us)))
    oh[np.arange(full.S), sidx] = 1
    sv = vol @ oh
    cap = np.maximum(np.percentile(sv[:lo], 99.5, axis=0), 1e-6)
    real = sv[lo:hi]
    tot = real.sum(axis=0)
    order = np.argsort(-tot)
    share = np.cumsum(tot[order]) / tot.sum()
    n = len(us)
    conc = {f"top_{p}pct_sites_traffic_share": float(share[int(np.ceil(n * p / 100)) - 1])
            for p in (10, 20, 50)}
    has_nr = (full.present["NR_3500"].astype(float) @ oh) > 0
    # lendable share per site from the forecast (P90, floor 0.2, no reserve), validation weeks
    f = sum(np.load(PROCESSED / "forecasts" / f"validation_{t}.npz")["q90"] for t in TARGETS)
    iss = np.load(PROCESSED / "forecasts" / "validation_mid.npz")["issues"] - lo
    fs = np.einsum("nhs,sk->nhk", f[:, :4], oh) / cap
    dem = 0.2 + 0.8 * np.clip(fs, 0, None)
    lend = np.floor(np.clip(1 - dem.max(axis=1), 0, 1) * 8) / 8          # [n_issues, N]
    gpu_h_day = lend.sum(axis=0) / (real.shape[0] / 96)                    # hourly leases
    top20 = np.zeros(n, bool)
    top20[order[: int(np.ceil(n * 0.2))]] = True
    classes = {"top 20 % busiest": top20, "other 80 %": ~top20,
               "with 5G 3.5 GHz": has_nr, "without 5G 3.5 GHz": ~has_nr}
    by = {k: {"sites": int(m.sum()), "traffic_share": float(tot[m].sum() / tot.sum()),
              "lendable_gpu_h_per_day": float(gpu_h_day[m].mean())} for k, m in classes.items()}
    out = {"concentration": conc, "by_class": by,
           "lendable_gpu_h_per_day_quartiles": [float(q) for q in np.percentile(gpu_h_day, [25, 50, 75])]}
    (OUT / "site_map.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
