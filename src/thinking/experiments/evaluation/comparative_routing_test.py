"""Comparative routing analysis.

Compares the breadth/depth router against baseline routing methods using the same
labeled examples as `routing_efficiency_test`.

Run:
  export OPENROUTER_API_KEY='sk-or-v1-...'
  python -m thinking.experiments.evaluation.comparative_routing_test

Outputs:
  - thinking/experiments/results/comparative_routing_analysis.json
"""

from __future__ import annotations

import argparse
import json
import time
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from thinking.core.dynamic_router import MultiStrategyRouter
from thinking.core.reasoning_router import AdaptiveReasoner
from thinking.experiments.core.breadth_depth_router import BreadthDepthRouter
from thinking.experiments.evaluation.routing_efficiency_test import (
    LabeledExample,
    load_labeled_examples,
)
from thinking.scripts.lm_proof_of_concept import configure_openrouter_lm


@dataclass(frozen=True)
class RouterComparison:
    router_name: str
    accuracy: float
    per_mode_accuracy: dict[str, float]
    mode_distribution: dict[str, int]
    confusion_matrix: dict[str, dict[str, int]]
    average_latency: float
    total_examples: int


@dataclass(frozen=True)
class ComparativeAnalysis:
    test_timestamp: str
    total_examples: int
    routers_compared: list[str]
    router_results: dict[str, RouterComparison]
    best_performing_router: str
    accuracy_rankings: list[str]
    per_mode_breakdown: dict[str, dict[str, float]]


def _package_root() -> Path:
    return Path(__file__).resolve().parents[2]


def test_router_performance(
    *,
    router_name: str,
    router_instance: Any,
    examples: list[LabeledExample],
    verbose: bool = False,
) -> RouterComparison:
    correct = 0
    mode_distribution: dict[str, int] = defaultdict(int)
    confusion: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    latencies: list[float] = []

    per_mode_correct: dict[str, int] = defaultdict(int)
    per_mode_total: dict[str, int] = defaultdict(int)

    for i, example in enumerate(examples, 1):
        if verbose and i % 50 == 0:
            print(f"  progress: {i}/{len(examples)}")

        expected_mode = example.reasoning_mode
        per_mode_total[expected_mode] += 1

        try:
            t0 = time.time()
            pred = router_instance(question=example.question)
            t1 = time.time()

            latencies.append(t1 - t0)

            predicted_mode = str(pred.reasoning_mode)
            mode_distribution[predicted_mode] += 1
            confusion[expected_mode][predicted_mode] += 1

            if predicted_mode == expected_mode:
                correct += 1
                per_mode_correct[expected_mode] += 1

        except Exception:
            confusion[expected_mode]["ERROR"] += 1
            latencies.append(0.0)

    accuracy = correct / len(examples)
    per_mode_accuracy = {
        mode: (per_mode_correct[mode] / per_mode_total[mode]) if per_mode_total[mode] else 0.0
        for mode in sorted(per_mode_total.keys())
    }
    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0

    return RouterComparison(
        router_name=router_name,
        accuracy=accuracy,
        per_mode_accuracy=dict(per_mode_accuracy),
        mode_distribution=dict(mode_distribution),
        confusion_matrix={k: dict(v) for k, v in confusion.items()},
        average_latency=avg_latency,
        total_examples=len(examples),
    )


def compare_all_routers(
    *,
    breadth_threshold: float = 0.8,
    depth_threshold: float = 0.7,
    model: str = "openrouter/openai/gpt-4o",
    output_file: Path | None = None,
    verbose: bool = True,
) -> dict[str, Any]:
    configure_openrouter_lm(model=model)

    examples = load_labeled_examples()

    if verbose:
        print("=" * 80)
        print("COMPARATIVE ROUTING ANALYSIS")
        print("=" * 80)
        print(f"Examples: {len(examples)}")
        print(f"Breadth/Depth thresholds: breadth={breadth_threshold}, depth={depth_threshold}")

    routers_to_test: dict[str, Any] = {
        "BreadthDepth": BreadthDepthRouter(
            breadth_threshold=breadth_threshold, depth_threshold=depth_threshold
        ),
        "AdaptiveReasoner": AdaptiveReasoner(),
        # Default threshold matches the core implementation (0.7)
        "MultiStrategy": MultiStrategyRouter(confidence_threshold=0.7),
        # More likely to use multi-strategy: higher threshold
        "MultiStrategy_Aggressive": MultiStrategyRouter(confidence_threshold=0.8),
        # Less likely to use multi-strategy: lower threshold
        "MultiStrategy_Conservative": MultiStrategyRouter(confidence_threshold=0.4),
    }

    router_results: dict[str, RouterComparison] = {}
    for name, router in routers_to_test.items():
        if verbose:
            print(f"\nTesting {name}...")
        router_results[name] = test_router_performance(
            router_name=name, router_instance=router, examples=examples, verbose=verbose
        )

    accuracy_rankings = sorted(router_results.keys(), key=lambda k: router_results[k].accuracy, reverse=True)
    best_router = accuracy_rankings[0]

    # Per-mode breakdown for convenience
    all_modes: set[str] = set()
    for r in router_results.values():
        all_modes.update(r.per_mode_accuracy.keys())

    per_mode_breakdown: dict[str, dict[str, float]] = {}
    for mode in sorted(all_modes):
        per_mode_breakdown[mode] = {
            router_name: router_results[router_name].per_mode_accuracy.get(mode, 0.0)
            for router_name in router_results.keys()
        }

    analysis = ComparativeAnalysis(
        test_timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
        total_examples=len(examples),
        routers_compared=list(routers_to_test.keys()),
        router_results=router_results,
        best_performing_router=best_router,
        accuracy_rankings=accuracy_rankings,
        per_mode_breakdown=per_mode_breakdown,
    )

    payload: dict[str, Any] = asdict(analysis)

    if output_file is not None:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        if verbose:
            print(f"\nSaved comparison results to: {output_file}")

    if verbose:
        print("\n" + "=" * 80)
        print("RANKINGS")
        print("=" * 80)
        for i, name in enumerate(accuracy_rankings, 1):
            r = router_results[name]
            print(f"{i}. {name}: {r.accuracy:.1%} (avg latency: {r.average_latency:.3f}s)")
        print(f"\nBest: {best_router} ({router_results[best_router].accuracy:.1%})")

    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare routing methods")
    parser.add_argument("--breadth-threshold", type=float, default=0.8)
    parser.add_argument("--depth-threshold", type=float, default=0.7)
    parser.add_argument("--model", default="openrouter/openai/gpt-4o")
    parser.add_argument("--output", default=None)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    default_out = _package_root() / "experiments" / "results" / "comparative_routing_analysis.json"
    out_path = Path(args.output) if args.output else default_out

    compare_all_routers(
        breadth_threshold=args.breadth_threshold,
        depth_threshold=args.depth_threshold,
        model=args.model,
        output_file=out_path,
        verbose=not args.quiet,
    )


if __name__ == "__main__":
    main()
