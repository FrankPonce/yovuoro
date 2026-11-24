"""Locked test weeks (9-22 Nov 2025): the frozen forecaster method, shifted forward, run once.

Exactly the configuration chosen on the validation weeks (Yövahti D29/D31/E17/E19: weekly re-fit,
rolling Mondrian calibration, no level norm). Fit on everything before the last two weeks before
the test split, calibrate on outcomes as they become known, forecast the test weeks. No tuning.
Writes results/forecasts/test_<target>.npz and results/forecast_test_report.json (this repo only;
the Yövahti data folder is not touched).

Run:  uv run --project ../ericsson python analysis/fit_test.py
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

from yovahti.energy.model import SPLITS
from yovahti.forecast import calibration as cal
from yovahti.forecast.quantile import (HORIZON, QUANTILES, TARGETS, TZ, Forecaster, pinball,
                                       refit_predict_log, seasonal_naive, truth)
from yovahti.world.data import load_world

OUT = Path(__file__).resolve().parent.parent / "results"


def main() -> None:
    t0 = time.time()
    world = load_world("all")
    test_start = int(np.searchsorted(world.times, pd.Timestamp(SPLITS["test"][0], tz="UTC")))
    test_end = world.T
    fit_end = test_start - 14 * 96
    issues_all = np.arange(fit_end, test_end - HORIZON + 1, 4)
    evm = issues_all >= test_start
    issues = issues_all[evm]
    hour = world.times.tz_convert(TZ).hour.to_numpy()[issues_all[:, None] + np.arange(HORIZON)[None, :]]
    print(f"world {world.T} x {world.S} in {time.time() - t0:.0f}s; {len(issues)} test issues", flush=True)
    (OUT / "forecasts").mkdir(parents=True, exist_ok=True)
    report = {"config": {"calib": "rolling", "refit_days": 7, "level_norm": False,
                         "window": "test 9-22 Nov 2025", "fit_end": str(world.times[fit_end])}}
    for target in TARGETS:
        t1 = time.time()
        f = Forecaster.fit(world, target, fit_end, level_norm=False)
        mask = world.present["NR_3500"] if target == "nr" else np.ones(world.S, dtype=bool)
        logp = refit_predict_log(world, target, fit_end, issues_all, 7 * 96, base=f, level_norm=False)
        ylog = np.log1p(truth(world, target, issues_all))
        lp = cal.rolling_mondrian(logp, ylog, hour, issues_all, evm, fit_end, sectors=mask)
        pred = {q: v[evm] for q, v in cal.to_mb(lp).items()}
        y = truth(world, target, issues)[:, :, mask]
        sn = seasonal_naive(world, target, issues)[:, :, mask]
        p50 = pred[0.5][:, :, mask]
        mae = float(np.abs(p50 - y).mean())
        report[target] = {
            "skill_vs_seasonal_naive_pct": float(100 * (1 - mae / np.abs(sn - y).mean())),
            "coverage_p10_p90_pct": float(100 * ((y >= pred[0.1][:, :, mask]) & (y <= pred[0.9][:, :, mask])).mean()),
            "above_p90_pct": float(100 * (y > pred[0.9][:, :, mask]).mean()),
            "pinball_p90": pinball(y, pred[0.9][:, :, mask], 0.9),
        }
        np.savez_compressed(OUT / "forecasts" / f"test_{target}.npz", issues=issues,
                            **{f"q{int(q * 100)}": pred[q] for q in QUANTILES})
        print(f"{target}: {time.time() - t1:.0f}s {json.dumps(report[target])}", flush=True)
    (OUT / "forecast_test_report.json").write_text(json.dumps(report, indent=1))
    print("done", flush=True)


if __name__ == "__main__":
    main()
