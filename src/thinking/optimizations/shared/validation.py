"""Validation and benchmarking framework for DSPy optimizations.

This module provides functions to validate optimization quality,
compare optimizers, and track performance metrics.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Callable, Dict, List

import dspy

logger = logging.getLogger(__name__)


def evaluate_module_performance(
    module: dspy.Module,
    test_examples: List[dspy.Example],
    metric: Callable[[Any, Any, Any], float],
) -> Dict[str, Any]:
    """Evaluate module performance on test examples.

    Args:
        module: DSPy module to evaluate
        test_examples: List of test examples
        metric: Metric function to evaluate predictions

    Returns:
        Dictionary with evaluation results
    """
    scores = []
    errors = 0
    start_time = time.time()

    for example in test_examples:
        try:
            pred = module(**example.inputs())
            score = metric(example, pred)
            scores.append(score)
        except Exception as e:
            logger.warning(f"Evaluation failed for example: {e}")
            errors += 1
            scores.append(0.0)

    eval_time = time.time() - start_time

    return {
        "avg_score": sum(scores) / len(scores) if scores else 0.0,
        "min_score": min(scores) if scores else 0.0,
        "max_score": max(scores) if scores else 0.0,
        "std_score": (
            (sum((s - sum(scores) / len(scores)) ** 2 for s in scores) / len(scores))
            ** 0.5
            if scores
            else 0.0
        ),
        "total_evaluated": len(test_examples),
        "successful_evaluations": len(scores),
        "failed_evaluations": errors,
        "evaluation_time": eval_time,
        "avg_time_per_example": eval_time / len(test_examples)
        if test_examples
        else 0.0,
    }


def validate_optimization_quality(
    baseline_module: dspy.Module,
    optimized_module: dspy.Module,
    test_examples: List[dspy.Example],
    metric: Callable[[Any, Any, Any], float],
    improvement_threshold: float = 0.05,
) -> Dict[str, Any]:
    """Compare baseline vs optimized module performance.

    Args:
        baseline_module: Original unoptimized module
        optimized_module: Trained/optimized module
        test_examples: Test examples for validation
        metric: Metric function to evaluate predictions
        improvement_threshold: Minimum relative improvement (default: 5%)

    Returns:
        Dictionary with validation results

    Examples:
        >>> results = validate_optimization_quality(
        ...     baseline_module=DirectAnswer(),
        ...     optimized_module=optimized,
        ...     test_examples=test_set,
        ...     metric=reasoning_quality_metric
        ... )
        >>> results['significant_improvement']
        True
    """
    logger.info("Validating optimization quality...")

    baseline_results = evaluate_module_performance(
        baseline_module, test_examples, metric
    )
    optimized_results = evaluate_module_performance(
        optimized_module, test_examples, metric
    )

    baseline_score = baseline_results["avg_score"]
    optimized_score = optimized_results["avg_score"]

    improvement = optimized_score - baseline_score
    relative_improvement = improvement / baseline_score if baseline_score > 0 else 0.0

    significant_improvement = relative_improvement >= improvement_threshold

    validation_summary = {
        "baseline_score": baseline_score,
        "optimized_score": optimized_score,
        "absolute_improvement": improvement,
        "relative_improvement": relative_improvement,
        "significant_improvement": significant_improvement,
        "improvement_threshold": improvement_threshold,
        "baseline_results": baseline_results,
        "optimized_results": optimized_results,
    }

    if significant_improvement:
        logger.info(
            f"✓ Validation passed: {relative_improvement * 100:.1f}% improvement "
            f"(baseline: {baseline_score:.3f} -> optimized: {optimized_score:.3f})"
        )
    else:
        logger.warning(
            f"✗ Validation warning: Only {relative_improvement * 100:.1f}% improvement "
            f"(baseline: {baseline_score:.3f} -> optimized: {optimized_score:.3f})"
        )
        logger.warning(
            f"  This is below the {improvement_threshold * 100:.0f}% threshold"
        )

    return validation_summary


def benchmark_optimizers(
    module: dspy.Module,
    trainset: List[dspy.Example],
    devset: List[dspy.Example],
    metric: Callable[[Any, Any, Any], float],
    budget: str = "light",
) -> Dict[str, Any]:
    """Benchmark different optimizers on the same task.

    Args:
        module: Base DSPy module to optimize
        trainset: Training examples
        devset: Development/test examples
        metric: Evaluation metric
        budget: GEPA budget level

    Returns:
        Dictionary with benchmark results for each optimizer
    """
    logger.info("Running optimizer benchmark...")

    results: Dict[str, Any] = {}

    # GEPA optimizer
    try:
        from dspy.teleprompt import GEPA

        start_time = time.time()
        gepa_optimizer = GEPA(metric=metric, auto=budget)
        gepa_optimized = gepa_optimizer.compile(module, trainset=trainset)
        gepa_time = time.time() - start_time

        gepa_eval = evaluate_module_performance(gepa_optimized, devset, metric)

        results["gepa"] = {
            "training_time": gepa_time,
            "eval_results": gepa_eval,
            "status": "success",
        }
        logger.info(f"GEPA: {gepa_eval['avg_score']:.3f} score in {gepa_time:.2f}s")
    except Exception as e:
        logger.error(f"GEPA failed: {e}")
        results["gepa"] = {"status": "failed", "error": str(e)}

    # BootstrapFewShot optimizer
    try:
        from dspy.teleprompt import BootstrapFewShot

        start_time = time.time()
        bfs_optimizer = BootstrapFewShot(
            metric=metric,
            max_bootstrapped_demos=8,
            max_labeled_demos=16,
        )
        bfs_optimized = bfs_optimizer.compile(module, trainset=trainset)
        bfs_time = time.time() - start_time

        bfs_eval = evaluate_module_performance(bfs_optimized, devset, metric)

        results["bootstrap_fewshot"] = {
            "training_time": bfs_time,
            "eval_results": bfs_eval,
            "status": "success",
        }
        logger.info(
            f"BootstrapFewShot: {bfs_eval['avg_score']:.3f} score in {bfs_time:.2f}s"
        )
    except Exception as e:
        logger.error(f"BootstrapFewShot failed: {e}")
        results["bootstrap_fewshot"] = {"status": "failed", "error": str(e)}

    # Find best performer
    best_optimizer = None
    best_score = 0.0
    for optimizer_name, optimizer_results in results.items():
        if optimizer_results["status"] == "success":
            score = optimizer_results["eval_results"]["avg_score"]
            if score > best_score:
                best_score = score
                best_optimizer = optimizer_name

    results["summary"] = {
        "best_optimizer": best_optimizer,
        "best_score": best_score,
        "total_optimizers": len(results),
    }

    if best_optimizer:
        logger.info(f"Best optimizer: {best_optimizer} ({best_score:.3f} score)")

    return results


def print_validation_report(results: Dict[str, Any]) -> None:
    """Print formatted validation report.

    Args:
        results: Validation results dictionary from validate_optimization_quality
    """
    print("\n" + "=" * 60)
    print("OPTIMIZATION VALIDATION REPORT")
    print("=" * 60)

    print(f"Baseline Score:        {results['baseline_score']:.4f}")
    print(f"Optimized Score:       {results['optimized_score']:.4f}")
    print(f"Absolute Improvement:   {results['absolute_improvement']:+.4f}")
    print(f"Relative Improvement:   {results['relative_improvement'] * 100:+.2f}%")
    print(f"Improvement Threshold: {results['improvement_threshold'] * 100:.0f}%")

    status = "✓ PASSED" if results["significant_improvement"] else "✗ FAILED"
    print(f"\nValidation Status:      {status}")

    if not results["significant_improvement"]:
        print("\nWarning: Optimization did not meet improvement threshold.")
        print("Consider:")
        print("  - Increasing training examples")
        print("  - Using different GEPA budget")
        print("  - Trying a different optimizer")

    print("=" * 60 + "\n")


def print_benchmark_report(results: Dict[str, Any]) -> None:
    """Print formatted benchmark report.

    Args:
        results: Benchmark results dictionary from benchmark_optimizers
    """
    print("\n" + "=" * 70)
    print("OPTIMIZER BENCHMARK REPORT")
    print("=" * 70)

    for optimizer_name, optimizer_results in results.items():
        if optimizer_name == "summary":
            continue

        print(f"\n{optimizer_name.upper()}")
        print("-" * 70)

        if optimizer_results["status"] == "success":
            eval_results = optimizer_results["eval_results"]
            print(f"  Training Time:       {optimizer_results['training_time']:.2f}s")
            print(f"  Average Score:       {eval_results['avg_score']:.4f}")
            print(f"  Min Score:           {eval_results['min_score']:.4f}")
            print(f"  Max Score:           {eval_results['max_score']:.4f}")
            print(f"  Std Dev:             {eval_results['std_score']:.4f}")
            print(f"  Evaluation Time:     {eval_results['evaluation_time']:.2f}s")
            print(
                f"  Success Rate:        "
                f"{eval_results['successful_evaluations']}/{eval_results['total_evaluated']} "
                f"({eval_results['successful_evaluations'] / eval_results['total_evaluated'] * 100:.0f}%)"
            )
        else:
            print(f"  Status: FAILED")
            print(f"  Error: {optimizer_results.get('error', 'Unknown')}")

    print("\n" + "-" * 70)
    if "summary" in results:
        summary = results["summary"]
        print(f"Best Optimizer:       {summary['best_optimizer']}")
        print(f"Best Score:           {summary['best_score']:.4f}")

    print("=" * 70 + "\n")
