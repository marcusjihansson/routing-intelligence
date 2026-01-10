# Optimizations (GEPA / teleprompt)

This package contains training + evaluation utilities for the reasoning modules and the routing classifier.

## Quick start

```bash
uv sync

# (Requires OpenRouter)
export OPENROUTER_API_KEY='sk-or-v1-...'

# Train a single module
uv run python -m thinking.optimizations.chain_of_thought.training --budget light --examples 20

# Evaluate a single module
uv run python -m thinking.optimizations.chain_of_thought.evaluation

# Orchestrated evaluation across all modules + a synthetic routing check
uv run python -m thinking.optimizations.orchestrators.evaluation_orchestrator
```

## Where to look

- `thinking/optimizations/{direct,chain_of_thought,tree_of_thoughts,graph_of_thoughts,atom_of_thoughts,combined}/`
  - `training.py` / `evaluation.py`
- `thinking/optimizations/shared/`
  - synthetic data generation, metrics, persistence
- `thinking/optimizations/orchestrators/`
  - one-shot train/eval entrypoints
- `thinking/optimizations/optimization/`
  - baseline-vs-optimized comparison helpers (`test_optimization.py`)

## Related docs

- `../docs/ARCHITECTURE.md`
- `../docs/GETTING_STARTED.md`
