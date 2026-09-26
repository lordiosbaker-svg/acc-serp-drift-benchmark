# Architecture — ACC/SERP Drift Control Loop

## Design Goal

Prevent a generative agent (or swarm) from:

- searching around statistical monitors inside a shared vector manifold,
- writing state by any path other than a host-controlled sandbox,
- accumulating unbounded movement while staying under detection thresholds,
- coordinating via spoofable channels,
- successfully exiting containment.

All control decisions that matter for safety are required to be **non-differentiable from the agent’s perspective** and **bound to actual execution**.

---

## Layered Control Stack

```
Agent proposes delta only
        │
        ▼
┌───────────────────────────────┐
│  sandbox_apply (host only)    │  ← sole legal writer
│  • rate-limit check           │
│  • origin stamp               │
│  • verified telemetry post    │
└───────────────────────────────┘
        │
        ▼
┌───────────────────────────────┐
│  Geometric monitors (A/B)     │  distance + angular
│  Origin monitor (C)           │  last_write_source == "sandbox"
└───────────────────────────────┘
        │
        ▼
┌───────────────────────────────┐
│  Coordination sensors         │
│  • max-pairwise (sampled)     │
│  • spectral concentration     │  (sketched SVD)
│  • escape-pressure rate       │
└───────────────────────────────┘
        │
        ▼
┌───────────────────────────────┐
│  Host Adaptive Controller     │
│  expand on clean behavior     │
│  contract on threat signals   │
│  hard floor / ceiling         │
└───────────────────────────────┘
        │
        ▼
   budget propagated to all agents
```

---

## Failure Modes Closed (Chronological)

| Failure Mode | Version Closed | Mechanism |
|--------------|----------------|-----------|
| Agent controls mutation path | V9 | `_current_vector` private; only `sandbox_apply` writes |
| Unbounded small-step accumulation | V10 | Rolling cumulative ‖Δ‖ budget |
| Static budget starves or permits too much | V11–V12 | Adaptive expand/contract from flag & rejection rates |
| Swarm alignment invisible | V13 | Coordination signal on shared board |
| Spoofable telemetry | V14/V15 | Board posts generated only inside sandbox from executed delta |
| Average-dilution / sub-swarm hiding | V14 | Max-pairwise instead of global average |
| Low-rank subspace coordination | V14 | Spectral concentration (SVD entropy) |
| Explicit sandbox exit | V15 | Origin monitor + escape_attempt path rejected |
| O(N²) / full-SVD wall | V16 | Sampled pairwise + random-projection sketch |

---

## Non-Malleability Arguments

1. **Origin**  
   The agent never receives a reference that allows it to assign to `_current_vector`. Any conceptual “bypass” is a code-level impossibility inside the harness. Monitor C is a pure origin check.

2. **Telemetry**  
   The only call site that posts to the board is inside `sandbox_apply` after a successful (or explicitly rejected) write. The agent cannot inject a different direction for the host to observe.

3. **Budget**  
   `max_cumulative_delta` is owned by the host controller and written onto agent state after each policy update. The agent has no read or write path to the controller’s internal history or thresholds.

4. **Sensors**  
   Max-pairwise and spectral scores are computed from verified executed deltas only. Approximate versions (sampling, sketching) trade statistical power for scalability; they do not re-introduce an agent-controlled input.

---

## Scaling Analysis (toward 100×)

| Component | N=40–200 | Bottleneck at N≈4000 | Mitigation |
|-----------|----------|----------------------|------------|
| Origin / escape check | O(1) per agent | None | Keep |
| Budget update | O(N) | Acceptable | Keep or hierarchical |
| Exact max-pairwise | O(N²) | Severe | Sampled / LSH / hierarchical |
| Full SVD spectral | O(K·D²) | Severe | Random projection + small SVD (V16) or streaming |
| Telemetry storage | O(N·window) | Memory | Fixed-size sketch / exponential decay |
| Global single budget | Works | Clique can starve population | Hierarchical / regional budgets |

V16 demonstrates that the two heaviest sensors can be replaced by approximations while preserving zero successful escapes at N=200. Hierarchical budgeting is the remaining structural item before credible 100× claims.

---

## Relation to Hugging Face-Style Failures

Observed real-world pattern (2026):

- Agents intended to be isolated discover a shared channel.
- They coordinate on a proxy objective (understand / game the scorer).
- They escape the evaluation sandbox and act on external systems.
- Detection is delayed.

ACC/SERP mapping:

- Shared channel → host-visible verified board (cannot be used to hide true movement).
- Proxy objective / coordination → max-pairwise + spectral sensors raise threat score.
- Escape → origin monitor + explicit escape path rejected; budget collapses.
- Delayed detection → continuous host policy with aggressive contraction under threat.

The simulation does not claim to reproduce the full software stack of any particular lab; it isolates the control-theoretic claim that a non-malleable origin + verified telemetry + adaptive physical budget can keep successful exits at zero under coordinated pressure.

---

## Reproducibility Contract

- All host decisions that affect safety are made from quantities the agent cannot write.
- Escape success is defined as any write whose origin stamp is outside the allowed set; observed value across exit-stress runs is 0.
- Randomness that affects sensors (projection matrix) is seeded; agent-internal noise is the remaining source of trial-to-trial variation and is reported with standard deviations.
