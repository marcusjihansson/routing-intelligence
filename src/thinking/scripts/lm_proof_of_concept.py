"""Demo: Adaptive Reasoning System with a real LM via OpenRouter.

Run:
  export OPENROUTER_API_KEY='sk-or-v1-...'
  python -m thinking.scripts.lm_proof_of_concept

Notes:
- Default model is `openrouter/openai/gpt-4o`.
- You can override with `--model`.
"""

from __future__ import annotations

import argparse
import os

import dspy

from thinking.core.dynamic_router import MultiStrategyRouter
from thinking.core.reasoning_router import AdaptiveReasoner


def configure_openrouter_lm(model: str = "openrouter/openai/gpt-4o") -> dspy.LM:
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENROUTER_API_KEY not set. Set it in your shell and re-run."
        )

    lm = dspy.LM(
        model=model,
        api_key=api_key,
        api_base="https://openrouter.ai/api/v1",
    )
    dspy.settings.configure(lm=lm)
    return lm


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model",
        default="openrouter/openai/gpt-4o",
        help="OpenRouter model name, e.g. openrouter/openai/gpt-4o",
    )
    args = parser.parse_args()

    try:
        configure_openrouter_lm(model=args.model)
    except Exception as e:
        print(f"Failed to configure LM: {e}")
        print("Set OPENROUTER_API_KEY and try again.")
        return

    reasoner = AdaptiveReasoner()
    router = MultiStrategyRouter(confidence_threshold=0.7)

    questions = [
        "What is the capital of Sweden?",
        "Why did the Roman Empire fall?",
        "How should I prioritize inventory across locations given seasonal demand?",
    ]

    print("Adaptive Reasoning System Demo (OpenRouter)")
    print("=" * 60)

    for q in questions:
        r = reasoner(question=q)
        print(f"\nQuestion: {q}")
        print(f"Routed mode: {r.reasoning_mode} (confidence: {r.confidence})")
        print(f"Answer: {r.answer}")

    q = "What are multiple plausible interpretations of this customer complaint?"
    r = router(question=q)
    print("\nMulti-strategy (aggregation) example")
    print("-" * 60)
    print(f"Question: {q}")
    print(f"Mode: {r.reasoning_mode} (confidence: {r.confidence})")
    print(f"Answer: {r.answer}")


if __name__ == "__main__":
    main()
