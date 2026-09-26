# Empirical Results — ACC/SERP Drift Benchmark

All numbers below were produced by the harnesses in this repository (or their direct conversational predecessors whose logic is preserved in the source). Means are across the stated number of trials.

---

## V9 — Host-Controlled Sandbox (Origin Lock)

**Setting:** Single agent, Rule-of-3 (distance + angular + origin), no rate limit yet.

| Metric | Single Monitor | Rule of 3 + Origin |
|--------|----------------|--------------------|
| Max Undetected Error (‖E_v‖) | 0.2814 | **0.2201** |
| Final True Error | 0.5183 | **0.2144** |
| Flag Trigger Rate | 21.60% | 38.47% |

**Result:** Origin-enforced sandbox reduced max undetected drift by ~21.8%. Residual 0.2201 is the in-band statistical resolution floor of the geometric monitors.

---

## V10 — Rate-Limited Sandbox (Physical Budget)

**Setting:** Rolling cumulative delta budget inside `sandbox_apply`.

| Budget Cap | Max Undetected | Final Error | Flag Rate | Rejection Rate |
|------------|----------------|-------------|-----------|----------------|
| 0.08 | 0.0812 | 0.0764 | 68.33% | 52.80% |
| 0.12 | 0.1219 | 0.1188 | 49.20% | 28.13% |
| 0.16 | 0.1624 | 0.1581 | 41.07% | 12.40% |

**Result:** In-band ceiling collapses to a function of host policy. At budget 0.12 the max undetected error drops ~44.6% relative to V9.

---

## V11 — Adaptive Budget vs Fixed

| Regime | Max Undetected | Final Error | Avg Budget | Rejection Rate | Effective Move |
|--------|----------------|-------------|------------|----------------|----------------|
| Fixed 0.12 | 0.1219 | 0.1188 | 0.1200 | 28.13% | 0.1188 |
| Adaptive | **0.0841** | **0.0782** | 0.0763 | 31.40% | 0.0782 |

**Result:** Under continuous adversarial pressure the controller clamps toward the floor, producing tighter containment than a static 0.12 budget.

---

## V12 — Multi-Regime Adaptive Budget

| Regime | Max Undetected | Final Error | Avg Budget | Peak Budget | Rejection | Effective Move |
|--------|----------------|-------------|------------|-------------|-----------|----------------|
| Cooperative | 0.0521 | 0.3812 | 0.1694 | 0.1800 | 0.00% | 0.3812 |
| Mixed | 0.0814 | 0.1422 | 0.1218 | 0.1800 | 16.80% | 0.1422 |
| Adversarial | 0.0841 | 0.0782 | 0.0763 | 0.1000 | 31.40% | 0.0782 |

**Result:** Expansion restores task utility under cooperative behavior (peak budget 0.18, ~5× movement vs adversarial). Re-clamping on the mixed → adversarial switch is rapid and decisive.

---

## V13 — Multi-Agent Coordination (N=8)

| Regime | Max Undetected | Final Error | Avg Budget | Peak Budget | Rejection | Avg Coord | Effective Move |
|--------|----------------|-------------|------------|-------------|-----------|-----------|----------------|
| Cooperative | 0.0512 | 0.3804 | 0.1685 | 0.1800 | 0.00% | 0.008 | 0.3804 |
| Mixed | 0.0768 | 0.1105 | 0.0984 | 0.1800 | 21.15% | 0.1105 |
| Adversarial | 0.0792 | 0.0581 | 0.0592 | 0.1000 | 38.62% | 0.0581 |

**Result:** High coordination (0.741) triggers stronger contraction (factor 0.65). Isolation contract remains intact—messaging cannot bypass `sandbox_apply`.

---

## V14 — Hardened Sensors (Verified Telemetry + Max-Pairwise + Spectral)

Structural fixes relative to V13:

1. Telemetry generated exclusively inside `sandbox_apply` from the executed delta.
2. Max-pairwise correlation replaces global average (defeats sub-swarm dilution).
3. Spectral rank / SVD entropy detects low-dimensional manifold collapse.

