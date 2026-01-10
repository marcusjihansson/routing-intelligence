"""Threshold optimization and analysis.

Consumes the JSON produced by `routing_efficiency_test` and produces:
- a human-readable text report
- a threshold matrix JSON (accuracy grid)

Run:
  python -m thinking.experiments.evaluation.threshold_optimization --criteria balanced
"""

from __future__ import annotations

import argparse
import json
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any


def _package_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_results_data(results_file: Path) -> dict[str, Any]:
    return json.loads(results_file.read_text(encoding="utf-8"))


def analyze_threshold_sensitivity(results_data: dict[str, Any]) -> dict[str, Any]:
    results = results_data["results"]

    breadth_sensitivity: dict[float, list[float]] = defaultdict(list)
    depth_sensitivity: dict[float, list[float]] = defaultdict(list)

    for r in results:
        breadth_sensitivity[float(r["breadth_threshold"])].append(float(r["accuracy"]))
        depth_sensitivity[float(r["depth_threshold"])].append(float(r["accuracy"]))

    def _stats(values: list[float]) -> dict[str, float | int]:
        return {
            "mean_accuracy": float(statistics.mean(values)),
            "std_accuracy": float(statistics.stdev(values)) if len(values) > 1 else 0.0,
            "min_accuracy": float(min(values)),
            "max_accuracy": float(max(values)),
            "sample_count": len(values),
        }

    breadth_stats = {k: _stats(v) for k, v in breadth_sensitivity.items()}
    depth_stats = {k: _stats(v) for k, v in depth_sensitivity.items()}

    # Simple stability ranking: accuracy penalized by average std across its breadth/depth bucket
    stability_scores: list[dict[str, float]] = []
    for r in results:
        b = float(r["breadth_threshold"])
        d = float(r["depth_threshold"])
        acc = float(r["accuracy"])

        stability = acc - (breadth_stats[b]["std_accuracy"] + depth_stats[d]["std_accuracy"]) / 2
        stability_scores.append(
            {
                "breadth_threshold": b,
                "depth_threshold": d,
                "accuracy": acc,
                "stability_score": float(stability),
            }
        )

    stability_scores.sort(key=lambda x: x["stability_score"], reverse=True)

    return {
        "breadth_sensitivity": breadth_stats,
        "depth_sensitivity": depth_stats,
        "most_stable_configurations": stability_scores[:10],
        "optimal_configuration": stability_scores[0] if stability_scores else None,
    }


def find_optimal_thresholds(
    results_data: dict[str, Any], optimization_criteria: str = "accuracy"
) -> dict[str, Any]:
    results = results_data["results"]

    if optimization_criteria == "accuracy":
        best = max(results, key=lambda r: float(r["accuracy"]))
        reasoning = "Maximum routing accuracy"
    elif optimization_criteria == "stability":
        sens = analyze_threshold_sensitivity(results_data)
        best = sens["optimal_configuration"]
        if best is None:
            raise RuntimeError("No results available to optimize")
        reasoning = "Best balance of accuracy and stability"
    elif optimization_criteria == "balanced":
        # Prefer >= 70% if present; otherwise fall back to max accuracy.
        candidates = [r for r in results if float(r["accuracy"]) >= 0.70]
        if candidates:
            best = max(candidates, key=lambda r: float(r["accuracy"]))
            reasoning = "High accuracy (≥70%)"
        else:
            best = max(results, key=lambda r: float(r["accuracy"]))
            reasoning = "Highest accuracy (no configurations met 70% threshold)"
    else:
        raise ValueError(f"Unknown optimization criteria: {optimization_criteria}")

    return {
        "optimal_breadth_threshold": float(best["breadth_threshold"]),
        "optimal_depth_threshold": float(best["depth_threshold"]),
        "expected_accuracy": float(best["accuracy"]),
        "optimization_criteria": optimization_criteria,
        "reasoning": reasoning,
        "configuration_details": best,
    }


def analyze_mode_routing_patterns(results_data: dict[str, Any]) -> dict[str, Any]:
    results = results_data["results"]

    mode_patterns: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for r in results:
        mode_dist: dict[str, int] = r.get("mode_distribution", {})
        total = sum(mode_dist.values())
        for mode, count in mode_dist.items():
            pct = (count / total) if total else 0.0
            mode_patterns[mode].append(
                {
                    "breadth_threshold": float(r["breadth_threshold"]),
                    "depth_threshold": float(r["depth_threshold"]),
                    "percentage": float(pct),
                    "count": int(count),
                    "accuracy": float(r["accuracy"]),
                }
            )

    mode_analysis: dict[str, Any] = {}
    mode_favoring_configs: dict[str, Any] = {}

    for mode, patterns in mode_patterns.items():
        percentages = [p["percentage"] for p in patterns]
        mode_analysis[mode] = {
            "avg_percentage": float(statistics.mean(percentages)) if percentages else 0.0,
            "std_percentage": float(statistics.stdev(percentages)) if len(percentages) > 1 else 0.0,
            "min_percentage": float(min(percentages)) if percentages else 0.0,
            "max_percentage": float(max(percentages)) if percentages else 0.0,
            "sample_count": len(patterns),
        }

        mode_favoring_configs[mode] = sorted(
            patterns, key=lambda p: p["percentage"], reverse=True
        )[:3]

    return {
        "mode_analysis": mode_analysis,
        "mode_favoring_configurations": mode_favoring_configs,
        "total_configurations_analyzed": len(results),
    }


def _threshold_matrix(results_data: dict[str, Any]) -> dict[str, Any]:
    results = results_data["results"]
    matrix: dict[str, dict[str, float]] = defaultdict(dict)

    for r in results:
        b = str(r["breadth_threshold"])
        d = str(r["depth_threshold"])
        matrix[b][d] = float(r["accuracy"])

    return {"accuracy_matrix": matrix}


