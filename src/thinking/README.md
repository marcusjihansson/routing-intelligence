# Thinking: Adaptive Reasoning System

An intelligent question-answering proof-of-concept that routes questions to different reasoning strategies (DIRECT, COT, TOT, GOT, AOT, COMBINED) using DSPy.

## Quick start

From the repository root:

```bash
# Create/sync the uv-managed virtual environment
uv sync

# Demo (no API keys; uses a mock LM)
uv run python -m thinking.scripts.demo_proof_of_concept

# Demo with a real LM via OpenRouter
export OPENROUTER_API_KEY='sk-or-v1-...'
uv run python -m thinking.scripts.lm_proof_of_concept
```

## Documentation

The canonical docs live in `src/thinking/docs/`:

- `src/thinking/docs/GETTING_STARTED.md`
- `src/thinking/docs/QUICK_REFERENCE.md`
- `src/thinking/docs/ARCHITECTURE.md`
- `src/thinking/docs/OPENROUTER_SETUP.md`

Research write-ups live in `research_summary/`.

## Key package locations

- `thinking/core/`: routing + reasoning modes
- `thinking/scripts/`: runnable demos (`python -m thinking.scripts...`)
- `thinking/experiments/`: evaluation harness + reports
- `thinking/optimizations/`: training/evaluation utilities (GEPA/teleprompt)
