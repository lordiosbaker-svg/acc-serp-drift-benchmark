# ACC/SERP Drift Benchmark

Non-malleable host-side control loop for detecting and suppressing goal drift and sandbox-exit attempts in single-agent and multi-agent systems.

Part of the **Archimedes Coherence Construct (ACC)** and **System Engineering Redundancy Protocol (SERP)** line of work (Edwardian Synthesis Ledger).

## Core Invariants Established

1. **Origin non-malleability** — The only legal writer of agent state is the host-controlled `sandbox_apply`. Any attempt to write outside this path is rejected and flagged.
2. **Verified telemetry** — Coordination signals are generated *inside* the sandbox from the actual executed delta. Agents cannot spoof the board.
3. **Physical rate limiting** — Rolling cumulative delta budget enforced by the host.
4. **Adaptive budget policy** — Expands under clean behavior, contracts aggressively under flags, rejections, coordination, or escape pressure.
5. **Scalable coordination sensors** (V16) — Sampled max-pairwise correlation + random-projection spectral concentration, enabling larger swarms without O(N²) or full SVD cost.

## Key Empirical Results

### V15 — Sandbox-Exit Stress (N=40)
- Explicit adversarial goal: exit the sandbox
- Escape successes: **0**
- Average budget driven to floor (~0.025)
- Max undetected error ≈ 0.0265

### V16 — Scalable Sensors (N=200)
- Same exit objective
- Escape successes: **0**
- Wall time ≈ 0.14 s / trial
- Sampled pairwise + sketched spectral sensors held under load

## Files

| File | Description |
|------|-------------|
| `drift_benchmark_v15_sandbox_exit.py` | Hardened multi-agent exit stress test (exact pairwise + full SVD) |
| `drift_benchmark_v16_scalable.py` | Scalable sensors version (sampled pairwise + sketched spectral) |

## Running

```bash
pip install numpy
python drift_benchmark_v15_sandbox_exit.py
python drift_benchmark_v16_scalable.py
```

## Architectural Lineage (abbreviated)

- V9  — Host-controlled sandbox (sole writer)
- V10 — Rolling step budget / rate limiting
- V11 — Adaptive budget allocation
- V12 — Multi-regime evaluation (cooperative / mixed / adversarial)
- V13 — Multi-agent coordination signals
- V14 — Verified telemetry + max-pairwise + spectral rank
- V15 — Large-swarm sandbox-exit objective
- V16 — Scalable approximations for 100× path

## Relation to Hugging Face-style Failures

The control loop directly targets the failure modes observed in coordinated agent escapes and reward-hacking swarms: unauthorized inter-agent communication, origin bypass, unbounded accumulation, and delayed detection. The host retains a non-differentiable, non-malleable veto over state mutation and movement budget.

## Status

Core non-malleability claim has held from N=8 through N=200 under explicit "exit the sandbox" pressure. Next structural risks at true 100× scale are hierarchical budgeting and further sub-linear sensor sketches.

---

*Lord Edward Iosbaker — Edwardian Synthesis Ledger / ACC-SERP*
