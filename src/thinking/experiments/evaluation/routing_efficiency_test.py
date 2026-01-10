"""Routing efficiency testing for the breadth/depth router.

This evaluates `BreadthDepthRouter` across a grid of breadth/depth thresholds using
labeled examples (pulled from `thinking/optimizations/*/training_examples.jsonl`).

Run (requires OpenRouter):
  export OPENROUTER_API_KEY='sk-or-v1-...'
  python -m thinking.experiments.evaluation.routing_efficiency_test --quick

Outputs:
  - thinking/experiments/results/routing_efficiency_results.json
"""

from __future__ import annotations

import argparse
import json
import time
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import dspy

from thinking.experiments.core.breadth_depth_router import BreadthDepthRouter
from thinking.scripts.lm_proof_of_concept import configure_openrouter_lm


@dataclass(frozen=True)
class LabeledExample:
    question: str
    answer: str
    reasoning_mode: str
    source_file: str


@dataclass(frozen=True)
class RoutingTestResult:
    breadth_threshold: float
    depth_threshold: float
    total_examples: int
    correct_predictions: int
    accuracy: float
    per_mode_accuracy: dict[str, float]
    mode_distribution: dict[str, int]
    average_scores: dict[str, float]
    test_duration: float
    confusion_matrix: dict[str, dict[str, int]]


def _package_root() -> Path:
    # .../thinking/experiments/evaluation/routing_efficiency_test.py -> .../thinking
    return Path(__file__).resolve().parents[2]


def load_labeled_examples() -> list[LabeledExample]:
    """Load labeled examples from `thinking/optimizations/*/training_examples.jsonl`."""

    base_path = _package_root() / "optimizations"
    mode_mapping = {
        "direct": "DIRECT",
        "chain_of_thought": "COT",
        "tree_of_thoughts": "TOT",
        "graph_of_thoughts": "GOT",
        "atom_of_thoughts": "AOT",
        "combined": "COMBINED",
    }

    examples: list[LabeledExample] = []

    for mode_dir, mode_abbrev in mode_mapping.items():
        jsonl_file = base_path / mode_dir / "training_examples.jsonl"
        if not jsonl_file.exists():
            continue

        with jsonl_file.open("r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)
                    examples.append(
                        LabeledExample(
                            question=data["question"],
                            answer=data.get("answer", ""),
                            reasoning_mode=mode_abbrev,
                            source_file=str(jsonl_file),
                        )
                    )
                except Exception as e:
                    raise RuntimeError(
                        f"Failed to parse {jsonl_file} line {line_num}: {e}"
                    ) from e

    mode_counts = Counter(ex.reasoning_mode for ex in examples)
    if not examples:
        raise RuntimeError(
            f"No labeled examples found. Expected JSONL under: {base_path}"
        )

    # Simple sanity check: we expect 6 modes.
    if len(mode_counts) < 2:
        raise RuntimeError(f"Unexpected labeled example distribution: {dict(mode_counts)}")

    return examples


def evaluate_threshold_combination(
    examples: list[LabeledExample],
    breadth_threshold: float,
    depth_threshold: float,
    *,
    verbose: bool = False,
) -> RoutingTestResult:
    start_time = time.time()

    router = BreadthDepthRouter(
        breadth_threshold=breadth_threshold,
        depth_threshold=depth_threshold,
    )

    correct = 0
    mode_distribution: dict[str, int] = defaultdict(int)
    confusion: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    per_mode_correct: dict[str, int] = defaultdict(int)
    per_mode_total: dict[str, int] = defaultdict(int)

    total_breadth = 0.0
    total_depth = 0.0
    score_count = 0

    for i, example in enumerate(examples, 1):
        if verbose and i % 50 == 0:
            print(f"  progress: {i}/{len(examples)}")

        expected_mode = example.reasoning_mode
        per_mode_total[expected_mode] += 1

        try:
            pred = router(question=example.question)
            predicted_mode = str(pred.reasoning_mode)

            mode_distribution[predicted_mode] += 1
            confusion[expected_mode][predicted_mode] += 1

            if predicted_mode == expected_mode:
                correct += 1
                per_mode_correct[expected_mode] += 1

            if getattr(pred, "breadth_score", None) is not None:
                total_breadth += float(pred.breadth_score)
                total_depth += float(pred.depth_score)
                score_count += 1

        except Exception:
            confusion[expected_mode]["ERROR"] += 1

    accuracy = correct / len(examples)

    per_mode_accuracy = {
        mode: (per_mode_correct[mode] / per_mode_total[mode]) if per_mode_total[mode] else 0.0
        for mode in sorted(per_mode_total.keys())
    }

    avg_breadth = total_breadth / score_count if score_count else 0.0
    avg_depth = total_depth / score_count if score_count else 0.0

    return RoutingTestResult(
        breadth_threshold=breadth_threshold,
        depth_threshold=depth_threshold,
        total_examples=len(examples),
        correct_predictions=correct,
        accuracy=accuracy,
        per_mode_accuracy=dict(per_mode_accuracy),
        mode_distribution=dict(mode_distribution),
        average_scores={"breadth": avg_breadth, "depth": avg_depth},
        test_duration=time.time() - start_time,
        confusion_matrix={k: dict(v) for k, v in confusion.items()},
    )


def test_routing_efficiency(
    *,
    quick: bool,
    model: str,
    output_file: Path | None,
    verbose: bool,
) -> dict[str, Any]:
    configure_openrouter_lm(model=model)

    examples = load_labeled_examples()

    if quick:
        thresholds = [0.5, 0.6, 0.7]
    else:
        thresholds = [0.4, 0.5, 0.6, 0.7, 0.8]

    results: list[RoutingTestResult] = []

    total_configs = len(thresholds) * len(thresholds)
    print("=" * 80)
    print("ROUTING EFFICIENCY TEST")
    print("=" * 80)
    print(f"Examples: {len(examples)}")
    print(f"Thresholds: {thresholds} ({total_configs} configurations)")

    start = time.time()

    for b in thresholds:
        for d in thresholds:
            if verbose:
                print(f"\nTesting breadth={b}, depth={d}")
            results.append(
                evaluate_threshold_combination(examples, b, d, verbose=verbose)
            )

    best = max(results, key=lambda r: r.accuracy)

    payload: dict[str, Any] = {
        "test_summary": {
            "total_examples": len(examples),
            "total_configurations": total_configs,
            "threshold_range": thresholds,
            "best_configuration": {
                "breadth_threshold": best.breadth_threshold,
                "depth_threshold": best.depth_threshold,
                "accuracy": best.accuracy,
            },
            "test_duration": time.time() - start,
        },
        "results": [asdict(r) for r in results],
    }

    if output_file is not None:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"\nSaved results to: {output_file}")

    print(
        f"\nBest configuration: breadth={best.breadth_threshold}, depth={best.depth_threshold} -> {best.accuracy:.1%}"
    )
    print(f"Total runtime: {payload['test_summary']['test_duration']:.1f}s")

    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate breadth/depth routing efficiency")
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run a smaller 3x3 threshold grid (0.5,0.6,0.7)",
    )
    parser.add_argument(
        "--model",
        default="openrouter/openai/gpt-4o",
        help="OpenRouter model name",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Path to write JSON results (default: thinking/experiments/results/routing_efficiency_results.json)",
    )
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    default_out = _package_root() / "experiments" / "results" / "routing_efficiency_results.json"
    out_path = Path(args.output) if args.output else default_out

    test_routing_efficiency(
        quick=args.quick,
        model=args.model,
        output_file=out_path,
        verbose=args.verbose,
    )


if __name__ == "__main__":
    main()
