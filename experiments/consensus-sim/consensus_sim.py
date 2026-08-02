"""
consensus_sim.py - Minimal multi-agent Byzantine consensus simulator.

N agents each propose a binary value (0 or 1). f of them are Byzantine
and may send different values to different peers. Honest agents decide by
majority rule after one broadcast round.

Key result demonstrated:
  - Single-round majority gives validity (when all honest start equal) for n > 2f.
  - Full agreement among split-valued honest agents is NOT guaranteed even with
    n > 3f; proper BFT needs f+1 relay rounds (Lamport-Shostak-Pease 1982).
"""

import random
import argparse
from collections import Counter
from dataclasses import dataclass


@dataclass
class Agent:
    id: int
    value: int
    byzantine: bool = False


class ConsensusSim:
    """Single-round broadcast with majority-rule decision."""

    def __init__(self, n: int, f: int, seed: int = 42):
        if n < 1:
            raise ValueError("Need at least 1 agent")
        if f < 0 or f >= n:
            raise ValueError(f"f must satisfy 0 <= f < n, got f={f}, n={n}")
        self.n = n
        self.f = f
        rng = random.Random(seed)
        byz_ids = set(rng.sample(range(n), f))
        self.agents = [
            Agent(id=i, value=rng.randint(0, 1), byzantine=(i in byz_ids))
            for i in range(n)
        ]
        self._rng = rng

    def run(self, adversary: str = "adaptive") -> dict:
        """
        Run one round and return results.

        adversary controls how Byzantine senders pick the value sent to
        each individual recipient:
          "adaptive" - sends 0 to even-id recipients, 1 to odd-id recipients
                       (maximises split potential regardless of honest values)
          "random"   - independent random bit per (sender, recipient)
          "collude1" - all Byzantine agents uniformly send 1
        """
        received = {a.id: {} for a in self.agents}

        for sender in self.agents:
            for receiver in self.agents:
                if not sender.byzantine:
                    val = sender.value
                elif adversary == "collude1":
                    val = 1
                elif adversary == "adaptive":
                    val = receiver.id % 2
                else:
                    val = self._rng.randint(0, 1)
                received[receiver.id][sender.id] = val

        decisions = {}
        for agent in self.agents:
            c = Counter(received[agent.id].values())
            top = c.most_common()
            # Deterministic tie-break: lower value wins
            if len(top) > 1 and top[0][1] == top[1][1]:
                decisions[agent.id] = min(top[0][0], top[1][0])
            else:
                decisions[agent.id] = top[0][0]

        honest_ids = {a.id for a in self.agents if not a.byzantine}
        honest_dec = {aid: decisions[aid] for aid in honest_ids}
        agreed = len(set(honest_dec.values())) == 1

        return {
            "n": self.n,
            "f": self.f,
            "agreed": agreed,
            "consensus_value": next(iter(honest_dec.values())) if agreed else None,
            "honest_initial": {a.id: a.value for a in self.agents if not a.byzantine},
            "honest_decisions": honest_dec,
            "bft_threshold_met": self.n > 3 * self.f,
        }


def run_sweep(max_n: int = 12, trials: int = 100, adversary: str = "adaptive") -> list:
    """Sweep all (n, f) pairs and record agreement rate over many seeds."""
    rows = []
    for n in range(1, max_n + 1):
        for f in range(n):
            hits = sum(
                ConsensusSim(n, f, seed=s).run(adversary)["agreed"]
                for s in range(trials)
            )
            rows.append({
                "n": n,
                "f": f,
                "agreement_rate": hits / trials,
                "bft_ok": n > 3 * f,
            })
    return rows


def main() -> None:
    ap = argparse.ArgumentParser(description="Byzantine consensus simulator")
    sub = ap.add_subparsers(dest="cmd", required=True)

    rp = sub.add_parser("run", help="Single consensus round")
    rp.add_argument("-n", type=int, default=7, metavar="N",
                    help="Total number of agents (default: 7)")
    rp.add_argument("-f", type=int, default=2, metavar="F",
                    help="Byzantine agents (default: 2)")
    rp.add_argument("--seed", type=int, default=42)
    rp.add_argument("--adversary", choices=["adaptive", "random", "collude1"],
                    default="adaptive")

    sp = sub.add_parser("sweep", help="Sweep n/f combinations and print agreement rates")
    sp.add_argument("--max-n", type=int, default=10)
    sp.add_argument("--trials", type=int, default=100)
    sp.add_argument("--adversary", choices=["adaptive", "random", "collude1"],
                    default="adaptive")

    args = ap.parse_args()

    if args.cmd == "run":
        r = ConsensusSim(args.n, args.f, seed=args.seed).run(adversary=args.adversary)
        print(f"n={r['n']}, f={r['f']}, BFT threshold (n > 3f): {r['bft_threshold_met']}")
        print(f"Initial values : {r['honest_initial']}")
        print(f"Final decisions: {r['honest_decisions']}")
        print(f"Agreed: {r['agreed']}  |  Value: {r['consensus_value']}")
    else:
        rows = run_sweep(max_n=args.max_n, trials=args.trials, adversary=args.adversary)
        print(f"{'n':>3}  {'f':>3}  {'n>3f':>6}  {'agree%':>8}")
        print("-" * 28)
        for r in rows:
            print(f"{r['n']:>3}  {r['f']:>3}  {str(r['bft_ok']):>6}  {r['agreement_rate']:>7.0%}")


if __name__ == "__main__":
    main()
