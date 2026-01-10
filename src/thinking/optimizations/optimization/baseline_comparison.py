"""Baseline vs optimized comparison utilities."""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass
from typing import Any, Callable, Dict, List

import dspy

from thinking.optimizations.shared.model_persistence import load_optimized_module


@dataclass(frozen=True)
class ComparisonResult:
    module_name: str
    baseline_accuracy: float
    optimized_accuracy: float
    improvement: float
    improvement_pct: float
    baseline_avg_time: float
    optimized_avg_time: float
    test_cases: int
    detailed_results: List[Dict[str, Any]]


def compare_baseline_vs_optimized(
    *,
    baseline_module: Any,
    optimized_module: Any,
    test_suite: List[dspy.Example],
    module_name: str,
    metric_fn: Callable[[Any, Any, Any], float],
    verbose: bool = True,
) -> ComparisonResult:
    if verbose:
        print("=" * 80)
        print(f"COMPARING BASELINE VS OPTIMIZED: {module_name.upper()}")
        print("=" * 80)

    baseline_scores: list[float] = []
    optimized_scores: list[float] = []
    baseline_times: list[float] = []
    optimized_times: list[float] = []

    detailed: list[dict[str, Any]] = []

    for i, example in enumerate(test_suite, 1):
        inputs = example.inputs()

        # Baseline
        b_err = None
        try:
            t0 = time.time()
            b_pred = baseline_module(**inputs)
            t1 = time.time()
            b_score = float(metric_fn(example, b_pred))
        except Exception as e:
            b_pred = None
            b_score = 0.0
            t1 = time.time()
            t0 = t1
            b_err = str(e)

        baseline_scores.append(b_score)
        baseline_times.append(t1 - t0)

        # Optimized
        o_err = None
        try:
            t0o = time.time()
            o_pred = optimized_module(**inputs)
            t1o = time.time()
            o_score = float(metric_fn(example, o_pred))
        except Exception as e:
            o_pred = None
            o_score = 0.0
            t1o = time.time()
            t0o = t1o
            o_err = str(e)

        optimized_scores.append(o_score)
        optimized_times.append(t1o - t0o)

        detailed.append(
            {
                "example_idx": i - 1,
                "baseline_score": b_score,
                "optimized_score": o_score,
                "improvement": o_score - b_score,
                "baseline_time": t1 - t0,
                "optimized_time": t1o - t0o,
                "baseline_error": b_err,
                "optimized_error": o_err,
            }
        )

        if verbose and i % 10 == 0:
            print(f"Progress: {i}/{len(test_suite)}")

    baseline_acc = sum(baseline_scores) / len(baseline_scores) if baseline_scores else 0.0
    optimized_acc = sum(optimized_scores) / len(optimized_scores) if optimized_scores else 0.0

    improvement = optimized_acc - baseline_acc
    improvement_pct = (improvement / baseline_acc * 100.0) if baseline_acc > 0 else 0.0

    baseline_avg_time = sum(baseline_times) / len(baseline_times) if baseline_times else 0.0
    optimized_avg_time = sum(optimized_times) / len(optimized_times) if optimized_times else 0.0

    result = ComparisonResult(
        module_name=module_name,
        baseline_accuracy=baseline_acc,
        optimized_accuracy=optimized_acc,
        improvement=improvement,
        improvement_pct=improvement_pct,
        baseline_avg_time=baseline_avg_time,
        optimized_avg_time=optimized_avg_time,
        test_cases=len(test_suite),
        detailed_results=detailed,
    )

    if verbose:
        print("\n" + "=" * 80)
        print("COMPARISON RESULTS")
        print("=" * 80)
        print(f"Baseline accuracy:  {baseline_acc:.1%}")
        print(f"Optimized accuracy: {optimized_acc:.1%}")
        print(f"Improvement:        {improvement:+.1%} ({improvement_pct:+.1f}%)")
        print("\nLatency:")
        print(f"Baseline avg:  {baseline_avg_time * 1000:.1f}ms")
        print(f"Optimized avg: {optimized_avg_time * 1000:.1f}ms")

    return result


def run_comparison_suite(
    *,
    module_name: str,
    baseline_module: Any,
    optimized_module_path: str,
    module_class: type,
    test_suite: List[dspy.Example],
    metric_fn: Callable[[Any, Any, Any], float],
    verbose: bool = True,
) -> ComparisonResult:
    if verbose:
        print(f"Loading optimized module from: {optimized_module_path}")

    optimized_module, _metadata = load_optimized_module(
        module_path=optimized_module_path, module_class=module_class, verbose=verbose
    )

    return compare_baseline_vs_optimized(
        baseline_module=baseline_module,
        optimized_module=optimized_module,
        test_suite=test_suite,
        module_name=module_name,
        metric_fn=metric_fn,
        verbose=verbose,
    )


def as_dict(result: ComparisonResult) -> Dict[str, Any]:
    return asdict(result)
