"""Shared evaluation metrics for training/testing.

These metrics are intentionally lightweight heuristics suitable for demos.
For production-quality evaluation, replace with task-specific or human-graded
metrics.
"""

from __future__ import annotations

from typing import Any, Callable


def classifier_accuracy_metric(example: Any, pred: Any, trace: Any = None) -> float:
    """1.0 if predicted mode matches example.reasoning_mode, else 0.0."""

    pred_mode = None
    if hasattr(pred, "reasoning_mode"):
        pred_mode = pred.reasoning_mode
    elif hasattr(pred, "reasoning_type"):
        pred_mode = pred.reasoning_type

    if not hasattr(example, "reasoning_mode") or pred_mode is None:
        return 0.0

    return float(str(example.reasoning_mode).upper() == str(pred_mode).upper())


def reasoning_quality_metric(example: Any, pred: Any, trace: Any = None) -> float:
    """A small heuristic score in [0,1] based on answer length/diversity."""

    if not hasattr(pred, "answer"):
        return 0.0

    answer = str(pred.answer)

    score = 0.0

    # Reasonable length
    if 50 < len(answer) < 2000:
        score += 0.3

    # Some reasoning indicators
    reasoning_words = ["because", "therefore", "first", "second", "thus", "consequently"]
    if any(word in answer.lower() for word in reasoning_words):
        score += 0.3

    # Not too repetitive
    words = answer.split()
    if words:
        diversity = len(set(words)) / len(words)
        if diversity > 0.5:
            score += 0.4

    return min(score, 1.0)


def combined_metric(
    *, accuracy_weight: float = 0.7, quality_weight: float = 0.3
) -> Callable[[Any, Any, Any], float]:
    """Return a combined metric function."""

    def metric(example: Any, pred: Any, trace: Any = None) -> float:
        acc = classifier_accuracy_metric(example, pred, trace)
        qual = reasoning_quality_metric(example, pred, trace)
        return accuracy_weight * acc + quality_weight * qual

    return metric


# GEPA-compatible metrics (accept extra args, return float)

def gepa_classifier_metric(
    gold: Any,
    pred: Any,
    trace: Any = None,
    pred_name: Any = None,
    pred_trace: Any = None,
) -> float:
    return classifier_accuracy_metric(gold, pred, trace)


def gepa_reasoning_metric(
    gold: Any,
    pred: Any,
    trace: Any = None,
    pred_name: Any = None,
    pred_trace: Any = None,
) -> float:
    return reasoning_quality_metric(gold, pred, trace)


def gepa_combined_metric(
    *, accuracy_weight: float = 0.7, quality_weight: float = 0.3
) -> Callable[..., float]:
    def metric(
        gold: Any,
        pred: Any,
        trace: Any = None,
        pred_name: Any = None,
        pred_trace: Any = None,
    ) -> float:
        acc_score = classifier_accuracy_metric(gold, pred, trace)
        qual_score = reasoning_quality_metric(gold, pred, trace)
        return accuracy_weight * acc_score + quality_weight * qual_score

    return metric
