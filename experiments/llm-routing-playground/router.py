"""Cost/latency-aware router between two mock LLM backends."""

from dataclasses import dataclass, field
from typing import Literal
from backends import FastCheapBackend, SlowExpensiveBackend, BackendResponse


Strategy = Literal["cost", "latency", "quality", "balanced"]


@dataclass
class Request:
    input_tokens: int
    complexity: float        # 0.0 (trivial) to 1.0 (very hard)
    latency_budget_ms: float = 5000.0
    max_cost_usd: float = 0.10
    label: str = ""


@dataclass
class RoutingDecision:
    request: Request
    chosen_backend: str
    reason: str
    response: BackendResponse
    rejected_backend: str
    rejected_reason: str


@dataclass
class RouterConfig:
    strategy: Strategy = "balanced"
    # balanced: score = quality_weight*quality - cost_weight*norm_cost - latency_weight*norm_latency
    quality_weight: float = 0.5
    cost_weight: float = 0.3
    latency_weight: float = 0.2
    # Hard limits applied before scoring
    enforce_budget: bool = True
    enforce_latency: bool = True


class Router:
    def __init__(self, config: RouterConfig | None = None):
        self.config = config or RouterConfig()
        self._fast = FastCheapBackend()
        self._slow = SlowExpensiveBackend()
        self.history: list[RoutingDecision] = []

    def _simulate(self, backend, req: Request, seed: int) -> BackendResponse:
        return backend.call(req.input_tokens, req.complexity, seed=seed)

    def route(self, req: Request, seed: int = 42) -> RoutingDecision:
        cfg = self.config
        fast_resp = self._simulate(self._fast, req, seed)
        slow_resp = self._simulate(self._slow, req, seed)

        if cfg.strategy == "cost":
            chosen, rejected, reason, rej_reason = self._pick_cost(req, fast_resp, slow_resp)
        elif cfg.strategy == "latency":
            chosen, rejected, reason, rej_reason = self._pick_latency(req, fast_resp, slow_resp)
        elif cfg.strategy == "quality":
            chosen, rejected, reason, rej_reason = self._pick_quality(req, fast_resp, slow_resp)
        else:
            chosen, rejected, reason, rej_reason = self._pick_balanced(req, fast_resp, slow_resp, cfg)

        decision = RoutingDecision(req, chosen.backend_name, reason, chosen, rejected.backend_name, rej_reason)
        self.history.append(decision)
        return decision

    def _pick_cost(self, req, fast, slow):
        if fast.cost_usd <= slow.cost_usd:
            return fast, slow, "lowest cost", f"${slow.cost_usd:.4f} > ${fast.cost_usd:.4f}"
        return slow, fast, "lowest cost", f"${fast.cost_usd:.4f} > ${slow.cost_usd:.4f}"

    def _pick_latency(self, req, fast, slow):
        if fast.latency_ms <= slow.latency_ms:
            return fast, slow, "lowest latency", f"{slow.latency_ms:.0f}ms > {fast.latency_ms:.0f}ms"
        return slow, fast, "lowest latency", f"{fast.latency_ms:.0f}ms > {slow.latency_ms:.0f}ms"

    def _pick_quality(self, req, fast, slow):
        if slow.quality_score >= fast.quality_score:
            return slow, fast, "highest quality", f"q={slow.quality_score:.2f} vs q={fast.quality_score:.2f}"
        return fast, slow, "highest quality", f"q={fast.quality_score:.2f} vs q={slow.quality_score:.2f}"

    def _pick_balanced(self, req, fast, slow, cfg):
        max_cost = max(fast.cost_usd, slow.cost_usd) or 1e-9
        max_lat = max(fast.latency_ms, slow.latency_ms) or 1e-9

        def score(r: BackendResponse) -> float:
            budget_ok = not cfg.enforce_budget or r.cost_usd <= req.max_cost_usd
            latency_ok = not cfg.enforce_latency or r.latency_ms <= req.latency_budget_ms
            if not budget_ok or not latency_ok:
                return -1.0
            return (cfg.quality_weight * r.quality_score
                    - cfg.cost_weight * r.cost_usd / max_cost
                    - cfg.latency_weight * r.latency_ms / max_lat)

        fs, ss = score(fast), score(slow)
        if fs >= ss:
            reason = f"balanced score {fs:.3f} vs {ss:.3f}"
            rej = f"score {ss:.3f} < {fs:.3f}"
            return fast, slow, reason, rej
        reason = f"balanced score {ss:.3f} vs {fs:.3f}"
        rej = f"score {fs:.3f} < {ss:.3f}"
        return slow, fast, reason, rej
