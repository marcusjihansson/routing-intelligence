"""Routing (classifier) evaluation utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

import dspy

from thinking.core.reasoning_router import AdaptiveReasoner
from thinking.optimizations.shared.data_generation import SyntheticDataGenerator


@dataclass(frozen=True)
class RoutingAccuracyResult:
    accuracy: float
    correct: int
    total: int
    per_mode_accuracy: Dict[str, float]
    confusion_matrix: Dict[str, Dict[str, int]]


def generate_test_suite_for_routing(num_examples_per_mode: int = 20) -> List[dspy.Example]:
    """Generate a synthetic labeled test suite for routing."""

    gen = SyntheticDataGenerator()
    return gen.generate_classifier_data(num_examples_per_mode=num_examples_per_mode)


def evaluate_routing_accuracy(
    classifier: Any,
    test_suite: List[dspy.Example],
    *,
    verbose: bool = True,
) -> RoutingAccuracyResult:
    correct = 0
    confusion: Dict[str, Dict[str, int]] = {}
    per_mode_total: Dict[str, int] = {}
    per_mode_correct: Dict[str, int] = {}

    for ex in test_suite:
        expected = str(ex.reasoning_mode).upper()
        per_mode_total[expected] = per_mode_total.get(expected, 0) + 1

        pred = classifier(question=ex.question)
        predicted = str(getattr(pred, "reasoning_mode", getattr(pred, "reasoning_type", ""))).upper()

        confusion.setdefault(expected, {})
        confusion[expected][predicted] = confusion[expected].get(predicted, 0) + 1

        if predicted == expected:
            correct += 1
            per_mode_correct[expected] = per_mode_correct.get(expected, 0) + 1

    total = len(test_suite)
    accuracy = correct / total if total else 0.0

    per_mode_accuracy = {
        mode: (per_mode_correct.get(mode, 0) / per_mode_total.get(mode, 1))
        for mode in per_mode_total.keys()
    }

    if verbose:
        print(f"Overall accuracy: {accuracy:.1%} ({correct}/{total})")

    return RoutingAccuracyResult(
        accuracy=accuracy,
        correct=correct,
        total=total,
        per_mode_accuracy=per_mode_accuracy,
        confusion_matrix=confusion,
    )


def compare_classifier_versions(
    *,
    baseline_classifier: Any,
    optimized_classifier: Any,
    test_suite: List[dspy.Example],
    verbose: bool = True,
) -> Dict[str, Any]:
    base = evaluate_routing_accuracy(baseline_classifier, test_suite, verbose=False)
    opt = evaluate_routing_accuracy(optimized_classifier, test_suite, verbose=False)

    improvement = opt.accuracy - base.accuracy

    if verbose:
        print(f"Baseline:  {base.accuracy:.1%}")
        print(f"Optimized: {opt.accuracy:.1%}")
        print(f"Improvement: {improvement:+.1%}")

    return {
        "baseline": base.__dict__,
        "optimized": opt.__dict__,
        "improvement": improvement,
    }
