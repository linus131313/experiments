# Experiments

Small, focused experiments in **Agentic AI**, **Model Context Protocol (MCP)**, and **AI Governance**. Each subfolder is a self-contained prototype — code, a short README, and (where it makes sense) a reproducibility note. Nothing here is production software; the point is to probe an idea end-to-end without technical debt.

Topics cluster around my professional focus: multi-agent systems, MCP tool semantics, EU AI Act / ISO 42001 / NIST AI RMF tooling, and reliability patterns for LLM-based systems.

## Index

See [`ideas.md`](./ideas.md) for the running backlog and `experiments/` subfolders for completed work.

## Why a monorepo

Keeps the blast radius small. Each experiment lives in its own folder, has its own deps, and dies when it has served its purpose. No package registry, no semver, no issue backlog.

— Linus ([linus-teklenburg.de](https://www.linus-teklenburg.de))
