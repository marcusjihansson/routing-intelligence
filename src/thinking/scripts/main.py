"""Convenience demo entrypoint.

Prefer `thinking.scripts.demo_proof_of_concept` (no API keys) and
`thinking.scripts.lm_proof_of_concept` (OpenRouter).

This script exists as a small wrapper for interactive exploration.
"""

from __future__ import annotations

import argparse

import dspy

from thinking.core.dynamic_router import MultiStrategyRouter
from thinking.core.reasoning_router import AdaptiveReasoner
from thinking.scripts.demo_proof_of_concept import MockLM
from thinking.scripts.lm_proof_of_concept import configure_openrouter_lm


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a small adaptive reasoning demo")
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use the built-in MockLM (no external API calls)",
    )
    parser.add_argument(
        "--model",
        default="openrouter/openai/gpt-4o",
        help="OpenRouter model (ignored with --mock)",
    )
    args = parser.parse_args()

    if args.mock:
        dspy.settings.configure(lm=MockLM())
    else:
        configure_openrouter_lm(model=args.model)

    reasoner = AdaptiveReasoner()
    multi = MultiStrategyRouter(confidence_threshold=0.7)

    questions = [
        "What is the capital of Sweden?",
        "Explain why the sky is blue.",
        "How do climate, economics, and politics interconnect in energy policy?",
    ]

    print("Adaptive Reasoning Demo")
    print("=" * 60)

    for q in questions:
        r = reasoner(question=q)
        print(f"\nQ: {q}")
        print(f"Mode: {r.reasoning_mode} (confidence: {r.confidence})")
        print(f"A: {r.answer}")

    q = "What is consciousness?"
    r = multi(question=q)
    print("\nMulti-strategy example")
    print("-" * 60)
    print(f"Q: {q}")
    print(f"Mode: {r.reasoning_mode} (confidence: {r.confidence})")
    print(f"A: {r.answer}")


if __name__ == "__main__":
    main()
