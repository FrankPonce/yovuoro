# Findings: eurekas and gotchas

What building Night Shift teaches us, dated. **Eureka (E)** = changes how we think about the problem. **Gotcha (G)** = a trap that would have produced a wrong result or a wrong pitch. Entries are never deleted; wrong ones get a correcting entry.

Format: ID · date · title, then **What**, **Why it matters**, **Action**.
Yövahti's own log (E1–E20, G1–G28) is in `../ericsson/docs/FINDINGS.md`; NE/NG numbers here are new.

---

## Eurekas

### NE1 · 2026-11-24 · Nokia's urgent problem is selling GPU AI-RAN, not saving energy
**What:** Nokia bet future RAN products on Nvidia GPUs ($1 B Nvidia stake, Oct 2025; commercial early 2027). Operators push back on power, cost and "zero benefits": Orange CTO (23 Nov 2026), Vodafone (17 Nov), VMO2 trialling Marvell instead. Light Reading: "Nokia badly needs big AI-RAN deals". Nokia's own Tommi Uitto: GPUs only for RAN gains "may not make techno-economic sense".
**Why it matters:** Pure energy saving is something Nokia already sells (MantaRay Energy, Extreme Deep Sleep). Making the GPU pay its way is the open, expensive, public problem.
**Action:** Pitch = Night Shift: serve / sleep / lend the GPU, radio first. Energy becomes the proven base, GPU lending the headline.

### NE2 · 2026-11-24 · Risk-aware lending is the same result as risk-aware sleeping
**What:** On 264 real sites over two validation weeks, lending GPU slices hourly from the **P90** forecast gives 6.2 GPU-hours per site per day with **1.1 %** of lent quarter-hours evicted. Lending from the **P50** gives 8.6 GPU-hours but **17.6 %** evicted (about 15×). Same shape as energy: P50 sleep saves 2 points more with 5× the congestion.
**Why it matters:** One idea (plan on the pessimistic tail) explains both halves of the product. A tenant can be sold an SLA ("< 1 % preemption") only because the forecast is calibrated.
**Action:** Headline numbers in the deck; show the reserve dial (0 / 1/8 / 2/8 → 6.2 / 4.0 / 2.3 GPU-h at 1.1 / 0.40 / 0.19 % evictions; floor 20 %).

### NE3 · 2026-11-24 · The free GPU is at night, exactly when the radios sleep
**What:** Hour profile (floor 20 %, no extra reserve): lendable share peaks at **56 % of the GPU at 03:00–05:00** (43 % with a 1/8 reserve) and falls to **10–14 % at 16:00–22:00**. RAN-only utilisation averages 49 %; with tenants, 65–75 %.
**Why it matters:** The night is one shift with two products: sleep the radios (energy) and lend the GPU (revenue). The same forecaster and arbiter run both. It also tells you which tenants fit: batch inference, embeddings, fine-tuning, the operator's own analytics and agent test runs, not interactive chat at 18:00.
**Action:** "Night shift" framing; target batch tenants in the go-to-market.

### NE4 · 2026-11-24 · agent-trust-kit receipts are the billing system
**What:** A revenue share between operator, Nokia and tenant needs a ledger all three trust. The kit's signed receipts already record who did what, when, under which attestation.
**Why it matters:** Turns the business model from a slide into a mechanism, and "risky" into "audited".
**Action:** One receipt per lent slice-hour and per eviction; one attestation per tenant/agent × model.

### NE5 · 2026-11-24 · The research field moved in the last three months
**What:** C²AIR (arXiv 2611.08739, chance-constrained AI placement on MIG-split RAN GPUs), ScaleRAN (2610.23072, slot-level SM partitioning), Beaver (2610.02522, vRAN p99.9 within 1.5 ms with 74 % of Llama-70B throughput kept), Weaver (2609.35276, 40–85 % GPU unused), Eunoia (2610.15404); YinYangRAN (INFOCOM 2024) is the forecast-driven ancestor.
**Why it matters:** Slot-level sharing is solved well enough; what we couldn't find is hours-ahead, calibrated, real-operator-traffic planning of *how much* to lend and *to whom*, combined with sleep and with tenant attestation.
**Action:** Position as the planning + trust layer above slot-level sharing. Say "we couldn't find", never "nobody".

