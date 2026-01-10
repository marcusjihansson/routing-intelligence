"""CLI orchestrator for loading optimized reasoning modules."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from thinking.optimizations.orchestrators.module_loader.module_loader import (
    OptimizedReasoner,
    list_available_modules,
    load_all_optimized,
    load_gepa,
)
from thinking.optimizations.orchestrators.module_loader.validation import (
    validate_reasoner_composition,
    validate_single_module,
)
from thinking.optimizations.shared.model_persistence import (
    create_training_summary,
    save_optimized_module,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Load optimized reasoning modules from saved_modules/"
    )

    parser.add_argument(
        "--path",
        default="saved_modules",
        help="Base path for saved modules (default: saved_modules)",
    )

    parser.add_argument(
        "--module",
        action="append",
        dest="modules",
        help="Load specific module (can be specified multiple times)",
    )

    parser.add_argument(
        "--load-all",
        action="store_true",
        help="Load all available optimized modules",
    )

    parser.add_argument(
        "--list",
        action="store_true",
        help="List available modules and exit",
    )

    parser.add_argument(
        "--validate",
        action="store_true",
        help="Run validation after loading",
    )

    parser.add_argument(
        "--test-questions",
        type=int,
        default=3,
        help="Number of test questions per mode for validation (default: 3)",
    )

    parser.add_argument(
        "--save-to",
        type=str,
        help="Save composed reasoner to this path as module.json + metadata.json",
    )

    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    try:
        if args.list:
            _list_modules(args.path, args.verbose)
            return

        if args.modules:
            _load_specific_modules(args)
        elif args.load_all or not args.modules:
            _load_all_modules(args)
        else:
            parser.print_help()

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


def _list_modules(path: str, verbose: bool) -> None:
    """List available optimized modules."""
    available = list_available_modules(path)

    print(f"Available optimized modules in {path}:")
    if not available:
        print("  (none found)")
        return

    for module_name, module_path in sorted(available.items()):
        timestamp = module_path.split("_")[-1].replace("/", "")
        print(f"  ✓ {module_name:<10} → {Path(module_path).name}")

    all_module_names = ["direct", "cot", "tot", "got", "aot", "combined", "classifier"]
    missing = [m for m in all_module_names if m not in available]
    if missing and verbose:
        print("\n  Missing optimized modules:")
        for m in missing:
            print(f"  ✗ {m:<10}")


def _load_specific_modules(args: argparse.Namespace) -> None:
    """Load specific modules specified by --module flag."""
    if args.verbose:
        print(f"Loading specific modules from: {args.path}")

    loaded_modules = {}
    for module_name in args.modules:
        if args.verbose:
            print(f"  Loading {module_name}...")

        try:
            module = load_gepa(optimization_path=args.path, module=module_name)
            loaded_modules[module_name] = module
            print(f"  ✓ Loaded {module_name}")
        except FileNotFoundError:
            print(f"  ✗ {module_name} not found in {args.path}")
            raise
        except Exception as e:
            print(f"  ✗ Failed to load {module_name}: {e}")
            raise

    if args.validate:
        if args.verbose:
            print("\nRunning validation...")

        all_valid = True
        any_skipped = False
        for module_name, module in loaded_modules.items():
            print(f"\nValidating {module_name}:")
            result = validate_single_module(
                module=module,
                module_name=module_name,
                num_test_questions=args.test_questions,
                verbose=args.verbose,
            )

            if result.get("skipped"):
                any_skipped = True
            elif not result["valid"]:
                all_valid = False

        if all_valid and not any_skipped:
            print("\n✓ All modules validated successfully")
        elif any_skipped:
            print("\n⚠ Validation skipped for some modules (no LM configured)")
        else:
            print("\n✗ Some modules failed validation")
            exit(1)


def _load_all_modules(args: argparse.Namespace) -> None:
    """Load all available optimized modules and compose into reasoner."""
    if args.verbose:
        print(f"Loading all optimized modules from: {args.path}")

    try:
        reasoner = load_all_optimized(optimization_path=args.path)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        print("\nHint: Train modules first using:", file=sys.stderr)
        print(
            "  uv run python -m thinking.optimizations.chain_of_thought.training --budget light --examples 20",
            file=sys.stderr,
        )
        exit(1)

    metadata = reasoner.get_module_metadata()
    optimized_modes = reasoner.get_optimized_modes()
    unoptimized_modes = reasoner.get_unoptimized_modes()

    print(f"\nOptimizedReasoner composed:")
    print(f"  Optimization path: {metadata.get('optimization_path', args.path)}")

    if optimized_modes:
        print(f"  Optimized modes ({len(optimized_modes)}):")
        for mode in optimized_modes:
            print(f"    ✓ {mode}")
    else:
        print("  Optimized modes: (none)")

    if unoptimized_modes and args.verbose:
        print(f"  Unoptimized modes ({len(unoptimized_modes)}):")
        for mode in unoptimized_modes:
            print(f"    - {mode}")

    if args.validate:
        if args.verbose:
            print("\nRunning validation...")

        result = validate_reasoner_composition(
            reasoner=reasoner,
            test_questions_per_mode=args.test_questions,
            verbose=args.verbose,
        )

        if not result["valid"]:
            print("\n✗ Reasoner validation failed")
            exit(1)

        metadata["validation"] = result

    if args.save_to:
        _save_reasoner(reasoner, args.save_to, metadata, args.verbose)


def _save_reasoner(
    reasoner: OptimizedReasoner,
    save_path: str,
    metadata: dict,
    verbose: bool,
) -> None:
    """Save composed reasoner to specified path."""
    save_dir = Path(save_path)
    save_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    system_name = f"optimized_system_{timestamp}"
    system_dir = save_dir / system_name
    system_dir.mkdir(exist_ok=True)

    module_file = system_dir / "module.json"
    reasoner.save(str(module_file))

    save_metadata = {
        "module_name": "optimized_reasoner",
        "type": "OptimizedReasoner",
        "timestamp": timestamp,
        "saved_at": datetime.now().isoformat(),
        "modules": metadata.get("optimized_modes", {}),
        "classifier_path": metadata.get("classifier_path"),
        "optimization_path": metadata.get("optimization_path"),
    }

    if "validation" in metadata:
        save_metadata["validation"] = {
            "valid": metadata["validation"]["valid"],
            "overall_success_rate": metadata["validation"]["overall_success_rate"],
            "mode_success_rates": metadata["validation"]["mode_success_rates"],
        }

    metadata_file = system_dir / "metadata.json"
    metadata_file.write_text(
        json.dumps(save_metadata, indent=2) + "\n", encoding="utf-8"
    )

    if verbose:
        print(f"\n✓ Saved optimized system to: {system_dir}")


if __name__ == "__main__":
    import sys

    main()
