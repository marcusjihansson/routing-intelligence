"""Demo: breadth/depth scoring router with a real LM via OpenRouter.

Run:
  export OPENROUTER_API_KEY='sk-or-v1-...'
  python -m thinking.scripts.lm_proof_of_concept_scoring

This demonstrates the experimental `BreadthDepthRouter` alongside the baseline
`AdaptiveReasoner`.
"""

from __future__ import annotations

import argparse

import dspy

from thinking.core.reasoning_router import AdaptiveReasoner
from thinking.experiments.core.breadth_depth_router import BreadthDepthRouter
from thinking.scripts.lm_proof_of_concept import configure_openrouter_lm


def main() -> None:
    parser = argparse.ArgumentParser(description="Demo breadth/depth scoring router")
    parser.add_argument(
        "--model",
        default="openrouter/openai/gpt-4o",
        help="OpenRouter model name",
    )
    parser.add_argument(
        "--breadth-threshold",
        type=float,
        default=0.8,
    )
    parser.add_argument(
        "--depth-threshold",
        type=float,
        default=0.7,
    )
    args = parser.parse_args()

    configure_openrouter_lm(model=args.model)

    baseline = AdaptiveReasoner()
    bd = BreadthDepthRouter(
        breadth_threshold=args.breadth_threshold,
        depth_threshold=args.depth_threshold,
    )

    questions = [
        "What is the capital of France?",
        "How do sleep, stress, and cognitive performance interconnect?",
        "From first principles, why does gravity exist?",
        "Design a comprehensive framework for ethical AI development.",
    ]

    print("Breadth/Depth Scoring Demo")
    print("=" * 60)

    for q in questions:
        print(f"\nQ: {q}")

        r0 = baseline(question=q)
        print(f"Baseline -> {r0.reasoning_mode} (conf: {r0.confidence})")

        r1 = bd(question=q)
        print(
            f"Breadth/Depth -> {r1.reasoning_mode} (breadth={r1.breadth_score:.2f}, depth={r1.depth_score:.2f}, conf={r1.confidence:.2f})"
        )
        print(f"Routing rationale: {r1.routing_rationale}")


if __name__ == "__main__":
    main()