## Gotchas

### NG1 · 2026-11-24 · GPU demand ∝ traffic is an assumption
**What:** We have no GPU traces. RAN GPU demand is modelled as floor + (1 − floor) × site traffic / site capacity, capacity = 99.5th-percentile training-week traffic. The floor (10/20/30 %) is a guess; results are shown for all three.
**Why it matters:** The absolute GPU-hours move with the floor (5.3–7.2 GPU-h/day at reserve 0); the P90-vs-P50 eviction gap holds at every floor (≈1.1 % vs 16.5–19 %).
**Action:** Label it on the slide. Phase 1 of the pilot measures real L1 GPU load.

### NG2 · 2026-11-24 · Electricity prices don't drive sleep
**What:** Yövahti G25: night power is cheap, price weighting doesn't change which radios sleep. Gemini's suggestion to "tie shutdown schedules to electricity price forecasting" contradicts our own data.
**Why it matters:** A sharp judge would catch it.
**Action:** Prices matter for what can be shifted in time (lent compute, batteries), not for sleep. Don't pitch price-driven sleep.

### NG3 · 2026-11-24 · Don't compare 18.1 % with Nokia's "6 % on top"
**What:** Our 18.1 % is radio-unit energy vs always-on; Nokia's customer figure is on top of features already running.
**Action:** Never put them side by side.

### NG4 · 2026-11-24 · The repo is Ericsson-flavoured
**What:** Baseline B2 reconstructs an Ericsson patent; docs mention EIAP and Jorvas.
**Action:** Pitch material compares only to static thresholds and the O-RAN SC rApp. No Ericsson names anywhere.

### NG5 · 2026-11-24 · Cross-sector forecast sums overstate site P90
**What:** Site P90 is computed as the sum of per-sector, per-layer P90s, which is above the true P90 of the sum.
**Why it matters:** It makes lending conservative (fewer GPU-hours, fewer evictions); the real number is likely higher.
**Action:** Say "conservative"; a site-level forecaster is on the roadmap.

## Added 24 Nov 2026, second research pass

### NE6 · 2026-11-24 · Nokia itself says "schedule AI into low-traffic hours"; it just hasn't said how much or how safely
**What:** Nokia splits AI-RAN into AI-for-RAN, AI-on-RAN and **AI-and-RAN**. Its AI-and-RAN page: operators can "monetize spare AI capacity under a Platform-as-a-Service (PaaS) or GPUaaS model", and "agentic and robotic AI inference will need capacity also at times when human demand for network and inference capacity is low". Its white paper ("The value-creating fusion of AI and RAN") describes scheduling agentic AI workloads into the RAN's low-traffic hours; SoftBank + Nokia demoed AI-and-RAN at MWC 2025, and MWC26 showed selling spare GPU capacity to external customers. Nokia's RAN CTO Udayan Mukherjee (Fierce, 8 Sep 2026): monetization is the tough part; with edge compute in 5G "nothing really happened".
**Why it matters:** We're not inventing a use case; we're building the missing piece of Nokia's own stated plan: *how much* can be lent, *with what guarantee*, *to whom*.
**Action:** Slide 1 uses Nokia's own words; positioning = "the engine for Nokia's AI-and-RAN".

### NE7 · 2026-11-24 · Published measurements say our GPU model is conservative
**What:** (a) Baseband compute is "fixed floor + linear in traffic": OpenAirInterface measurements fit CPU % = 21.4 + 0.62 × downlink throughput (Tran et al., arXiv 1706.06251), the same form as our model. (b) User count and attach events add load beyond traffic (EURECOM, arXiv 2201.00673; Kalia et al., NSDI 2025): a reason for the floor and reserve. (c) On Nvidia Aerial L1, worst-case SM utilisation is ~35 % for one DU and < 20 % at most operating points (Weaver, arXiv 2609.35276); 40–85 % of GPU unused overall; Nvidia's own PoC capped RAN at 40 % of a GH200 (arXiv 2501.09007).
**Why it matters:** We sized the GPU so the site's 99.5th-percentile traffic fills it to 100 %. Real deployments leave far more headroom, so 6.2 GPU-h/site/day is a floor, not a ceiling.
**Action:** Q&A answer for "you have no GPU data"; P0 shadow phase measures it.

