"""Evaluation utilities for the Direct (DIRECT) reasoning module."""

from __future__ import annotations

import argparse
from typing import Any, Dict, List

from thinking.core.reasoning_modes import DirectAnswer
from thinking.optimizations.shared.openrouter_config import (
    configure_openrouter_lm,
    print_setup_instructions,
)


def create_direct_test_suite() -> List[Dict[str, Any]]:
    return [
        {
            "question": "What is the capital of France?",
            "expected_mode": "DIRECT",
            "category": "factual",
            "difficulty": "easy",
        },
        {
            "question": "How many days are in a leap year?",
            "expected_mode": "DIRECT",
            "category": "factual",
            "difficulty": "easy",
        },
        {
            "question": "Who wrote 'Romeo and Juliet'?",
            "expected_mode": "DIRECT",
            "category": "factual",
            "difficulty": "easy",
        },
        {
            "question": "What is 15 + 27?",
            "expected_mode": "DIRECT",
            "category": "math",
            "difficulty": "easy",
        },
        {
            "question": "Define machine learning",
            "expected_mode": "DIRECT",
            "category": "definition",
            "difficulty": "easy",
        },
    ]


def evaluate_direct_module(
    module: DirectAnswer,
    test_suite: List[Dict[str, Any]] | None = None,
    *,
    verbose: bool = True,
) -> Dict[str, Any]:
    if test_suite is None:
        test_suite = create_direct_test_suite()

    if verbose:
        print("=" * 80)
        print("EVALUATING DIRECT ANSWER MODULE")
        print("=" * 80)

    results: list[dict[str, Any]] = []

    for test_case in test_suite:
        question = test_case["question"]
        try:
            prediction = module(question=question)
            answer = prediction.answer if hasattr(prediction, "answer") else str(prediction)
            is_concise = len(answer) < 300

            results.append(
                {
                    "question": question,
                    "answer_length": len(answer),
                    "is_concise": is_concise,
                    "category": test_case.get("category", "unknown"),
                }
            )
        except Exception as e:
            if verbose:
                print(f"Error on question: {question} -> {e}")
            results.append({"question": question, "error": str(e)})

    valid_results = [r for r in results if "error" not in r]

    summary: dict[str, Any] = {
        "total_tests": len(test_suite),
        "successful": len(valid_results),
        "avg_length": (
            sum(r["answer_length"] for r in valid_results) / len(valid_results)
            if valid_results
            else 0
        ),
        "conciseness_rate": (
            sum(1 for r in valid_results if r["is_concise"]) / len(valid_results)
            if valid_results
            else 0
        ),
        "detailed_results": results,
    }

    if verbose:
        print(f"\nResults: {summary['successful']}/{summary['total_tests']} successful")
        print(f"Avg length: {summary['avg_length']:.0f} chars")
        print(f"Conciseness rate: {summary['conciseness_rate']:.1%}")

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate DirectAnswer module")
    parser.add_argument("--model", default="openrouter/openai/gpt-4o")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    lm = configure_openrouter_lm(model=args.model, verbose=not args.quiet)
    if lm is None:
        print_setup_instructions()
        raise SystemExit(1)

    module = DirectAnswer()
    evaluate_direct_module(module, verbose=not args.quiet)


if __name__ == "__main__":
    main()
