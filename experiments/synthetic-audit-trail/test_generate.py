import json
import io
from datetime import datetime, timezone

import pytest

from generate import AuditTrailGenerator, AuditEvent, EVENT_WEIGHTS, main


def test_event_count():
    gen = AuditTrailGenerator(seed=42)
    events = list(gen.generate(50))
    assert len(events) == 50


def test_required_fields_non_null():
    gen = AuditTrailGenerator(seed=0)
    for ev in gen.generate(30):
        assert ev.event_id
        assert ev.event_type
        assert ev.timestamp
        assert ev.user_id
        assert ev.model_id
        assert ev.latency_ms > 0


def test_event_types_are_valid():
    gen = AuditTrailGenerator(seed=1)
    for ev in gen.generate(100):
        assert ev.event_type in EVENT_WEIGHTS


def test_reproducible_with_seed():
    gen_a = AuditTrailGenerator(seed=99)
    gen_b = AuditTrailGenerator(seed=99)
    ids_a = [ev.event_id for ev in gen_a.generate(20)]
    ids_b = [ev.event_id for ev in gen_b.generate(20)]
    assert ids_a == ids_b


def test_anomaly_rate_respected():
    gen = AuditTrailGenerator(seed=7, anomaly_rate=1.0)
    events = list(gen.generate(20))
    assert all(ev.anomaly for ev in events)

    gen_zero = AuditTrailGenerator(seed=7, anomaly_rate=0.0)
    events_zero = list(gen_zero.generate(200))
    assert not any(ev.anomaly for ev in events_zero)
