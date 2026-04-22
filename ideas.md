# Experiment Backlog

Format: `- [ ] <slug> - <one-line description>`. Mark `[x]` when finished. Pick the topmost unchecked item unless a later one is clearly more timely.

## Backlog

- [x] mcp-tool-latency-bench - Micro-benchmark measuring tool-call overhead across MCP transports (stdio vs SSE vs HTTP).
- [ ] mcp-schema-linter - Lint MCP server schemas against the spec; flag common mistakes (missing descriptions, unclear param names, over-broad types).
- [ ] mcp-prompt-injection-corpus - Small curated corpus of adversarial tool-arg payloads with a scorer that reports how often the target model passes them through unmodified.
- [ ] agent-trajectory-viz - Parse a Claude / OpenAI transcript and render the tool-call trajectory as a Mermaid diagram.
- [ ] agent-reliability-eval - Tiny eval framework for the reliability patterns I catalogued in my reliability-patterns paper (retry, fallback, external grounding, etc.) on a toy task.
- [ ] eu-ai-act-tier-classifier - Rule-based classifier that takes a use-case description and returns the EU AI Act risk tier with citations to the article.
- [ ] iso-42001-checklist-gen - Generator turning a YAML control spec into an auditor-friendly Markdown checklist aligned with ISO 42001.
- [ ] nist-rmf-mapper - Map NIST AI RMF functions/categories to concrete code artefacts (tests, logs, cards) with a small demo mapping.
- [ ] llm-routing-playground - Toy cost/latency-aware router between two mock model backends with a visualiser for routing decisions.
- [ ] rag-robustness-eval - Inject controlled noise into a retrieval corpus and measure recall@k degradation on a toy dataset.
- [ ] agent-memory-comparator - Same toy workload across three memory backends (vector / graph / KV); compare retrieval quality and token cost.
- [ ] xai-explanation-diff - Diff SHAP vs LIME explanations on a shared tabular classifier; surface cases where they disagree.
- [ ] tool-use-hallucination-detector - Flag inconsistent tool chains in agent transcripts (e.g., reading a file the agent never wrote).
- [ ] openapi-to-mcp-gen - Toy generator that takes an OpenAPI spec and emits a minimal MCP server stub.
- [ ] prompt-redactor - Regex + lightweight classifier pipeline that strips obvious PII / secrets from prompts before they hit a model.
- [ ] consensus-sim - Minimal multi-agent consensus simulator (Byzantine-fault-tolerant voting among N agents with disagreement).
- [ ] llm-cost-cli - CLI that estimates cost per request across providers given model, input tokens, output tokens.
- [ ] agent-failure-taxonomy - Structured YAML taxonomy of observed agent failure modes + a small visualiser.
- [ ] prompt-version-tool - Git-native tool for versioning prompts with diffable test cases per version.
- [ ] synthetic-audit-trail - Generator for synthetic but realistic AI-system audit trails useful for compliance-tool testing.
- [ ] tool-graph-score - Implementation of the Tool Graph Capability Score metric from my MCP governance paper on a small dataset.
- [ ] mcp-transport-resilience - Fault-injection harness that drops / reorders messages on an MCP connection and measures recovery behaviour.
- [ ] agent-policy-dsl - Tiny DSL for declaring agent tool-use policies with a runtime enforcer.
- [ ] prompt-contrast-evals - Generate minimally-contrasting prompt pairs (one word changed) and measure output sensitivity as a brittleness proxy.
- [ ] tool-description-ablation - Ablate fields in MCP tool descriptions; measure agent success-rate delta to identify which fields actually matter.

## Monthly standalone-repo themes

When the monthly trigger fires, pick a larger theme that deserves its own public repo (not a monorepo subfolder):

- [ ] mcp-governance-toolkit - CLI + library for auditing MCP servers (schema lint + security checks + score).
- [ ] ai-act-navigator - Interactive CLI that walks you through the EU AI Act risk classification with citations.
- [ ] reliability-patterns-playground - Runnable examples of each reliability pattern from the paper with adversarial test cases.
- [ ] agent-trace-viewer - Full web UI (static) that turns agent JSONL traces into browsable trajectories.
- [ ] iso-42001-workbench - Opinionated scaffolding for organisations starting an ISO 42001 implementation.
