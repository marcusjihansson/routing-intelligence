# Adaptive Reasoning System

[https://github.com/marcusjohansson/routing-intelligence.git](https://github.com/marcusjohansson/routing-intelligence.git)

An intelligent question-answering system that routes questions to different reasoning strategies based on their characteristics (breadth and depth).

## Quick Start

```bash
# Install dependencies
uv sync

# Run demo (no API keys needed - uses mock LM)
uv run python -m thinking.scripts.demo_proof_of_concept

# Run with real LM via OpenRouter
export OPENROUTER_API_KEY='sk-or-v1-...'
uv run python -m thinking.scripts.lm_proof_of_concept
```

## Overview

This project focuses on **routing intelligence**—analyzing a question and selecting the optimal *reasoning strategy* for answering it. This is distinct from **model routing**, which routes questions to different model tiers based on cost.

### Key Distinction

| Aspect | Routing Intelligence | Model Routing |
|--------|---------------------|---------------|
| **What is routed** | Questions → Reasoning forms | Questions → Model tiers |
| **Basis for routing** | Question complexity (breadth/depth) | Question complexity + cost constraints |
| **Goal** | Match reasoning strategy to question type | Minimize cost while maintaining quality |

## Reasoning Modes

The system implements 6 reasoning modes:

| Mode | Description | Best For |
|------|-------------|----------|
| **DIRECT** | Single prediction | Simple factual questions |
| **COT** (Chain of Thought) | Step-by-step reasoning | Questions requiring logical steps |
| **TOT** (Tree of Thoughts) | Multiple interpretation paths | Ambiguous questions with multiple valid interpretations |
| **GoT** (Graph of Thoughts) | Interconnected concept analysis | Complex multi-domain queries |
| **AoT** (Atom of Thoughts) | First-principles decomposition | Technical troubleshooting, deep understanding |
| **COMBINED** | Multi-strategy synthesis | Complex problems requiring multiple approaches |

## Core Mechanism

```
Question → Breadth/Depth Analysis → Classifier → Reasoning Mode Selection → Answer
```

### Breadth Score
Does this question require information from multiple domains?

- Low: "What's my total revenue this month?"
- High: "How should I restructure my product categories for better SEO and easier inventory management?"

### Depth Score
Does this question require understanding underlying mechanisms?

- Low: "Show me my top 10 products"
- High: "Why is my inventory sync failing for this specific SKU?"

## Research Focus Areas

1. How well can AI classify questions by their reasoning needs?
2. Can thresholds improve routing robustness?
3. Does GEPA optimization improve classifier accuracy?

## Project Structure

```
src/thinking/
├── core/           # Routing + reasoning modes
├── scripts/        # Runnable demos (python -m thinking.scripts...)
├── experiments/    # Evaluation harness + reports
├── optimizations/  # Training/evaluation utilities (GEPA/teleprompt)
└── docs/           # Detailed documentation
```

## Documentation

- [Getting Started](src/thinking/docs/GETTING_STARTED.md)
- [Architecture](src/thinking/docs/ARCHITECTURE.md)
- [Quick Reference](src/thinking/docs/QUICK_REFERENCE.md)

### Shopify-Specific Documentation

For the Shopify Sidekick use case, see:
- [research_summary/Shopify/PROPOSAL.md](research_summary/Shopify/PROPOSAL.md) - Enhancement proposal
- [research_summary/Shopify/SHOPIFY.md](research_summary/Shopify/SHOPIFY.md) - Shopify-specific details
- [research_summary/Shopify/SHOPIFY_INTEGRATION.md](research_summary/Shopify/SHOPIFY_INTEGRATION.md) - Integration strategy

## Acknowledgments

This project draws on the public case study available at claude.com/customers/shopify.
