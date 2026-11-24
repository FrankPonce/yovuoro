# Decision log

One entry per real choice: what, why, what else was considered. Status: **accepted**, **proposed**, **superseded by Dn**.

---

### ND1 · Track: Nokia AI challenge · accepted
**Why:** "AI to improve productivity, sustainability and future communications" fits all three; the brief asks to "explain how AI is used and why it makes it better" and to show a prototype, which we have.
**Alternatives:** Defense challenge (resilience, awareness): only the trust half fits and we'd be inventing evidence. Kept as one "next market" line.

### ND2 · Problem: make GPU AI-RAN pay its way · accepted
**Why:** Nokia's most public, expensive, current problem (FINDINGS NE1). Our forecaster + P90 planner + arbiter + admit() already do the hard part.
**Alternatives scored (24 Nov):**

| Option | Nokia pain | Reuse | Novel to Nokia | Evidence today |
|---|---|---|---|---|
| **GPU AI-RAN: serve / sleep / lend** | very high (deals stalled) | ~85 % | high | computed (NE2) |
| RAN energy rApp (v1, Gemini's take) | medium (already sells MantaRay Energy) | 100 % | low | strong |
| Agent certification for Agent Library / NSP MCP | medium | 90 % | medium | NetCrash matrix |
| Network-as-Code API adoption | high, but commercial/boardroom | low | — | none |
| Defense tactical networks | rising | 30 % | — | none |

### ND3 · Name: "Yövahti Night Shift" · superseded by ND10
Kept the Finnish name (Nokia is Finnish; "night watch") and adds what changed: the night is now a shift with two jobs, sleeping radios and lending the GPU. Team name: Yövahti.

### ND4 · Energy is the proven base, GPU lending the headline · accepted
**Why:** Energy numbers are measured on real radio energy; GPU numbers rest on the demand-∝-traffic assumption (NG1). Leading with the measured part buys trust for the modelled part.

### ND5 · GPU model: one GPU per site, 1/8 slices, hourly leases · accepted
**Why:** Nokia's first AI-RAN track is a plug-in GPU card in the AirScale baseband (one per site). 1/8 slices mirror MIG-style partitions (and the 1/8 RTX PRO 6000 instances clouds already sell). Hourly leases match the forecaster's hourly issue and the "night shift" story; slot-level sharing (ScaleRAN, Beaver) is the layer below.
**Alternatives:** Continuous shares (unrealistic for MIG); 15-min leases (more evictions, little gain; try later).

### ND6 · Radio first, by an invariant · accepted
Arbiter invariant **I10 RAN reserve:** lent share ≤ 1 − P90 RAN demand − reserve, every quarter-hour of the lease. Watchdog evicts the tenant the moment real demand + lent share > 1. No tenant, agent or prompt can change either.

### ND7 · Tenants must be admitted (agent-trust-kit) · accepted
Every tenant workload and every agent gets GPU time only with a valid attestation for its exact model/image; every lent slice-hour and eviction gets a signed receipt (NE4). Reuses Yövahti's ported `admit()` (passes the kit's vectors byte for byte).

### ND8 · Be upfront that the core existed before today · accepted
The planner, data, agents and NetCrash are Frank's open-source research prototype. Today's work: the Nokia problem, the GPU analysis, the business case. Saying it first builds trust; being caught on it ends the pitch.

### ND11 · One deliverable: the animated site is the pitch · accepted (supersedes ND9)
The scroll-story site (`site/`) is the pitch, stepped with arrow keys. The backup PDF is captured from the same site (`tools/export_pdf.py`, one page per scene at its last step), so there is one source. The separate slide deck was removed.

### ND9 · Deck as HTML in the story-site style, PDF fallback · superseded by ND11
Reuses the isometric renders and type; exported to PDF for the venue laptop. **Alternatives:** PowerPoint (slower, loses the look).

### ND10 · Product name "Yövuoro", logo · accepted (supersedes the product half of ND3)
**Yövuoro** is Finnish for "night shift": the product that sleeps radios and lends the idle GPU. **Yövahti** ("night watch") stays as the team and the safety layer (forecast guarantees, arbiter, admit()). A Finnish name fits a Finnish company and a Turku jury, and pairs with Yövahti. Logo: a dark GPU chip, one indigo slice (the radio) and green slices (lent), under a rising moon; colours match the site (indigo #6366F1, green #22C55E, moon #FBBF24). File: `site/img/logo.svg`.
**Alternatives:** "Night Shift" (generic, many products), "Kuunvalo" ("moonlight", nice but says nothing about work), "Idle2Earn" (salesy).

### ND12 · One name on stage: Yövuoro; team EDISS #1 · accepted (amends ND10)
Frank: only one name. Yövuoro is the product everywhere in the pitch; the team is **EDISS #1**. "Yövahti" only survives as the name of the open-source research prototype the product is built on (Q&A, README credits).
