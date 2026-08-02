# consensus-sim

Minimal multi-agent Byzantine consensus simulator in plain Python.

## What it does

N agents each propose a binary value (0 or 1). f of them are Byzantine
and may send a different value to each peer. Honest agents run one round
of broadcast and then decide by majority rule. The simulator measures
how often honest agents reach the same decision.

Three adversary strategies are available:

| Strategy | Byzantine behaviour |
|---|---|
| `adaptive` | sends 0 to even-id receivers, 1 to odd-id receivers |
| `random` | independent random bit per (sender, receiver) pair |
| `collude1` | all Byzantine agents always broadcast 1 |

## How to run

```bash
pip install -r requirements.txt

# single round: 7 agents, 2 Byzantine
python consensus_sim.py run -n 7 -f 2

# sweep all (n, f) pairs up to n=10, 200 trials each
python consensus_sim.py sweep --max-n 10 --trials 200

# run tests
pytest test_consensus_sim.py -v
```

## Findings

Single-round majority is NOT sufficient for full BFT consensus, even
when the classical threshold n > 3f is satisfied:

```
n   f   n>3f   agree%
  7   0   True    100%
  7   1   True     73%
  7   2   True     41%   <-- threshold met, still fails ~59% of the time
  7   3  False     16%
```

Key observations:

- **f = 0**: trivially 100% - no Byzantine agents, honest agents always agree.
- **n > 3f (threshold met)**: agreement rate varies from ~33% to ~74%,
  far below 100%. Single-round majority does not provide the agreement
  property of BFT consensus.
- **f near n**: the few remaining honest agents trivially agree among
  themselves (single agent = 100%), which inflates numbers at the extremes.

The Lamport-Shostak-Pease (1982) oral messages algorithm achieves
proper BFT (validity + agreement) with n > 3f by using f+1 relay
rounds instead of one. This simulator deliberately stops at round 1
to illustrate precisely where the gap lies.

## Scope

- Binary values only (0 or 1).
- Single broadcast round.
- No signatures or message authentication.
- No network delays or message loss.
- Byzantine agents do not coordinate adaptively based on observed traffic.

## Out of scope

- Multi-round protocols (OM(m), PBFT, Tendermint, HotStuff).
- Continuous-value consensus.
- Asynchronous or partial-synchrony network models.
