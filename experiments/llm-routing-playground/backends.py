"""Mock LLM backends with simulated cost and latency profiles."""

import random
import time
from dataclasses import dataclass


@dataclass
class BackendResponse:
    backend_name: str
    output_tokens: int
    latency_ms: float
    cost_usd: float
    quality_score: float  # 0.0-1.0, simulated


class FastCheapBackend:
    """Fast, cheap backend - lower quality on complex tasks."""

    name = "fast-cheap"
    cost_per_1k_input = 0.0005   # $0.50 / 1M tokens
    cost_per_1k_output = 0.0015
    base_latency_ms = 120
    latency_jitter_ms = 40
    quality_on_simple = 0.92
    quality_on_complex = 0.61

    def call(self, input_tokens: int, complexity: float, seed: int = 0) -> BackendResponse:
        rng = random.Random(seed)
        output_tokens = max(10, int(input_tokens * rng.uniform(0.4, 0.9)))
        latency = self.base_latency_ms + rng.uniform(0, self.latency_jitter_ms)
        latency += input_tokens * 0.05
        cost = (input_tokens / 1000) * self.cost_per_1k_input + \
               (output_tokens / 1000) * self.cost_per_1k_output
        quality = self.quality_on_simple + complexity * (self.quality_on_complex - self.quality_on_simple)
        quality = max(0.0, min(1.0, quality + rng.uniform(-0.05, 0.05)))
        return BackendResponse(self.name, output_tokens, latency, cost, quality)


class SlowExpensiveBackend:
    """Slow, expensive backend - consistently high quality."""

    name = "slow-expensive"
    cost_per_1k_input = 0.015    # $15 / 1M tokens
    cost_per_1k_output = 0.075
    base_latency_ms = 1800
    latency_jitter_ms = 400
    quality_on_simple = 0.97
    quality_on_complex = 0.91

    def call(self, input_tokens: int, complexity: float, seed: int = 0) -> BackendResponse:
        rng = random.Random(seed)
        output_tokens = max(10, int(input_tokens * rng.uniform(0.6, 1.4)))
        latency = self.base_latency_ms + rng.uniform(0, self.latency_jitter_ms)
        latency += input_tokens * 0.4
        cost = (input_tokens / 1000) * self.cost_per_1k_input + \
               (output_tokens / 1000) * self.cost_per_1k_output
        quality = self.quality_on_simple + complexity * (self.quality_on_complex - self.quality_on_simple)
        quality = max(0.0, min(1.0, quality + rng.uniform(-0.03, 0.03)))
        return BackendResponse(self.name, output_tokens, latency, cost, quality)
