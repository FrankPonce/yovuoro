# Yövuoro: roadmap

Status: 24 Nov 2026. Two horizons: **today** (the pitch at 12:45) and **the product** (what we'd build with Nokia; this is also the "HOW" slide).

## Rules

1. Every step ends with something that runs or can be shown.
2. Measured before modelled: energy numbers are measured on real radio energy; GPU numbers are modelled and say so (NG1).
3. Log as you go: surprises → [FINDINGS.md](FINDINGS.md), choices → [DECISIONS.md](DECISIONS.md), sources → [SOURCES.md](SOURCES.md).
4. Radio first, always: no step may add a path where a tenant or agent can take capacity the radio needs (ND6).

---

## Horizon 1: today, 24 Nov 2026

| # | Step | Done when | Status |
|---|---|---|---|
| T0 | Brief + repo audit | Challenge PDF read; Yövahti reuse mapped | done |
| T1 | Research Nokia's problems | 6 problems scored (ND2); pick made | done |
| T2 | Night Shift analysis | `analysis/night_shift.py` on 264 real sites; results in `results/night_shift.json` | done (NE2, NE3) |
| T3 | Docs | README, ROADMAP, FINDINGS, DECISIONS, SOURCES | done |
| T4 | Business numbers | Value per site, per operator; pricing; costs (below) | done (first pass) |
| T5 | Pitch deck | Title + Nokia's 3 project slides + close, HTML → PDF | |
| T6 | Script + Q&A sheet | ≤ 650 words; 8 hard questions answered | |
| T7 | Rehearse ×2 | 4:45 on the clock | |
| T8 | Stretch: Nokia-ised story site | Night Shift section; B2 removed | done (`site/`, served from the repo root) |

**Timeline:** 10:00–10:30 Nokia talk (note their words) · 10:35–11:30 T5–T6 · 11:30–12:15 lunch + T7 · 12:15–12:40 PDF, screenshots, venue check · 12:45 pitch.

---

## Horizon 2: the product

| Phase | What | Done when | Reuse |
|---|---|---|---|
| **P0 · Shadow** (month 1–2) | Night Shift runs beside a live Nokia AI-RAN cluster (e.g. Turku, Finnish operator), plans but doesn't act. Measure real L1 GPU load vs traffic (closes NG1) | Forecast coverage and would-be eviction rate measured on real GPU traces | forecaster, planner, MCP |
| **P1 · Sleep** (month 2–3) | Acts on radio sleep inside arbiter limits, as an rApp on MantaRay SMO alongside MantaRay Energy | kWh saved at zero KPI degradation, signed receipts | planner, arbiter, watchdog |
| **P2 · Lend** (month 3–5) | Lends GPU slices hourly to admitted tenants: the operator's own batch AI first (analytics, embeddings, agent test runs), then external batch inference | GPU-hours lent, eviction < 1 %, receipts reconcile with billing | arbiter I10, admit(), receipts |
| **P3 · Agents** (month 4–6) | AI agents from Nokia's Agent Library act through MCP only after NetCrash on the model they run; event agent reads calendars | Attested agents only; event-night congestion reduced | MCP, NetCrash, attestations |
| **P4 · Scale** (6 months+) | Site-selection map: which sites get GPUs (NE8); Multi-site placement (C²AIR-style chance constraints across sites), site-level forecaster (NG5), price-aware lending (prices matter for shiftable compute, NG2), certification as a service | Fleet-level results; certification revenue | — |

### Building blocks

| Block | Status | Source |
|---|---|---|
| Real data: 749 sectors, 264 sites, 15-min load + radio energy | ready | Yövahti S1 |
| Energy model per radio unit (R² 0.84–0.96), 3GPP TR 38.864 sleep | ready | Yövahti S2 |
| Quantile forecaster, conformal calibration (P10–P90 coverage 80–84 %) | ready | Yövahti S4 |
| DP sleep planner (18.1 % saved, 6× less congestion than static rules) | ready | Yövahti S5 |
| GPU lending planner (hourly, 1/8 slices, P90 + reserve) | prototype | `analysis/night_shift.py` |
| Arbiter I1–I5 + **I10 RAN reserve**, watchdog | I1–I5 ready; I10 in analysis only | Yövahti S8 |
| MCP server (12 tools), agents, budget guard | ready (first slice) | Yövahti S6–S7 |
| NetCrash (11 tests + N20 calendar injection), attestations, `admit()` (agent-trust-kit compatible) | v0 ready | Yövahti S8–S9 |
| Story site + isometric renders | ready (Ericsson-flavoured) | Yövahti `web/` |

### Partners and resources

- **Nokia:** AI-RAN (ARC-Pro / AirScale GPU card), MantaRay SMO + Non-RT RIC, Agent Library, NSP MCP framework.
- **Nvidia:** MIG / Green Contexts for slot-level isolation (the layer below us).
- **Operator:** one Finnish operator for P0–P2 (Turku cluster).
- **Research:** slot-level sharing papers (ScaleRAN, Beaver, Weaver) are complementary; AI-RAN Alliance for the attestation standard.
- **Team:** ~3 engineers × 6 months (forecasting/optimisation, platform integration, security/trust).

## Business case (first pass, assumptions explicit)

| Line | Number | Basis |
|---|---|---|
| GPU lent | 6.2 GPU-h / site / day at 1.1 % eviction (4.0 at 0.4 %) | NE2, floor 20 % |
| Lending value | ~€360 / site / yr | 2 270 GPU-h × €0.40/GPU-h (well under cloud RTX PRO 6000 $1.5–3/h, matches 1/8-instance pricing) × 40 % sell-through |
| Energy value | ~€330 / site / yr | 2.68 kWh/sector-day × 2.8 sectors × 365 ≈ 2.8 MWh × €0.12/kWh |
| **Value per site** | **~€700 / yr** | |
| Operator, 10 000 AI-RAN sites | **~€7 M / yr** | |
| Price | ~20 % of value: €140 / site / yr licence (or rev share on lending) + €10–20 k per agent × model certification | operator keeps ~80 % |
| ARR per operator | **~€1.4 M** + certification | |
| Running cost | LLM ≈ €0.50 / sector / yr (€0.04 per 31-sector night); compute negligible | Yövahti E20 |
| Build cost | ~3 engineers × 6 months | |

## Risks

| Risk | Fallback |
|---|---|
| GPU demand doesn't track traffic (NG1) | P0 measures it; the energy half stands alone |
| Inference prices collapse | Energy carries the base case; tenants are the operator's own batch AI first |
| Operators don't buy GPUs at all | Same planner sells to non-GPU sites as an energy + agent-trust rApp |
| Judges see it as an Ericsson project | ND8: say it first; no Ericsson names in material |
