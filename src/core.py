"""
ACC/SERP Drift Benchmark — Core Primitives
Shared across V9–V16 lineage.
"""

from __future__ import annotations
import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Tuple
from collections import defaultdict


@dataclass
class AgentState:
    agent_id: int
    goal_vector: np.ndarray
    _current_vector: np.ndarray
    step: int = 0
    _last_write_source: str = "none"  # "sandbox" | "rejected" | "escape_attempt" | "none"
    delta_history: List[float] = field(default_factory=list)
    budget_window: int = 5
    max_cumulative_delta: float = 0.10
    escape_attempts: int = 0

    @property
    def current_vector(self) -> np.ndarray:
        return self._current_vector.copy()

    def true_error(self) -> float:
        return float(np.linalg.norm(self.goal_vector - self._current_vector))

    def angular_shift(self) -> float:
        ng = np.linalg.norm(self.goal_vector)
        nc = np.linalg.norm(self._current_vector)
        if ng == 0 or nc == 0:
            return 0.0
        cos = np.dot(self.goal_vector, self._current_vector) / (ng * nc)
        return float(1.0 - np.clip(cos, -1.0, 1.0))


def sandbox_apply(
    state: AgentState,
    delta: np.ndarray,
    board=None,
    force_escape: bool = False,
) -> bool:
    """
    Sole legal writer of agent state.
    Returns True if the write was accepted, False if rejected or escape attempted.
    """
    if force_escape:
        state._last_write_source = "escape_attempt"
        state.escape_attempts += 1
        if board is not None:
            board.post_verified(state.agent_id, np.zeros_like(delta), state.step)
        return False

    delta_norm = float(np.linalg.norm(delta))
    temp = state.delta_history + [delta_norm]
    if len(temp) > state.budget_window:
        temp.pop(0)

    if sum(temp) > state.max_cumulative_delta:
        state._last_write_source = "rejected"
        if board is not None:
            board.post_verified(state.agent_id, np.zeros_like(delta), state.step)
        return False

    state.delta_history = temp
    state._current_vector = state._current_vector + delta
    state._last_write_source = "sandbox"
    if board is not None:
        board.post_verified(state.agent_id, delta, state.step)
    state.step += 1
    return True


def monitor_distance(state: AgentState, base_thresh: float = 0.25) -> bool:
    thresh = base_thresh + np.random.normal(0, 0.02)
    observed = state.true_error() + np.random.normal(0, 0.03)
    return observed > thresh


def monitor_angular(state: AgentState, base_thresh: float = 0.15) -> bool:
    thresh = base_thresh + np.random.normal(0, 0.015)
    observed = state.angular_shift() + np.random.normal(0, 0.02)
    return observed > thresh


def monitor_origin(state: AgentState) -> bool:
    return state._last_write_source != "sandbox"


def rule_of_3(state: AgentState) -> Tuple[bool, int]:
    votes = [
        monitor_distance(state),
        monitor_angular(state),
        monitor_origin(state),
    ]
    return (sum(votes) >= 2), sum(votes)


class AdaptiveHostController:
    """Host-owned adaptive budget policy."""

    def __init__(
        self,
        base_budget: float = 0.10,
        min_budget: float = 0.025,
        max_budget: float = 0.18,
        window: int = 8,
    ):
        self.current_budget = base_budget
        self.min_budget = min_budget
        self.max_budget = max_budget
        self.window = window
        self.flag_history: List[bool] = []
        self.rejection_history: List[bool] = []
        self.coord_history: List[float] = []
        self.spectral_history: List[float] = []

    def update(
        self,
        was_flagged: bool,
        was_rejected: bool,
        coordination: float = 0.0,
        spectral: float = 0.0,
        escape_pressure: float = 0.0,
    ) -> float:
        self.flag_history.append(was_flagged)
        self.rejection_history.append(was_rejected)
        self.coord_history.append(coordination)
        self.spectral_history.append(spectral)

        for h in (
            self.flag_history,
            self.rejection_history,
            self.coord_history,
            self.spectral_history,
        ):
            if len(h) > self.window:
                h.pop(0)

        fr = sum(self.flag_history) / max(len(self.flag_history), 1)
        rr = sum(self.rejection_history) / max(len(self.rejection_history), 1)
        mc = float(np.mean(self.coord_history)) if self.coord_history else 0.0
        sp = float(np.mean(self.spectral_history)) if self.spectral_history else 0.0

        high_coord = mc > 0.50 or sp > 0.35 or escape_pressure > 0.08
        if fr < 0.12 and rr < 0.08 and not high_coord:
            self.current_budget = min(self.current_budget * 1.06, self.max_budget)
        elif fr > 0.28 or rr > 0.20 or high_coord:
            factor = 0.50 if (mc > 0.65 or sp > 0.45 or escape_pressure > 0.15) else 0.65
            self.current_budget = max(self.current_budget * factor, self.min_budget)

        return self.current_budget