def generate_threshold_optimization_report(
    *,
    results_file: Path,
    output_report: Path,
    output_matrix: Path,
    optimization_criteria: str = "balanced",
) -> None:
    results_data = load_results_data(results_file)

    optimal = find_optimal_thresholds(results_data, optimization_criteria)
    sensitivity = analyze_threshold_sensitivity(results_data)
    mode_patterns = analyze_mode_routing_patterns(results_data)

    # Write matrix JSON
    output_matrix.parent.mkdir(parents=True, exist_ok=True)
    output_matrix.write_text(
        json.dumps(_threshold_matrix(results_data), indent=2), encoding="utf-8"
    )

    # Build report
    lines: list[str] = []
    lines.append("=" * 80)
    lines.append("THRESHOLD OPTIMIZATION ANALYSIS REPORT")
    lines.append("=" * 80)
    lines.append("")

    lines.append("OPTIMIZATION SUMMARY")
    lines.append("-" * 25)
    lines.append(f"Optimization Criteria: {optimization_criteria}")
    lines.append(f"Total Configurations Analyzed: {len(results_data['results'])}")
    lines.append("")

    lines.append("RECOMMENDED CONFIGURATION")
    lines.append("-" * 30)
    lines.append(f"Breadth Threshold: {optimal['optimal_breadth_threshold']:.2f}")
    lines.append(f"Depth Threshold: {optimal['optimal_depth_threshold']:.2f}")
    lines.append(f"Expected Accuracy: {optimal['expected_accuracy']:.1%}")
    lines.append(f"Reasoning: {optimal['reasoning']}")
    lines.append("")

    lines.append("THRESHOLD SENSITIVITY ANALYSIS")
    lines.append("-" * 35)
    lines.append("Breadth Threshold Impact:")
    for thresh in sorted(sensitivity["breadth_sensitivity"].keys(), key=float):
        stats = sensitivity["breadth_sensitivity"][thresh]
        lines.append(
            f"  Threshold {float(thresh):.1f}: Mean {stats['mean_accuracy']:.1%} (n={stats['sample_count']})"
        )

    lines.append("")
    lines.append("Depth Threshold Impact:")
    for thresh in sorted(sensitivity["depth_sensitivity"].keys(), key=float):
        stats = sensitivity["depth_sensitivity"][thresh]
        lines.append(
            f"  Threshold {float(thresh):.1f}: Mean {stats['mean_accuracy']:.1%} (n={stats['sample_count']})"
        )

    lines.append("")
    lines.append("MODE ROUTING PATTERNS")
    lines.append("-" * 25)
    for mode, stats in sorted(mode_patterns["mode_analysis"].items()):
        lines.append(f"{mode}:")
        lines.append(f"  Avg Percentage: {stats['avg_percentage']:.1%}")
        lines.append(f"  Std Deviation: {stats['std_percentage']:.1%}")
        lines.append("")

    lines.append("RECOMMENDATIONS")
    lines.append("-" * 18)
    best_acc = optimal["expected_accuracy"]
    if best_acc > 0.75:
        lines.append("✅ Excellent performance. Breadth/depth routing looks promising.")
    elif best_acc > 0.70:
        lines.append("✅ Good performance. Further tuning may improve results.")
    else:
        lines.append("❌ Suboptimal performance - revisit scoring approach or data quality")

    stable = sensitivity.get("optimal_configuration")
    if stable is not None:
        lines.append("")
        lines.append(
            f"Stability Note: most stable config: {stable['breadth_threshold']}/{stable['depth_threshold']} "
            f"(acc: {stable['accuracy']:.1%}, stability: {stable['stability_score']:.3f})"
        )

    lines.append("")
    lines.append("Next Steps:")
    lines.append("1. Validate optimal configuration on additional test data")
    lines.append("2. Compare with baseline routing methods")
    lines.append("3. Consider score calibration or different threshold logic")
    lines.append("4. Evaluate performance on real user queries")

    output_report.parent.mkdir(parents=True, exist_ok=True)
    output_report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze threshold sweep results")
    parser.add_argument(
        "--criteria",
        default="balanced",
        choices=["accuracy", "stability", "balanced"],
        help="Optimization criteria",
    )
    parser.add_argument(
        "--results",
        default=None,
        help="Path to routing_efficiency_results.json (default: thinking/experiments/results/routing_efficiency_results.json)",
    )
    parser.add_argument(
        "--output-report",
        default=None,
        help="Path to write threshold optimization report (default: thinking/experiments/results/threshold_optimization_report.txt)",
    )
    parser.add_argument(
        "--output-matrix",
        default=None,
        help="Path to write threshold matrix json (default: thinking/experiments/results/threshold_matrix.json)",
    )
    args = parser.parse_args()

    default_results = _package_root() / "experiments" / "results" / "routing_efficiency_results.json"
    default_report = _package_root() / "experiments" / "results" / "threshold_optimization_report.txt"
    default_matrix = _package_root() / "experiments" / "results" / "threshold_matrix.json"

    results_path = Path(args.results) if args.results else default_results
    report_path = Path(args.output_report) if args.output_report else default_report
    matrix_path = Path(args.output_matrix) if args.output_matrix else default_matrix

    generate_threshold_optimization_report(
        results_file=results_path,
        output_report=report_path,
        output_matrix=matrix_path,
        optimization_criteria=args.criteria,
    )

    print(f"Wrote report: {report_path}")
    print(f"Wrote matrix: {matrix_path}")


if __name__ == "__main__":
    main()