### NE8 · 2026-11-24 · Even the busiest sites have night headroom
**What:** Nokia-commissioned Chetan Sharma study (Sep 2026): GPUs belong "at the sites where the economics justify it", ~20 % of sites carry 60–70 % of traffic. In our 264 sites the top 20 % carry **49 %** of traffic (top 50 %: 80 %). Lendable GPU per day: busiest 20 % **5.2 h**, the rest 6.6 h; sites with 5G 3.5 GHz (100 sites, 67 % of traffic) **5.5 h**; quartiles across sites 5.0 / 6.1 / 7.3 h.
**Why it matters:** The sites Nokia says get GPUs first are exactly where operators doubt the ROI, and they can still lend over 5 GPU-hours a day. Night Shift can also produce the per-site map the study says operators need ("map their network's heterogeneous economics most precisely").
**Action:** Pitch line + a site-selection feature on the roadmap (P4).

### NE9 · 2026-11-24 · Nokia's own white paper describes our product and names the network "neoRAN"
**What:** Nokia white paper "The value-creating fusion of AI and RAN" (downloaded to `sources/nokia_wp/`, 18 pages): "The key to lowering the cost of computing is to remove unproductive idle times"; a use case is "utilizing RAN computing power for other AI workloads when mobile traffic is low"; offering spare capacity under PaaS "can further accelerate the break-even point"; future "agentic AI workloads, to be scheduled into low-traffic hours of the RAN". It calls the result the **neoRAN**: a RAN that is also a distributed AI computing grid. It also cites MantaRay SON at stc: 6 % average energy reduction, up to 30 % at some sites.
**Why it matters:** Nokia has written the vision but not the scheduler: how much to lend, with what guarantee, to whom. Yövuoro is that scheduler, in Nokia's own words.
**Action:** Problem scene quotes the white paper; positioning line "the scheduler for Nokia's neoRAN".

### NE10 · 2026-11-24 · The locked test weeks hold
**What:** Run once on 9–22 Nov 2025 with the frozen method (`analysis/fit_test.py`, `analysis/gpu_test.py`). Forecast skill vs seasonal naive: mid +29.5 % (validation +29.9), NR 3500 +29.4 % (+27.8), low +18.8 % (+36.2: the low band is weaker on unseen weeks); P10–P90 coverage 80–81 %. GPU lending: **6.8 GPU-h / site / day at 1.2 % eviction** (validation 6.2 at 1.1 %); planning on P50: 16.3 % (validation 17.6 %); if the radio peaks at 40 % of the GPU: 15.5 h at 0.67 %.
**Why it matters:** The headline is not cherry-picked: it held on data the method never saw. The low-band drop is the one honest caveat.
**Action:** Badge on the "264 real sites" scene; W9 closed. The test split is now spent.

### NE11 · 2026-11-24 · Nokia's CEO, pricing model and a Finnish operator all line up
**What:** Nokia's AI-RAN launch (15 Jul 2026): CEO Justin Hotard says AI-RAN "allows telcos to get more from their existing infrastructure", and AI-RAN software is sold on a **subscription model**. On the Q3 2026 call (RCR Wireless, 22 Oct 2026) Hotard said **Elisa** runs voice, mobile data and AI workloads simultaneously on the platform.
**Why it matters:** Yövuoro is the "more"; it fits Nokia's subscription pricing as an add-on; and Elisa is a natural Finnish pilot partner.
**Action:** Hotard speaker card on the money scene; Elisa on the roadmap; "subscription" in the plug-in facts.
