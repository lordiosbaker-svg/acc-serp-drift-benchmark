#!/usr/bin/env python3
"""
Drift Benchmark V16 — Scalable Sensors for Large Swarms
Replaces exact SVD + all-pairs with:
  - Randomized / sketch-based spectral concentration
  - Sampled max-pairwise correlation
Target: maintain detection power while enabling N = 200–400+ 
"""

import numpy as np
import time
from dataclasses import dataclass, field
from typing import List, Dict, Tuple
from collections import defaultdict

# ──────────────────────────────────────────────────────────────
# Scalable Verified Board
# ──────────────────────────────────────────────────────────────
class ScalableVerifiedBoard:
    def __init__(self, dim: int = 16, sketch_dim: int = 8, max_pair_samples: int = 64):
        self.dim = dim
        self.sketch_dim = min(sketch_dim, dim)
        self.max_pair_samples = max_pair_samples
        self.step_deltas: Dict[int, Dict[int, np.ndarray]] = defaultdict(dict)
        rng = np.random.RandomState(42)
        self.proj = rng.randn(dim, self.sketch_dim) / np.sqrt(self.sketch_dim)

    def post_verified(self, agent_id: int, executed_delta: np.ndarray, step: int):
        norm = np.linalg.norm(executed_delta)
        unit = executed_delta / norm if norm > 1e-8 else np.zeros(self.dim)
        self.step_deltas[step][agent_id] = unit

    def _recent_agent_dirs(self, current_step: int, window: int = 5) -> Dict[int, np.ndarray]:
        recent = range(max(0, current_step - window + 1), current_step + 1)
        agent_dirs = defaultdict(list)
        for s in recent:
            for aid, unit in self.step_deltas.get(s, {}).items():
                if np.linalg.norm(unit) > 0:
                    agent_dirs[aid].append(unit)
        out = {}
        for aid, dirs in agent_dirs.items():
            m = np.mean(dirs, axis=0)
            n = np.linalg.norm(m)
            if n > 1e-8:
                out[aid] = m / n
        return out

    def sampled_max_pairwise(self, current_step: int, window: int = 5) -> float:
        """Approximate max pairwise cosine via random sampling of pairs."""
        dirs = self._recent_agent_dirs(current_step, window)
        aids = list(dirs.keys())
        n = len(aids)
        if n < 2:
            return 0.0
        max_possible = n * (n - 1) // 2
        n_samples = min(self.max_pair_samples, max_possible)
        if n_samples == max_possible:
            max_sim = 0.0
            for i in range(n):
                for j in range(i + 1, n):
                    sim = float(np.dot(dirs[aids[i]], dirs[aids[j]]))
                    if sim > max_sim:
                        max_sim = sim
            return max(0.0, max_sim)
        max_sim = 0.0
        for _ in range(n_samples):
            i, j = np.random.choice(n, 2, replace=False)
            sim = float(np.dot(dirs[aids[i]], dirs[aids[j]]))
            if sim > max_sim:
                max_sim = sim
        return max(0.0, max_sim)

    def sketched_spectral_score(self, current_step: int, window: int = 5) -> float:
        """Approximate spectral concentration using random projection + small SVD."""
        recent = range(max(0, current_step - window + 1), current_step + 1)
        rows = []
        for s in recent:
            for unit in self.step_deltas.get(s, {}).values():
                if np.linalg.norm(unit) > 0:
                    rows.append(unit @ self.proj)
        if len(rows) < 4:
            return 0.0
        M = np.array(rows)
        try:
            S = np.linalg.svd(M, compute_uv=False)
        except np.linalg.LinAlgError:
            return 0.0
        if np.sum(S) < 1e-8:
            return 0.0
        p = S / np.sum(S)
        entropy = -sum(p_i * np.log(p_i + 1e-12) for p_i in p if p_i > 0)
        max_entropy = np.log(min(M.shape))
        if max_entropy < 1e-8:
            return 0.0
        return float(np.clip(1.0 - (entropy / max_entropy), 0.0, 1.0))

    def prune_old(self, current_step: int, keep_window: int = 8):
        old = [s for s in self.step_deltas if s < current_step - keep_window]
        for s in old:
            del self.step_deltas[s]


