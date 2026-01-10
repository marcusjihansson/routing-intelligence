"""CLI to test whether optimization improved modules/classifier."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Callable

import dspy

from thinking.core.reasoning_modes import (
    AtomOfThoughts,
    ChainOfThought,
    CombinedReasoning,
    DirectAnswer,
    GraphOfThoughts,
    TreeOfThoughts,
)
from thinking.core.reasoning_router import AdaptiveReasoner
from thinking.optimizations.optimization.baseline_comparison import run_comparison_suite
from thinking.optimizations.optimization.routing_evaluation import generate_test_suite_for_routing
from thinking.optimizations.shared.metrics import classifier_accuracy_metric, reasoning_quality_metric
from thinking.optimizations.shared.model_persistence import get_latest_module


def _examples_from_test_suite_dicts(test_cases: list[dict[str, Any]]) -> list[dspy.Example]:
    return [dspy.Example(question=tc["question"]).with_inputs("question") for tc in test_cases]


def _load_test_suite_for_module(module: str) -> list[dspy.Example]:
    if module == "direct":
        from thinking.optimizations.direct.evaluation import create_direct_test_suite

        return _examples_from_test_suite_dicts(create_direct_test_suite())
    if module == "cot":
        from thinking.optimizations.chain_of_thought.evaluation import create_cot_test_suite

        return _examples_from_test_suite_dicts(create_cot_test_suite())
    if module == "tot":
        from thinking.optimizations.tree_of_thoughts.evaluation import create_tot_test_suite

        return _examples_from_test_suite_dicts(create_tot_test_suite())
    if module == "got":
        from thinking.optimizations.graph_of_thoughts.evaluation import create_got_test_suite

        return _examples_from_test_suite_dicts(create_got_test_suite())
    if module == "aot":
        from thinking.optimizations.atom_of_thoughts.evaluation import create_aot_test_suite

        return _examples_from_test_suite_dicts(create_aot_test_suite())
    if module == "combined":
        from thinking.optimizations.combined.evaluation import create_combined_test_suite

        return _examples_from_test_suite_dicts(create_combined_test_suite())

    raise ValueError(f"Unknown module: {module}")


def _baseline_for(module: str):
    if module == "direct":
        return DirectAnswer(), DirectAnswer
    if module == "cot":
        return ChainOfThought(), ChainOfThought
    if module == "tot":
        return TreeOfThoughts(branches=3, depth=2), TreeOfThoughts
    if module == "got":
        return GraphOfThoughts(max_nodes=5), GraphOfThoughts
    if module == "aot":
        return AtomOfThoughts(), AtomOfThoughts
    if module == "combined":
        return CombinedReasoning(), CombinedReasoning
    if module == "classifier":
        return AdaptiveReasoner(), AdaptiveReasoner

    raise ValueError(f"Unknown module: {module}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Test baseline vs optimized modules")
    parser.add_argument(
        "--module",
        required=True,
        help="One of: direct,cot,tot,got,aot,combined,classifier,all",
    )
    parser.add_argument(
        "--search-dir",
        default=".",
        help="Directory where *_optimized_* folders are stored",
    )
    parser.add_argument("--output", default=None, help="Write JSON report to this path")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    modules = [args.module]
    if args.module == "all":
        modules = ["direct", "cot", "tot", "got", "aot", "combined"]

    report: dict[str, Any] = {
        "modules": [],
    }

    for mod in modules:
        baseline, cls = _baseline_for(mod)

        latest = get_latest_module(module_name=mod, save_dir=args.search_dir)
        if latest is None:
            raise SystemExit(
                f"No saved modules found for '{mod}' in {args.search_dir}. Train one first."
            )

        if mod == "classifier":
            test_suite = generate_test_suite_for_routing(num_examples_per_mode=10)
            metric: Callable[..., float] = classifier_accuracy_metric
        else:
            test_suite = _load_test_suite_for_module(mod)
            metric = reasoning_quality_metric

        result = run_comparison_suite(
            module_name=mod,
            baseline_module=baseline,
            optimized_module_path=latest,
            module_class=cls,
            test_suite=test_suite,
            metric_fn=metric,
            verbose=not args.quiet,
        )

        report["modules"].append(result.__dict__)

    if args.output:
        Path(args.output).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        if not args.quiet:
            print(f"Wrote report to: {args.output}")


if __name__ == "__main__":
    main()
