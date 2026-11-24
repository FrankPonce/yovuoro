# Yövuoro

![Yövuoro logo](site/img/logo.svg)

**The night shift for AI-RAN: the radio always wins, the GPU pays its way.**

Yövuoro (Finnish for "night shift") by team EDISS #1 · Nokia Student Network Challenge, Turku, 24 Nov 2026 · AI challenge.

## The problem
Nokia is putting Nvidia GPUs into its future RAN. Operators push back: too much power, too much cost, and "zero benefits" (Orange CTO, 23 Nov 2026). Nokia's own answer, lending idle GPU time to AI workloads, isn't done, because nobody wants to risk the radio for it.

## The idea
At night both the radios and the base-station GPU sit idle. For every site and every quarter-hour, Yövuoro decides whether to **serve**, **sleep** the capacity radios, or **lend** spare GPU slices, planning on the pessimistic (P90) forecast so the radio always comes first. Only tenants and AI agents with a signed test result for their exact model get on; every lent slice-hour gets a signed receipt.

## The product
**Yövuoro is software**: an rApp on Nokia's MantaRay SMO, licensed per site per year and sold by Nokia inside the AI-RAN deal. No new hardware. Three pillars on one brain:

| Pillar | What it does | Result |
|---|---|---|
| **Sleep** | switches off capacity radios nobody needs, wakes them before the rush | 18.1 % radio energy saved at a sixth of static rules' congestion |
| **Lend** | rents the GPU slices the radio won't need to AI jobs, hour by hour; hands them back when traffic returns | 6.2 GPU-h / site / day, 1.1 % handed back |
| **Admit** | only AI jobs and agents that passed crash tests on their exact model get on; every lease gets a signed receipt | untested agents refused |
| *Brain* | *a cautious (P90) forecast of every site's traffic, 10 hours ahead* | *P10–P90 coverage 80–84 %* |

In: live network counters, event calendars, prices. Out: sleep/wake commands to AirScale radios, GPU slice leases to the ARC-Pro card, signed receipts to billing.

## Numbers (real live-network data, 749 sectors / 264 sites, validation weeks 26 Oct – 8 Nov 2025)

| | Result | Basis |
|---|---|---|
| Radio energy saved | **18.1 %** vs always-on, 6× less congestion than static rules | measured radio energy |
| GPU lent | **6.2 GPU-hours / site / day**, **1.1 %** evicted (planning on the average: 17.6 %) | modelled GPU demand ∝ traffic (NG1) |
| If the radio peaks at 40 % of the GPU (as measured in the literature) | **15.3 GPU-hours**, 0.65 % evicted | `results/headroom.json` |
| Night GPU lent | up to **56 %** of the GPU at 03:00–05:00 | same model |
| Busiest 20 % of sites | still **5.2 GPU-hours / day** | `results/site_map.json` |
| **Locked test weeks** (9–22 Nov, never seen) | **6.8 GPU-h / site / day, 1.2 % evicted**; forecast coverage 80–81 % | `results/gpu_test.json`, `results/forecast_test_report.json` |
| Event agent | 92 % of the derby's extra congestion removed by reading the calendar | synthetic surge on real traffic |
| LLM cost | €0.04 per 31-sector night | measured |

## See it

- **Live pitch:** https://yovuoro.vercel.app (step with → / space)
- **Full technical report:** https://yovuoro.vercel.app/report.html · [PDF](Yovuoro_report.pdf)
- **Pitch as PDF:** [Yovuoro_pitch.pdf](Yovuoro_pitch.pdf)

Run locally: `uv run --no-project python -m http.server 8779` in this folder, then open `http://localhost:8779/site/index.html`.

## Repo
- [site/](site/): the pitch (animated scroll story, arrow-key steps); `site/full.html` is the full original story for Q&A
- [docs/ROADMAP.md](docs/ROADMAP.md) · [docs/FINDINGS.md](docs/FINDINGS.md) · [docs/DECISIONS.md](docs/DECISIONS.md) · [docs/SOURCES.md](docs/SOURCES.md)
- [analysis/](analysis/): `night_shift.py` (GPU lending), `headroom.py` (sensitivity), `site_map.py` (which sites) → `results/`
- [tools/](tools/): `render_scenes.py` (Blender isometric renders, incl. the GPU cabinet), `web_images.py` (WebP trim), `export_pdf.py` (backup PDF from the site)

Built on [Yövahti](https://github.com/FrankPonce/yovahti), an open-source research prototype: forecaster, planner, MCP server, NetCrash, `admit()` and attestations (agent-trust-kit compatible).

```powershell
# with the Yövahti repo cloned next to this one and its data pipeline run:
uv run --project ../yovahti python analysis/night_shift.py
```
