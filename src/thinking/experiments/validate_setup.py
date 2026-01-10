"""Validate experiment setup.

This script checks that:
- OPENROUTER_API_KEY is set (optional for some steps)
- labeled examples can be loaded
- key experiment modules import correctly

Run:
  python -m thinking.experiments.validate_setup
"""

from __future__ import annotations

import os


def main() -> None:
    print("Breadth/Depth Routing Evaluation Setup Validation")
    print("=" * 60)

    all_checks_passed = True

    # 1) API key
    print("\n1) Checking OpenRouter API Key...")
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if api_key and len(api_key.strip()) > 10:
        print(" OK: OPENROUTER_API_KEY is set")
    else:
        print(" WARN: OPENROUTER_API_KEY not found or looks invalid")
        print("       Set it with: export OPENROUTER_API_KEY='sk-or-v1-...'\n")
        # Don't fail the entire validation; some steps are offline.

    # 2) Import sanity
    print("2) Checking imports...")
    try:
        from thinking.experiments.core.breadth_depth_router import BreadthDepthRouter  # noqa: F401
        from thinking.experiments.evaluation.routing_efficiency_test import (
            load_labeled_examples,
        )
        from thinking.experiments.evaluation.comparative_routing_test import (
            compare_all_routers,
        )
        from thinking.experiments.evaluation.threshold_optimization import (
            generate_threshold_optimization_report,
        )
        from thinking.experiments.evaluation.generate_reports import (
            generate_routing_report,
        )

        print(" OK: core experiment modules import")
    except Exception as e:
        print(f" ERROR: import check failed: {e}")
        all_checks_passed = False

    # 3) Data loading
    print("\n3) Testing labeled example loading...")
    try:
        from thinking.experiments.evaluation.routing_efficiency_test import load_labeled_examples

        examples = load_labeled_examples()
        mode_counts: dict[str, int] = {}
        for ex in examples:
            mode_counts[ex.reasoning_mode] = mode_counts.get(ex.reasoning_mode, 0) + 1

        print(f" OK: loaded {len(examples)} examples")
        for mode, count in sorted(mode_counts.items()):
            print(f"   - {mode}: {count}")
    except Exception as e:
        print(f" ERROR: data loading failed: {e}")
        all_checks_passed = False

    # 4) Router instantiation
    print("\n4) Testing router instantiation...")
    try:
        from thinking.experiments.core.breadth_depth_router import BreadthDepthRouter

        router = BreadthDepthRouter()
        print(" OK: BreadthDepthRouter instantiated")
        print(
            f"     thresholds: breadth={router.breadth_threshold}, depth={router.depth_threshold}"
        )
    except Exception as e:
        print(f" ERROR: router instantiation failed: {e}")
        all_checks_passed = False

    print("\n" + "=" * 60)
    if all_checks_passed:
        print("All required checks passed.")
        print("\nSuggested next steps:")
        print("  python -m thinking.experiments.evaluation.routing_efficiency_test --quick")
        print("  python -m thinking.experiments.evaluation.comparative_routing_test")
        print("  python -m thinking.experiments.evaluation.threshold_optimization")
    else:
        print("Some checks failed; fix errors above before running evaluations.")
    print("=" * 60)


if __name__ == "__main__":
    main()
