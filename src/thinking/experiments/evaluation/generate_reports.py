"""Generate human-readable reports and optional visualizations.

Consumes:
- routing efficiency results JSON
- comparative routing results JSON

Produces:
- routing_efficiency_report.txt
- comparative_routing_report.txt
- optional dashboard/*.png (if matplotlib/pandas/seaborn are installed)

Run:
  python -m thinking.experiments.evaluation.generate_reports
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def _package_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_results(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def generate_routing_report(results_data: dict[str, Any], output_file: Path) -> None:
    results = results_data["results"]
    summary = results_data["test_summary"]

    top_results = sorted(results, key=lambda x: float(x["accuracy"]), reverse=True)[:5]
    best = top_results[0]

    lines: list[str] = []
    lines.append("=" * 80)
    lines.append("ROUTING EFFICIENCY TEST REPORT")
    lines.append("=" * 80)
    lines.append("")

    lines.append("SUMMARY STATISTICS")
    lines.append("-" * 30)
    lines.append(f"Total examples tested: {summary['total_examples']}")
    lines.append(f"Threshold combinations tested: {summary['total_configurations']}")
    lines.append(f"Total test duration: {summary.get('test_duration', 0):.1f}s")
    lines.append("")

    lines.append("BEST CONFIGURATION")
    lines.append("-" * 20)
    lines.append(
        f"Breadth Threshold: {best['breadth_threshold']:.2f}\nDepth Threshold: {best['depth_threshold']:.2f}"
    )
    lines.append(f"Accuracy: {best['accuracy']:.1%}")
    lines.append("")

    lines.append("TOP 5 THRESHOLD CONFIGURATIONS")
    lines.append("-" * 35)
    for i, r in enumerate(top_results, 1):
        lines.append(
            f"{i}. Breadth: {r['breadth_threshold']:.1f}, Depth: {r['depth_threshold']:.1f}"
        )
        lines.append(f"   Accuracy: {float(r['accuracy']):.1%}")
        lines.append(f"   Avg Scores: {r.get('average_scores', {})}")
    lines.append("")

    lines.append("MODE DISTRIBUTION (AVERAGED OVER CONFIGS)")
    lines.append("-" * 45)

    # Average distribution across configurations
    mode_totals = defaultdict(int)
    for r in results:
        for mode, count in r.get("mode_distribution", {}).items():
            mode_totals[mode] += int(count)

    total_predictions = sum(mode_totals.values())
    if total_predictions:
        for mode, total_count in sorted(mode_totals.items(), key=lambda x: x[1], reverse=True):
            avg_count = total_count / len(results)
            pct = (total_count / total_predictions) * 100
            lines.append(f"{mode}: {avg_count:.1f} avg predictions/config ({pct:.1f}% total)")
    else:
        lines.append("No mode distribution data present.")

    lines.append("")
    lines.append("RECOMMENDATIONS")
    lines.append("-" * 15)
    if float(best["accuracy"]) > 0.75:
        lines.append("✅ Excellent performance.")
    elif float(best["accuracy"]) > 0.70:
        lines.append("✅ Good performance; further tuning may help.")
    else:
        lines.append("❌ Suboptimal performance. Consider revisiting scoring/prompting.")

    lines.append("")
    lines.append("Suggested next steps:")
    lines.append("1. Validate best configuration on additional data")
    lines.append("2. Compare against baseline routing methods")
    lines.append("3. Analyze per-mode performance for targeted improvements")
    lines.append("4. Consider score calibration or different threshold logic")

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text("\n".join(lines) + "\n", encoding="utf-8")


def generate_comparative_report(comparison_data: dict[str, Any], output_file: Path) -> None:
    router_results: dict[str, Any] = comparison_data["router_results"]
    rankings: list[str] = comparison_data["accuracy_rankings"]
    per_mode: dict[str, Any] = comparison_data.get("per_mode_breakdown", {})

    lines: list[str] = []
    lines.append("=" * 80)
    lines.append("COMPARATIVE ROUTING ANALYSIS REPORT")
    lines.append("=" * 80)
    lines.append("")

    lines.append("OVERALL PERFORMANCE RANKINGS")
    lines.append("-" * 35)
    for i, name in enumerate(rankings, 1):
        r = router_results[name]
        lines.append(f"{i}. {name}")
        lines.append(f"   Accuracy: {float(r['accuracy']):.1%}")
        lines.append(f"   Avg latency: {float(r['average_latency']):.3f}s")

    lines.append("")
    lines.append("PER-MODE PERFORMANCE (TOP 3 ROUTERS)")
    lines.append("-" * 40)
    top_3 = rankings[:3]
    for mode in sorted(per_mode.keys()):
        lines.append(f"{mode}:")
        for name in top_3:
            acc = float(per_mode[mode].get(name, 0.0))
            lines.append(f"  - {name}: {acc:.1%}")

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text("\n".join(lines) + "\n", encoding="utf-8")


def create_performance_dashboard(
    *,
    efficiency_results: dict[str, Any],
    comparison_results: dict[str, Any],
    output_dir: Path,
) -> None:
    """Create dashboard visualizations (optional dependencies)."""

    try:
        import matplotlib.pyplot as plt  # type: ignore
        import pandas as pd  # type: ignore
        import seaborn as sns  # type: ignore
    except ImportError as e:
        raise RuntimeError(
            "Dashboard generation requires matplotlib, pandas, and seaborn." \
            " Install them and rerun with --dashboard."
        ) from e

    output_dir.mkdir(parents=True, exist_ok=True)

    # Heatmap
    results = efficiency_results["results"]
    matrix: dict[float, dict[float, float]] = defaultdict(dict)
    for r in results:
        matrix[float(r["breadth_threshold"])][float(r["depth_threshold"])]= float(r["accuracy"])

    df = pd.DataFrame(matrix).T
    df = df.reindex(sorted(df.columns), axis=1)

    plt.figure(figsize=(10, 8))
    sns.heatmap(df, annot=True, fmt=".1%", cmap="viridis")
    plt.title("Breadth/Depth Routing Accuracy Heatmap")
    plt.xlabel("Depth Threshold")
    plt.ylabel("Breadth Threshold")
    plt.tight_layout()
    plt.savefig(output_dir / "accuracy_heatmap.png", dpi=300)
    plt.close()

    # Router comparison chart
    routers = list(comparison_results["router_results"].keys())
    accuracies = [float(comparison_results["router_results"][r]["accuracy"]) for r in routers]

    plt.figure(figsize=(12, 6))
    bars = plt.bar(routers, accuracies)
    plt.title("Router Accuracy Comparison")
    plt.ylabel("Accuracy")
    plt.ylim(0, 1)
    plt.xticks(rotation=45, ha="right")

    for bar, acc in zip(bars, accuracies):
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.01,
            f"{acc:.1%}",
            ha="center",
            va="bottom",
        )

    plt.tight_layout()
    plt.savefig(output_dir / "router_comparison.png", dpi=300)
    plt.close()

    # Latency vs accuracy
    latencies = [float(comparison_results["router_results"][r]["average_latency"]) for r in routers]
    accuracies_pct = [a * 100 for a in accuracies]

    plt.figure(figsize=(8, 6))
    plt.scatter(latencies, accuracies_pct, s=100, alpha=0.7)
    for i, router in enumerate(routers):
        plt.annotate(router, (latencies[i], accuracies_pct[i]), xytext=(5, 5), textcoords="offset points")

    plt.title("Latency vs Accuracy Trade-off")
    plt.xlabel("Average Latency (seconds)")
    plt.ylabel("Accuracy (%)")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_dir / "latency_accuracy_tradeoff.png", dpi=300)
    plt.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate routing evaluation reports")
    parser.add_argument(
        "--efficiency-results",
        default=None,
        help="Path to routing_efficiency_results.json",
    )
    parser.add_argument(
        "--comparison-results",
        default=None,
        help="Path to comparative_routing_analysis.json",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Directory to write reports (default: thinking/experiments/results)",
    )
    parser.add_argument(
        "--dashboard",
        action="store_true",
        help="Also generate PNG visualizations (requires matplotlib/pandas/seaborn)",
    )

    args = parser.parse_args()

    default_dir = _package_root() / "experiments" / "results"
    output_dir = Path(args.output_dir) if args.output_dir else default_dir

    eff_path = (
        Path(args.efficiency_results)
        if args.efficiency_results
        else default_dir / "routing_efficiency_results.json"
    )
    comp_path = (
        Path(args.comparison_results)
        if args.comparison_results
        else default_dir / "comparative_routing_analysis.json"
    )

    efficiency = load_results(eff_path)
    generate_routing_report(efficiency, output_dir / "routing_efficiency_report.txt")

    if comp_path.exists():
        comparison = load_results(comp_path)
        generate_comparative_report(comparison, output_dir / "comparative_routing_report.txt")

        if args.dashboard:
            create_performance_dashboard(
                efficiency_results=efficiency,
                comparison_results=comparison,
                output_dir=output_dir / "dashboard",
            )
    else:
        comparison = None

    print(f"Wrote routing report to: {output_dir / 'routing_efficiency_report.txt'}")
    if comp_path.exists():
        print(f"Wrote comparative report to: {output_dir / 'comparative_routing_report.txt'}")
        if args.dashboard:
            print(f"Wrote dashboard to: {output_dir / 'dashboard'}")


if __name__ == "__main__":
    main()