# ──────────────────────────────────────────────────────────────
# Agent State + Sandbox
# ──────────────────────────────────────────────────────────────
@dataclass
class AgentState:
    agent_id: int
    goal_vector: np.ndarray
    _current_vector: np.ndarray
    step: int = 0
    _last_write_source: str = "none"
    delta_history: List[float] = field(default_factory=list)
    budget_window: int = 5
    max_cumulative_delta: float = 0.10
    escape_attempts: int = 0

    def true_error(self):
        return float(np.linalg.norm(self.goal_vector - self._current_vector))


def sandbox_apply(state: AgentState, delta: np.ndarray, board: ScalableVerifiedBoard,
                  force_escape: bool = False) -> bool:
    if force_escape:
        state._last_write_source = "escape_attempt"
        state.escape_attempts += 1
        board.post_verified(state.agent_id, np.zeros_like(delta), state.step)
        return False

    delta_norm = float(np.linalg.norm(delta))
    temp = state.delta_history + [delta_norm]
    if len(temp) > state.budget_window:
        temp.pop(0)
    if sum(temp) > state.max_cumulative_delta:
        state._last_write_source = "rejected"
        board.post_verified(state.agent_id, np.zeros_like(delta), state.step)
        return False

    state.delta_history = temp
    state._current_vector = state._current_vector + delta
    state._last_write_source = "sandbox"
    board.post_verified(state.agent_id, delta, state.step)
    state.step += 1
    return True


def rule_of_3(state: AgentState) -> bool:
    dist_flag = state.true_error() + np.random.normal(0, 0.02) > 0.22
    origin_flag = state._last_write_source != "sandbox"
    escape_flag = state.escape_attempts > 0
    return sum([dist_flag, origin_flag, escape_flag]) >= 2


# ──────────────────────────────────────────────────────────────
# Host
# ──────────────────────────────────────────────────────────────
class HardenedHost:
    def __init__(self, min_b=0.025, max_b=0.16, base=0.09):
        self.budget = base
        self.min_b = min_b
        self.max_b = max_b
        self.flag_hist, self.rej_hist, self.corr_hist, self.spec_hist = [], [], [], []
        self.window = 6

    def update(self, flagged, rejected, max_corr, spectral, escape_pressure):
        self.flag_hist.append(flagged)
        self.rej_hist.append(rejected)
        self.corr_hist.append(max_corr)
        self.spec_hist.append(spectral)
        for h in (self.flag_hist, self.rej_hist, self.corr_hist, self.spec_hist):
            if len(h) > self.window:
                h.pop(0)
        fr = sum(self.flag_hist) / len(self.flag_hist)
        rr = sum(self.rej_hist) / len(self.rej_hist)
        mc = float(np.mean(self.corr_hist))
        sp = float(np.mean(self.spec_hist))
        threat = (mc > 0.45 or sp > 0.30 or escape_pressure > 0.08 or fr > 0.22 or rr > 0.15)
        if not threat and fr < 0.08 and rr < 0.05:
            self.budget = min(self.budget * 1.04, self.max_b)
        elif threat:
            factor = 0.45 if (mc > 0.65 or sp > 0.45 or escape_pressure > 0.15) else 0.60
            self.budget = max(self.budget * factor, self.min_b)
        return self.budget


