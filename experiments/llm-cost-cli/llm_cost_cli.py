"""
llm-cost-cli: estimate request cost across LLM providers.

Usage:
  python llm_cost_cli.py --model gpt-4o --input 1000 --output 500
  python llm_cost_cli.py --list
  python llm_cost_cli.py --model claude --input 2000 --output 800  # fuzzy match
"""

import argparse
import sys
from dataclasses import dataclass
from typing import Optional

# Prices in USD per 1M tokens, as of mid-2025.
# Format: (input_price, output_price)
MODELS: dict[str, tuple[float, float]] = {
    # Anthropic
    "claude-opus-5":             (15.00,  75.00),
    "claude-sonnet-5":           ( 3.00,  15.00),
    "claude-haiku-4-5":          ( 0.80,   4.00),
    "claude-opus-4-8":           (15.00,  75.00),
    "claude-sonnet-4-6":         ( 3.00,  15.00),
    "claude-haiku-3-5":          ( 0.80,   4.00),
    # OpenAI
    "gpt-4o":                    ( 2.50,  10.00),
    "gpt-4o-mini":               ( 0.15,   0.60),
    "gpt-4-turbo":               (10.00,  30.00),
    "gpt-4":                     (30.00,  60.00),
    "gpt-3.5-turbo":             ( 0.50,   1.50),
    "o3":                        (10.00,  40.00),
    "o3-mini":                   ( 1.10,   4.40),
    "o1":                        (15.00,  60.00),
    "o1-mini":                   ( 3.00,  12.00),
    "o4-mini":                   ( 1.10,   4.40),
    # Google
    "gemini-2.0-flash":          ( 0.10,   0.40),
    "gemini-2.5-flash":          ( 0.30,   2.50),
    "gemini-2.5-pro":            ( 1.25,  10.00),
    "gemini-1.5-pro":            ( 1.25,   5.00),
    "gemini-1.5-flash":          ( 0.075,  0.30),
    # Meta (via inference providers, typical rates)
    "llama-3.1-8b":              ( 0.10,   0.10),
    "llama-3.1-70b":             ( 0.52,   0.75),
    "llama-3.1-405b":            ( 3.00,   3.00),
    "llama-3.3-70b":             ( 0.59,   0.79),
    # Mistral
    "mistral-large":             ( 2.00,   6.00),
    "mistral-small":             ( 0.20,   0.60),
    "mixtral-8x7b":              ( 0.24,   0.24),
    # Cohere
    "command-r-plus":            ( 2.50,  10.00),
    "command-r":                 ( 0.15,   0.60),
}


@dataclass
class CostResult:
    model: str
    input_tokens: int
    output_tokens: int
    input_cost: float
    output_cost: float

    @property
    def total_cost(self) -> float:
        return self.input_cost + self.output_cost

    def format(self, fmt: str = "text") -> str:
        if fmt == "csv":
            return (
                f"{self.model},{self.input_tokens},{self.output_tokens},"
                f"{self.input_cost:.6f},{self.output_cost:.6f},{self.total_cost:.6f}"
            )
        lines = [
            f"Model:          {self.model}",
            f"Input tokens:   {self.input_tokens:,}",
            f"Output tokens:  {self.output_tokens:,}",
            f"Input cost:     ${self.input_cost:.6f}",
            f"Output cost:    ${self.output_cost:.6f}",
            f"Total cost:     ${self.total_cost:.6f}",
        ]
        return "\n".join(lines)


def fuzzy_match(query: str) -> Optional[str]:
    """Return the best matching model name for a partial query."""
    q = query.lower()
    # Exact match first
    if q in MODELS:
        return q
    # Prefix match
    matches = [m for m in MODELS if m.startswith(q)]
    if len(matches) == 1:
        return matches[0]
    # Substring match
    matches = [m for m in MODELS if q in m]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        # Prefer shortest (most specific)
        return sorted(matches, key=len)[0]
    return None


def estimate(model: str, input_tokens: int, output_tokens: int) -> CostResult:
    """Compute cost for a single request."""
    resolved = fuzzy_match(model)
    if resolved is None:
        raise ValueError(
            f"Unknown model '{model}'. Run with --list to see available models."
        )
    in_price, out_price = MODELS[resolved]
    input_cost = (input_tokens / 1_000_000) * in_price
    output_cost = (output_tokens / 1_000_000) * out_price
    return CostResult(resolved, input_tokens, output_tokens, input_cost, output_cost)


def list_models() -> str:
    """Return a formatted table of all models and their prices."""
    header = f"{'Model':<30} {'Input $/1M':>12} {'Output $/1M':>12}"
    sep = "-" * len(header)
    rows = [header, sep]
    # Group roughly by provider prefix
    for name, (inp, out) in sorted(MODELS.items()):
        rows.append(f"{name:<30} {inp:>12.3f} {out:>12.3f}")
    return "\n".join(rows)


def compare_models(input_tokens: int, output_tokens: int) -> str:
    """Return a cost comparison table for all models, sorted by total cost."""
    results = [
        estimate(m, input_tokens, output_tokens) for m in MODELS
    ]
    results.sort(key=lambda r: r.total_cost)
    header = f"{'Model':<30} {'Input $':>12} {'Output $':>12} {'Total $':>12}"
    sep = "-" * len(header)
    rows = [header, sep]
    for r in results:
        rows.append(
            f"{r.model:<30} {r.input_cost:>12.6f} {r.output_cost:>12.6f} {r.total_cost:>12.6f}"
        )
    return "\n".join(rows)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Estimate LLM request cost across providers.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python llm_cost_cli.py --model gpt-4o --input 1000 --output 500
  python llm_cost_cli.py --model claude-sonnet --input 2000 --output 800
  python llm_cost_cli.py --list
  python llm_cost_cli.py --compare --input 1000 --output 500
  python llm_cost_cli.py --model gpt-4o --input 1000 --output 500 --format csv
        """,
    )
    parser.add_argument("--model", "-m", help="Model name (supports partial match)")
    parser.add_argument("--input", "-i", type=int, default=0,
                        dest="input_tokens", help="Input token count")
    parser.add_argument("--output", "-o", type=int, default=0,
                        dest="output_tokens", help="Output token count")
    parser.add_argument("--list", "-l", action="store_true",
                        help="List all models and prices")
    parser.add_argument("--compare", "-c", action="store_true",
                        help="Show cost for all models given --input and --output")
    parser.add_argument("--format", "-f", choices=["text", "csv"], default="text",
                        help="Output format (default: text)")

    args = parser.parse_args()

    if args.list:
        print(list_models())
        return

    if args.compare:
        if args.input_tokens == 0 and args.output_tokens == 0:
            parser.error("--compare requires --input and/or --output")
        print(compare_models(args.input_tokens, args.output_tokens))
        return

    if not args.model:
        parser.error("--model is required (or use --list / --compare)")

    if args.input_tokens < 0 or args.output_tokens < 0:
        parser.error("Token counts must be non-negative")

    try:
        result = estimate(args.model, args.input_tokens, args.output_tokens)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.format == "csv":
        print("model,input_tokens,output_tokens,input_cost,output_cost,total_cost")
    print(result.format(args.format))


if __name__ == "__main__":
    main()
