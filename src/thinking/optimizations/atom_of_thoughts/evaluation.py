"""Evaluation utilities for the Atom of Thoughts (AOT) reasoning module."""

from __future__ import annotations

import argparse
from typing import Any, Dict, List

from thinking.core.reasoning_modes import AtomOfThoughts
from thinking.optimizations.shared.metrics import reasoning_quality_metric
from thinking.optimizations.shared.openrouter_config import (
    configure_openrouter_lm,
    print_setup_instructions,
)


def create_aot_test_suite() -> List[Dict[str, Any]]:
    return [
        {
            "question": "From first principles, why does gravity exist?",
            "expected_mode": "AOT",
            "category": "first_principles",
            "difficulty": "hard",
        },
        {
            "question": "Break down democracy to its atomic components.",
            "expected_mode": "AOT",
            "category": "first_principles",
            "difficulty": "hard",
        },
        {
            "question": "What is time at the most fundamental level?",
            "expected_mode": "AOT",
            "category": "first_principles",
            "difficulty": "hard",
        },
    ]


def evaluate_aot_module(
    module: AtomOfThoughts,
    test_suite: List[Dict[str, Any]] | None = None,
    *,
    verbose: bool = True,
) -> Dict[str, Any]:
    if test_suite is None:
        test_suite = create_aot_test_suite()

    if verbose:
        print("=" * 80)
        print("EVALUATING ATOM OF THOUGHTS (AOT) MODULE")
        print("=" * 80)

    detailed: list[dict[str, Any]] = []
    scores: list[float] = []

    for tc in test_suite:
        q = tc["question"]
        try:
            pred = module(question=q)
            score = reasoning_quality_metric(tc, pred)
            scores.append(score)
            detailed.append(
                {
                    "question": q,
                    "score": score,
                    "answer_length": len(str(pred.answer)) if hasattr(pred, "answer") else None,
                    "category": tc.get("category"),
                }
            )
        except Exception as e:
            detailed.append({"question": q, "error": str(e)})

    successful = sum(1 for r in detailed if "error" not in r)
    avg_score = sum(scores) / len(scores) if scores else 0.0

    summary: dict[str, Any] = {
        "total_tests": len(test_suite),
        "successful": successful,
        "avg_quality_score": avg_score,
        "detailed_results": detailed,
    }

    if verbose:
        print(f"\nResults: {successful}/{len(test_suite)} successful")
        print(f"Avg heuristic quality score: {avg_score:.3f}")

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate AtomOfThoughts module")
    parser.add_argument("--model", default="openrouter/openai/gpt-4o")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    lm = configure_openrouter_lm(model=args.model, verbose=not args.quiet)
    if lm is None:
        print_setup_instructions()
        raise SystemExit(1)

    module = AtomOfThoughts()
    evaluate_aot_module(module, verbose=not args.quiet)


if __name__ == "__main__":
    main()
