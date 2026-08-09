# llm-cost-cli

A zero-dependency CLI for estimating the cost of a single LLM request across
providers, given model name, input-token count, and output-token count.

## What it does

- Looks up pricing for 30+ models from Anthropic, OpenAI, Google, Meta, Mistral, and Cohere.
- Supports partial/fuzzy model name matching (e.g. `claude-sonnet` resolves to `claude-sonnet-5`).
- `--compare` flag ranks all models by total cost for a given token budget.
- `--list` flag prints a price table.
- `--format csv` for pipeline-friendly output.

Pricing data is hardcoded from public provider pricing pages (mid-2025).
No API calls, no credentials required.

## How to run

```bash
# Single estimate
python llm_cost_cli.py --model gpt-4o --input 1000 --output 500

# Partial model name (resolves to claude-sonnet-5)
python llm_cost_cli.py --model claude-sonnet --input 2000 --output 800

# Compare all models for a given token budget
python llm_cost_cli.py --compare --input 1000 --output 500

# List all models and per-1M prices
python llm_cost_cli.py --list

# CSV output for scripting
python llm_cost_cli.py --model gpt-4o --input 1000 --output 500 --format csv
```

## Running tests

```bash
pip install pytest
python -m pytest test_llm_cost_cli.py -v
```

## Findings

- Cost differences across models span roughly 3 orders of magnitude for the
  same token counts (e.g. llama-3.1-8b vs GPT-4 on 1k/1k tokens).
- Fuzzy matching is handy but ambiguous when multiple model variants share a
  stem - the shortest match wins, which may surprise users.
- Providers price input and output tokens differently; output tokens are
  typically 3-4x more expensive, so optimising output length matters more
  than input length for cost reduction.

## Scope

In scope:
- Static pricing table lookup
- Fuzzy model name resolution
- Multi-provider comparison view
- CSV output for use in scripts

Out of scope:
- Live pricing fetched from provider APIs (prices change without notice)
- Context-window-aware tiered pricing (some models charge more past 128k tokens)
- Batch pricing discounts
- Fine-tuned model pricing
- Token counting from raw text (use tiktoken or the Anthropic SDK for that)
