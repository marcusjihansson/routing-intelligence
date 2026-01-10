"""Breadth/Depth router evaluation utilities.

This module provides helpers to evaluate the breadth/depth router on a provided
DSPy test suite. It is separate from the threshold sweep and comparative scripts.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List

import dspy

from thinking.core.dynamic_router import MultiStrategyRouter
from thinking.core.reasoning_router import AdaptiveReasoner
from thinking.experiments.core.breadth_depth_router import BreadthDepthRouter


@dataclass(frozen=True)
class BreadthDepthEvaluation:
    total_queries: int
    correct_routes: int
    accuracy: float
    routing_distribution: Dict[str, int]
    misclassifications: List[Dict[str, Any]]
    average_scores: Dict[str, float]


def evaluate_breadth_depth_routing(
    breadth_depth_router: BreadthDepthRouter,
    test_suite: List[dspy.Example],
    *,
    verbose: bool = True,
) -> BreadthDepthEvaluation:
    """Evaluate breadth/depth routing performance on a labeled DSPy test suite."""

    correct = 0
    routing_counts: Dict[str, int] = defaultdict(int)
    misclassifications: List[Dict[str, Any]] = []

    total_breadth = 0.0
    total_depth = 0.0
    score_count = 0

    for i, example in enumerate(test_suite, 1):
        if verbose and i % 25 == 0:
            print(f"progress: {i}/{len(test_suite)}")

        question = str(example.question)
        expected_mode = str(getattr(example, "reasoning_mode", ""))

        try:
            result = breadth_depth_router(question=question)
            predicted_mode = str(result.reasoning_mode)

            routing_counts[predicted_mode] += 1

            if getattr(result, "breadth_score", None) is not None:
                total_breadth += float(result.breadth_score)
                total_depth += float(result.depth_score)
                score_count += 1

            if predicted_mode == expected_mode:
                correct += 1
            else:
                misclassifications.append(
                    {
                        "question": question,
                        "expected": expected_mode,
                        "predicted": predicted_mode,
                        "breadth_score": getattr(result, "breadth_score", None),
                        "depth_score": getattr(result, "depth_score", None),
                        "routing_rationale": getattr(result, "routing_rationale", ""),
                    }
                )
        except Exception as e:
            misclassifications.append(
                {
                    "question": question,
                    "expected": expected_mode,
                    "predicted": "ERROR",
                    "error": str(e),
                }
            )

    accuracy = correct / len(test_suite) if test_suite else 0.0

    avg_breadth = total_breadth / score_count if score_count else 0.0
    avg_depth = total_depth / score_count if score_count else 0.0

    return BreadthDepthEvaluation(
        total_queries=len(test_suite),
        correct_routes=correct,
        accuracy=accuracy,
        routing_distribution=dict(routing_counts),
        misclassifications=misclassifications,
        average_scores={"breadth": avg_breadth, "depth": avg_depth},
    )


def compare_routing_methods(
    test_suite: List[dspy.Example], *, verbose: bool = True
) -> Dict[str, Any]:
    """Compare BreadthDepthRouter vs AdaptiveReasoner vs MultiStrategyRouter."""

    bd_router = BreadthDepthRouter()
    adaptive = AdaptiveReasoner()
    multi = MultiStrategyRouter()

    bd = evaluate_breadth_depth_routing(bd_router, test_suite, verbose=False)

    def _accuracy(router) -> float:
        correct = 0
        for ex in test_suite:
            try:
                pred = router(question=str(ex.question))
                if str(pred.reasoning_mode) == str(getattr(ex, "reasoning_mode", "")):
                    correct += 1
            except Exception:
                continue
        return correct / len(test_suite) if test_suite else 0.0

    comparison = {
        "breadth_depth": {
            "accuracy": bd.accuracy,
            "routing_distribution": bd.routing_distribution,
            "average_breadth": bd.average_scores["breadth"],
            "average_depth": bd.average_scores["depth"],
        },
        "adaptive_baseline": {"accuracy": _accuracy(adaptive)},
        "multi_strategy": {"accuracy": _accuracy(multi)},
    }

    if verbose:
        print("Routing method comparison")
        for k, v in comparison.items():
            print(f"- {k}: {v['accuracy']:.1%}")

    return comparison
