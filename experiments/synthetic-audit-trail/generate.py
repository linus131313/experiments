#!/usr/bin/env python3
"""
Synthetic AI system audit trail generator.
Produces realistic JSONL or CSV audit events for compliance-tool testing.
"""
import argparse
import csv
import json
import math
import random
import sys
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

MODELS = [
    "claude-sonnet-4-6",
    "claude-opus-4-7",
    "claude-haiku-4-5",
    "gpt-4o",
    "gpt-4o-mini",
]

TOOLS = [
    "web_search",
    "code_executor",
    "file_read",
    "file_write",
    "database_query",
    "api_call",
    "calculator",
]

ERROR_CODES = [
    "RATE_LIMIT_EXCEEDED",
    "CONTEXT_LENGTH_EXCEEDED",
    "MODEL_UNAVAILABLE",
    "POLICY_VIOLATION",
    "TIMEOUT",
]

EVENT_WEIGHTS = {
    "inference_request": 0.50,
    "tool_invocation": 0.25,
    "policy_check": 0.15,
    "content_filter": 0.07,
    "error": 0.03,
}

RISK_WEIGHTS = {"low": 0.60, "medium": 0.30, "high": 0.10}


@dataclass
class AuditEvent:
    event_id: str
    event_type: str
    timestamp: str
    session_id: str
    user_id: str
    model_id: str
    latency_ms: float
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    policy_result: Optional[str] = None
    risk_tier: Optional[str] = None
    tool_name: Optional[str] = None
    error_code: Optional[str] = None
    anomaly: bool = False


def _weighted_choice(rng: random.Random, choices: dict) -> str:
    keys = list(choices.keys())
    weights = list(choices.values())
    return rng.choices(keys, weights=weights, k=1)[0]


def _lognormal(rng: random.Random, mean_ms: float, sigma: float = 0.5) -> float:
    mu = math.log(mean_ms) - 0.5 * sigma ** 2
    return round(math.exp(rng.gauss(mu, sigma)), 1)


class AuditTrailGenerator:
    def __init__(self, seed: Optional[int] = None, anomaly_rate: float = 0.02):
        self.rng = random.Random(seed)
        self.anomaly_rate = anomaly_rate
        # Pre-generate a pool of users and sessions for realistic co-occurrence.
        self._users = [
            "user_" + uuid.UUID(int=self.rng.randint(0, 2 ** 128)).hex[:12]
            for _ in range(50)
        ]
        self._sessions = [
            str(uuid.UUID(int=self.rng.randint(0, 2 ** 128)))
            for _ in range(200)
        ]

    def _make_event(self, base_time: datetime) -> AuditEvent:
        rng = self.rng
        event_type = _weighted_choice(rng, EVENT_WEIGHTS)
        is_anomaly = rng.random() < self.anomaly_rate

        base_latency = 800.0 if event_type == "inference_request" else 120.0
        if is_anomaly:
            base_latency *= rng.uniform(5.0, 20.0)

        ts = (
            base_time + timedelta(milliseconds=rng.randint(0, 60_000))
        ).isoformat()

        ev = AuditEvent(
            event_id=str(uuid.UUID(int=rng.randint(0, 2 ** 128))),
            event_type=event_type,
            timestamp=ts,
            session_id=rng.choice(self._sessions),
            user_id=rng.choice(self._users),
            model_id=rng.choice(MODELS),
            latency_ms=_lognormal(rng, base_latency),
            anomaly=is_anomaly,
        )

        if event_type == "inference_request":
            ev.input_tokens = rng.randint(50, 4096)
            ev.output_tokens = rng.randint(20, 2048)
            ev.risk_tier = _weighted_choice(rng, RISK_WEIGHTS)
            ev.policy_result = _weighted_choice(
                rng, {"allowed": 0.88, "flagged": 0.08, "denied": 0.04}
            )
        elif event_type == "tool_invocation":
            ev.tool_name = rng.choice(TOOLS)
            ev.input_tokens = rng.randint(10, 512)
        elif event_type == "policy_check":
            ev.policy_result = _weighted_choice(
                rng, {"allowed": 0.80, "flagged": 0.12, "denied": 0.08}
            )
            ev.risk_tier = _weighted_choice(rng, RISK_WEIGHTS)
        elif event_type == "content_filter":
            ev.policy_result = _weighted_choice(
                rng, {"allowed": 0.75, "flagged": 0.15, "denied": 0.10}
            )
        elif event_type == "error":
            ev.error_code = rng.choice(ERROR_CODES)

        return ev

    def generate(
        self,
        count: int,
        start_time: Optional[datetime] = None,
    ):
        if start_time is None:
            start_time = datetime.now(timezone.utc) - timedelta(hours=24)
        window_s = 86_400.0
        for _ in range(count):
            offset = timedelta(seconds=self.rng.uniform(0, window_s))
            yield self._make_event(start_time + offset)


def _serialize(event: AuditEvent) -> dict:
    return {k: v for k, v in asdict(event).items() if v is not None}


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Generate synthetic AI audit trail events"
    )
    parser.add_argument(
        "-n", "--count", type=int, default=100, help="Number of events to generate"
    )
    parser.add_argument(
        "-o", "--output", default="-", help="Output file path (- for stdout)"
    )
    parser.add_argument("--seed", type=int, default=None, help="Random seed")
    parser.add_argument(
        "--anomaly-rate",
        type=float,
        default=0.02,
        help="Fraction of events flagged as anomalies (0.0-1.0)",
    )
    parser.add_argument(
        "--format",
        choices=["jsonl", "csv"],
        default="jsonl",
        help="Output format",
    )
    args = parser.parse_args(argv)

    gen = AuditTrailGenerator(seed=args.seed, anomaly_rate=args.anomaly_rate)
    events = sorted(gen.generate(args.count), key=lambda e: e.timestamp)

    fh = open(args.output, "w", newline="") if args.output != "-" else sys.stdout
    try:
        if args.format == "jsonl":
            for ev in events:
                fh.write(json.dumps(_serialize(ev)) + "\n")
        else:
            fieldnames = list(asdict(events[0]).keys()) if events else []
            writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for ev in events:
                writer.writerow(asdict(ev))
    finally:
        if args.output != "-":
            fh.close()


if __name__ == "__main__":
    main()
