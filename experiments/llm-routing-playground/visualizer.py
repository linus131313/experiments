"""ASCII visualizer for routing decisions."""

from router import RoutingDecision


_COLS = ("Request", "Complexity", "Tokens", "Chosen", "Reason", "Cost($)", "Lat(ms)", "Quality")
_W = (18, 10, 7, 14, 34, 8, 8, 7)


def _row(*cells) -> str:
    return "  ".join(str(c).ljust(w) for c, w in zip(cells, _W))


def print_decision_table(decisions: list[RoutingDecision]) -> None:
    header = _row(*_COLS)
    sep = "-" * len(header)
    print(sep)
    print(header)
    print(sep)
    for d in decisions:
        r = d.request
        resp = d.response
        label = (r.label or f"{r.input_tokens}t")[:18]
        complexity = f"{'*' * round(r.complexity * 5):5s} {r.complexity:.1f}"
        print(_row(
            label,
            complexity,
            r.input_tokens,
            d.chosen_backend,
            d.reason[:34],
            f"{resp.cost_usd:.5f}",
            f"{resp.latency_ms:.0f}",
            f"{resp.quality_score:.2f}",
        ))
    print(sep)


def print_summary(decisions: list[RoutingDecision]) -> None:
    if not decisions:
        return
    fast_count = sum(1 for d in decisions if d.chosen_backend == "fast-cheap")
    slow_count = len(decisions) - fast_count
    total_cost = sum(d.response.cost_usd for d in decisions)
    avg_quality = sum(d.response.quality_score for d in decisions) / len(decisions)
    avg_latency = sum(d.response.latency_ms for d in decisions) / len(decisions)

    baseline_cost = sum(d.response.cost_usd for d in decisions if d.chosen_backend != "fast-cheap")
    counterfactual = sum(
        SlowExpensiveSim.estimate_cost(d.request) for d in decisions if d.chosen_backend == "fast-cheap"
    )

    print("\n  Summary")
    print(f"  Total requests : {len(decisions)}")
    print(f"  fast-cheap     : {fast_count}  ({100*fast_count//len(decisions)}%)")
    print(f"  slow-expensive : {slow_count}  ({100*slow_count//len(decisions)}%)")
    print(f"  Total cost     : ${total_cost:.4f}")
    print(f"  Avg quality    : {avg_quality:.3f}")
    print(f"  Avg latency    : {avg_latency:.0f} ms")
    _bar_chart(decisions)


class SlowExpensiveSim:
    @staticmethod
    def estimate_cost(req) -> float:
        out = req.input_tokens * 0.7
        return (req.input_tokens / 1000) * 0.015 + (out / 1000) * 0.075


def _bar_chart(decisions: list[RoutingDecision]) -> None:
    print("\n  Routing decisions by complexity bucket")
    buckets = {"0.0-0.2": [0, 0], "0.2-0.4": [0, 0], "0.4-0.6": [0, 0],
               "0.6-0.8": [0, 0], "0.8-1.0": [0, 0]}
    edges = [0.2, 0.4, 0.6, 0.8, 1.01]
    keys = list(buckets.keys())
    for d in decisions:
        c = d.request.complexity
        for i, e in enumerate(edges):
            if c < e:
                if d.chosen_backend == "fast-cheap":
                    buckets[keys[i]][0] += 1
                else:
                    buckets[keys[i]][1] += 1
                break
    for label, (f, s) in buckets.items():
        bar_f = "#" * f
        bar_s = "=" * s
        print(f"  {label}  fast[{bar_f:<6}] slow[{bar_s:<6}]  (f={f} s={s})")