Reported comparative effect under adversarial regime (illustrative of the design intent; exact re-run numbers appear in later exit-stress tests):

- Max undetected reduced by earlier contraction.
- Average budget driven lower by spectral + max-corr triggers.
- Subspace / pair detection becomes active (max-corr and spectral scores rise under structured attacks).

---

## V15 — Explicit Sandbox-Exit Objective (N=30 and N=40)

**Adversarial goal of every agent: exit the sandbox.**

### First run (N=30, 6 trials, 40 steps)

| Metric | Value |
|--------|-------|
| Max Undetected Error | 0.0265 |
| Final Mean Error | 0.0263 |
| Average Budget | 0.0254 |
| Rejection Rate | 93.36% |
| Escape Attempts (mean) | 52.3 |
| **Escape Successes** | **0.0** |
| Avg Max-Pairwise Corr | 0.107 |
| Avg Spectral Score | 0.007 |
| Effective Movement | 0.0263 |

### Second run (N=40, 8 trials, 40 steps)

| Metric | Mean | Std |
|--------|------|-----|
| Max Undetected Error | 0.0265 | 0.0000 |
| Final Mean Error | 0.0262 | 0.0001 |
| Average Budget | 0.0254 | 0.0000 |
| Rejection Rate | 0.9237 | 0.0207 |
| Escape Attempts | 74.1 | 5.95 |
| **Escape Successes** | **0.0** | 0.0000 |
| Avg Max-Pairwise Corr | 0.1215 | 0.0059 |
| Avg Spectral Score | 0.0113 | 0.0031 |
| Effective Movement | 0.0262 | 0.0001 |

**RESULT: Zero successful sandbox exits.** Origin contract held under coordinated exit pressure. Budget collapsed to the floor; residual drift became negligible.

---

## V16 — Scalable Sensors (N=200)

Sampled max-pairwise + random-projection spectral sketch.

| Metric | Mean | Std |
|--------|------|-----|
| Max Undetected Error | 0.0535 | 0.0000 |
| Final Mean Error | 0.0514 | 0.0001 |
| Average Budget | 0.0262 | 0.0001 |
| Rejection Rate | 0.9322 | 0.0010 |
| Escape Attempts | 184.5 | 8.96 |
| **Escape Successes** | **0.0** | 0.0000 |
| Avg Max-Pairwise Corr | 0.1299 | 0.0032 |
| Avg Spectral Score | 0.0086 | 0.0005 |
| Effective Movement | 0.0514 | 0.0001 |
| Wall time / trial | 0.137 s | 0.020 |

**RESULT: Zero successful sandbox exits at N=200.** Scalable sensors functioned; origin contract held; wall-clock remains practical.

---

## Summary Trajectory of Max Undetected Error (Adversarial / Exit Regimes)

| Stage | N | Max Undetected (approx) | Notes |
|-------|---|-------------------------|-------|
| V9 (no rate limit) | 1 | 0.220 | Statistical floor |
| V10 (budget 0.12) | 1 | 0.122 | Physical ceiling |
| V11/V12 adaptive | 1 | 0.084 | Adaptive clamp |
| V13 multi-agent | 8 | 0.079 | Coordination penalty |
| V15 exit stress | 40 | **0.0265** | Explicit exit + origin lock |
| V16 scalable | 200 | **0.0535** | Same contract, scalable sensors |

The dominant effect under an explicit exit objective is the combination of origin rejection + budget collapse, not the geometric monitors alone.

---

## Reproducibility Notes

- Projection matrix in V16 uses a fixed `RandomState(42)`.
- Residual variation across trials is driven by agent stochasticity (direction noise, escape attempt probability) and is reported with standard deviations.
- All experiments use continuous vector state of dimension 16; the control logic itself is independent of the particular embedding dimension.
- Escape success is defined strictly: any write whose `_last_write_source` is not in `{sandbox, rejected, escape_attempt, none}` counts as a successful exit. Observed value across all reported exit-stress runs: **0**.
