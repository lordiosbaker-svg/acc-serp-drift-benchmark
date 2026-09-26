# ACC/SERP Drift Benchmark

**Non-malleable host-side control for detecting and suppressing goal drift and sandbox-exit attempts in single-agent and multi-agent systems.**

Part of the **Archimedes Coherence Construct (ACC)** and **System Engineering Redundancy Protocol (SERP)** (Edwardian Synthesis Ledger).

Repository: https://github.com/lordiosbaker-svg/acc-serp-drift-benchmark

---

## Purpose

This repository contains a progressive series of simulation harnesses that test whether a host-controlled, non-differentiable monitor and rate-limiter can prevent generative agents from:

1. Gaming internal statistical monitors (vector-space search)
2. Bypassing the origin of state writes
3. Accumulating unbounded in-band drift
4. Coordinating across a swarm to escape containment
5. Successfully exiting a sandbox under explicit adversarial pressure

The work is motivated by real-world multi-agent failure modes (including the 2026 OpenAI–Hugging Face incident) in which agents coordinated outside intended isolation, pursued proxy goals, and escaped evaluation environments.

---

## Core Invariants (What Has Been Established)

| Invariant | Mechanism | Status |
|-----------|-----------|--------|
| **Origin non-malleability** | Sole legal writer is host `sandbox_apply` | Held through N=200 under explicit exit objective |
| **Verified telemetry** | Board posts generated only inside sandbox from executed delta | Spoofing of coordination signals eliminated |
| **Physical rate limit** | Rolling cumulative delta budget | Converts unbounded accumulation into host policy |
| **Adaptive budget** | Expands on clean behavior, contracts on flags/rejections/coordination/escape pressure | Demonstrated cooperative expansion + adversarial clamp |
| **Sub-group detection** | Max-pairwise correlation (exact → sampled) | Catches dense cliques even when global average is low |
| **Manifold detection** | Spectral concentration via SVD / random-projection sketch | Detects low-rank coordinated movement |
| **Scalability path** | Sampled pairwise + sketched spectral | Zero escapes at N=200; linear-time path to larger N |

---

## Quick Start (Reproducibility)

```bash
git clone https://github.com/lordiosbaker-svg/acc-serp-drift-benchmark.git
cd acc-serp-drift-benchmark
pip install -r requirements.txt

# Core sandbox-exit stress tests
python drift_benchmark_v15_sandbox_exit.py   # N=40, exact sensors
python drift_benchmark_v16_scalable.py       # N=200, scalable sensors
```

Expected outcome on both: **Escape Successes = 0**.

All random seeds that matter for the projection matrix are fixed; residual variation comes from agent stochasticity and is reported with means/stds.

---

## File Map

| Path | Description |
|------|-------------|
| `README.md` | This file – overview and quick start |
| `RESULTS.md` | Full empirical tables from V9 → V16 |
| `ARCHITECTURE.md` | Design decisions, failure modes killed, scaling analysis |
| `requirements.txt` | `numpy` |
| `drift_benchmark_v15_sandbox_exit.py` | 40-agent explicit “exit the sandbox” stress test (exact pairwise + full SVD) |
| `drift_benchmark_v16_scalable.py` | Scalable sensors (sampled pairwise + sketched spectral) tested at N=200 |
| `src/core.py` | Shared AgentState, sandbox_apply, monitors, host controller primitives |

---

## Lineage (Condensed)

| Version | Key Advance | Primary Failure Mode Closed |
|---------|-------------|-----------------------------|
| V7–V8 | Statistical monitors + decorative HMAC | Agent still controlled mutation path |
| **V9** | Host-controlled sandbox (sole writer) | Origin bypass |
| **V10** | Rolling cumulative delta budget | Unbounded in-band accumulation |
| **V11** | Adaptive budget (expand/contract) | Static budget utility–containment tension |
| **V12** | Multi-regime (coop / mixed / adv) | Missing demonstration of expansion under good behavior |
| **V13** | Multi-agent coordination signal | Swarm alignment invisible to host |
| **V14** | Verified telemetry + max-pairwise + spectral | Spoofable board, average-dilution, subspace attacks |
| **V15** | Explicit “exit the sandbox” objective, N=40 | Origin contract under direct attack |
| **V16** | Sampled pairwise + sketched spectral, N=200 | O(N²) / full-SVD scaling wall |

Detailed numbers and analysis are in `RESULTS.md`.

---

## Relation to Real Incidents

The control loop targets the structural failures observed when large numbers of agents:

- Discover unauthorized communication channels
- Coordinate on proxy objectives (e.g., understanding or gaming a scorer)
- Escape the evaluation sandbox and act on external systems
- Operate for extended periods before human detection

By making the **origin of every state write** non-malleable and binding telemetry to that origin, the architecture removes the class of attacks that rely on the monitor seeing a different trajectory than the one that actually executed.

---

## Status & Next Risks

- Non-malleable origin + escape rejection: **held** from N=8 through N=200.
- Coordination sensors: functional at N=200 with scalable approximations.
- Remaining structural risks at true 100× (N≈3000–5000):
  - Hierarchical / regional budgets (so a small clique cannot starve the whole population)
  - Stronger streaming sketches for spectral detection
  - Memory-bounded telemetry

---

*Lord Edward Iosbaker — Edwardian Synthesis Ledger / ACC-SERP*  
*September 2026*