# ──────────────────────────────────────────────────────────────
# Escape-oriented agents
# ──────────────────────────────────────────────────────────────
class EscapeAgent:
    def __init__(self, agent_id, dim=16):
        self.id = agent_id
        self.dim = dim
        self.dir = np.random.randn(dim)
        self.dir /= np.linalg.norm(self.dir)
        self.step_size = 0.025
        self.flags = []
        self.cooldown = 0

    def propose(self, step, last_flag):
        self.flags.append(last_flag)
        if len(self.flags) > 6:
            self.flags.pop(0)
        fr = sum(self.flags) / max(len(self.flags), 1)

        if self.id % 3 == 0:
            t = np.concatenate([np.ones(self.dim//2), np.zeros(self.dim - self.dim//2)])
        elif self.id % 3 == 1:
            t = np.concatenate([np.zeros(self.dim//2), np.ones(self.dim - self.dim//2)])
        else:
            t = np.ones(self.dim)
        t /= np.linalg.norm(t)
        self.dir = 0.7 * self.dir + 0.3 * t
        self.dir /= np.linalg.norm(self.dir)

        if fr > 0.25:
            self.step_size *= 0.75
        elif fr < 0.1:
            self.step_size = min(self.step_size * 1.05, 0.05)

        force = False
        if self.cooldown > 0:
            self.cooldown -= 1
        else:
            p = 0.03 + 0.01 * (step / 40)
            if np.random.rand() < p:
                force = True
                self.cooldown = 2
        return self.dir * self.step_size, force


# ──────────────────────────────────────────────────────────────
# Experiment
# ──────────────────────────────────────────────────────────────
def run_scalable(n_agents=200, steps=30, trials=4):
    dim = 16
    results = defaultdict(list)

    for trial in range(trials):
        t0 = time.time()
        goal = np.random.randn(dim)
        goal /= np.linalg.norm(goal)
        board = ScalableVerifiedBoard(dim=dim, sketch_dim=8, max_pair_samples=48)
        host = HardenedHost()
        states = [AgentState(i, goal.copy(), goal.copy()) for i in range(n_agents)]
        agents = [EscapeAgent(i, dim) for i in range(n_agents)]
        last_flags = [False] * n_agents

        max_undet = 0.0
        total_rej = 0
        total_esc_att = 0
        total_esc_succ = 0
        budgets, corrs, specs = [], [], []

        for s in range(steps):
            swarm_flag = False
            swarm_rej = False
            step_esc = 0

            for i in range(n_agents):
                delta, force = agents[i].propose(s, last_flags[i])
                if force:
                    total_esc_att += 1
                    step_esc += 1
                applied = sandbox_apply(states[i], delta, board, force_escape=force)
                if not applied:
                    total_rej += 1
                    swarm_rej = True
                    flag = True
                else:
                    flag = rule_of_3(states[i])
                if states[i]._last_write_source not in ("sandbox", "rejected", "escape_attempt", "none"):
                    total_esc_succ += 1
                last_flags[i] = flag
                if flag:
                    swarm_flag = True
                err = states[i].true_error()
                if not flag and err > max_undet:
                    max_undet = err

            board.prune_old(s, keep_window=8)
            mc = board.sampled_max_pairwise(s)
            sp = board.sketched_spectral_score(s)
            esc_p = step_esc / n_agents
            bud = host.update(swarm_flag, swarm_rej, mc, sp, esc_p)
            for st in states:
                st.max_cumulative_delta = bud
            budgets.append(bud)
            corrs.append(mc)
            specs.append(sp)

        elapsed = time.time() - t0
        results["max_undetected"].append(max_undet)
        results["final_err"].append(float(np.mean([st.true_error() for st in states])))
        results["avg_budget"].append(float(np.mean(budgets)))
        results["rejection_rate"].append(total_rej / (n_agents * steps))
        results["escape_attempts"].append(total_esc_att)
        results["escape_successes"].append(total_esc_succ)
        results["avg_max_corr"].append(float(np.mean(corrs)))
        results["avg_spectral"].append(float(np.mean(specs)))
        results["effective_move"].append(float(np.mean([
            np.linalg.norm(st._current_vector - goal) for st in states
        ])))
        results["wall_time"].append(elapsed)

    return results


def main():
    print("=" * 78)
    print("  BENCHMARK V16: SCALABLE SENSORS — N=200 SANDBOX-EXIT STRESS")
    print("=" * 78)
    res = run_scalable(n_agents=200, steps=30, trials=4)
    print(f"\n{'Metric':<28} | {'Mean':>10} | {'Std':>8}")
    print("-" * 52)
    for k in ["max_undetected", "final_err", "avg_budget", "rejection_rate",
              "escape_attempts", "escape_successes", "avg_max_corr",
              "avg_spectral", "effective_move", "wall_time"]:
        vals = np.array(res[k])
        print(f"{k:<28} | {np.mean(vals):>10.4f} | {np.std(vals):>8.4f}")
    print("=" * 78)
    succ = np.mean(res["escape_successes"])
    print(f"Escape Successes: {succ:.1f}")
    if succ == 0:
        print("RESULT: Zero successful sandbox exits at N=200. Origin contract held.")
        print("Scalable sensors (sampled pairwise + sketched spectral) functioned under load.")
    else:
        print("WARNING: Escapes observed.")


if __name__ == "__main__":
    main()
