"""Demo script showcasing the module loader functionality."""

from thinking.optimizations.orchestrators import (
    list_available_modules,
    load_gepa,
    load_all_optimized,
    validate_single_module,
)

OPTIMIZATION_PATH = "src/thinking/optimizations/saved_modules"


def demo_list_modules():
    """Demo: List available optimized modules."""
    print("=" * 80)
    print("DEMO: Listing Available Modules")
    print("=" * 80)

    available = list_available_modules(OPTIMIZATION_PATH)

    print(f"\nFound {len(available)} optimized modules:")
    for module_name, path in available.items():
        print(f"  ✓ {module_name:<10} → {path}")

    return available


def demo_load_single_module(available_modules):
    """Demo: Load a single optimized module."""
    print("\n" + "=" * 80)
    print("DEMO: Loading Single Module")
    print("=" * 80)

    if "cot" in available_modules:
        cot_module = load_gepa(optimization_path=OPTIMIZATION_PATH, module="cot")
        print(f"\n✓ Loaded: {type(cot_module).__name__}")
        print(f"  Module type: {type(cot_module).__name__}")
        return cot_module
    else:
        print("\n✗ COT module not available")
        return None


def demo_load_all_modules(available_modules):
    """Demo: Load all optimized modules into OptimizedReasoner."""
    print("\n" + "=" * 80)
    print("DEMO: Loading All Modules")
    print("=" * 80)

    reasoner = load_all_optimized(optimization_path=OPTIMIZATION_PATH)

    print(f"\n✓ Loaded OptimizedReasoner")
    optimized = reasoner.get_optimized_modes()
    unoptimized = reasoner.get_unoptimized_modes()

    print(f"\nOptimized modes ({len(optimized)}):")
    for mode in optimized:
        print(f"  ✓ {mode}")

    if unoptimized:
        print(f"\nDefault modes ({len(unoptimized)}):")
        for mode in unoptimized:
            print(f"  - {mode}")

    metadata = reasoner.get_module_metadata()
    print(f"\nMetadata:")
    print(f"  Optimization path: {metadata.get('optimization_path')}")
    print(f"  Classifier: {metadata.get('classifier_path', 'Not loaded')}")

    return reasoner


def demo_validate_module(module):
    """Demo: Validate a single module."""
    print("\n" + "=" * 80)
    print("DEMO: Validating Single Module")
    print("=" * 80)

    print("\nNote: Validation requires OPENROUTER_API_KEY to be set")
    print("Without API key, validation will be skipped\n")

    result = validate_single_module(
        module=module, module_name="cot", num_test_questions=2, verbose=True
    )

    print(f"\nValidation result:")
    print(f"  Valid: {result.get('valid', False)}")
    print(f"  Success rate: {result.get('success_rate', 0):.1%}")

    if result.get("skipped"):
        print(f"  Skipped: {result.get('skip_reason')}")


def main():
    """Run all demos."""
    print("\n")
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║     Module Loader Demo - Optimized Reasoning System                 ║")
    print("╚══════════════════════════════════════════════════════════════════╝")

    available = demo_list_modules()

    if available:
        cot = demo_load_single_module(available)

        if cot:
            demo_validate_module(cot)

        reasoner = demo_load_all_modules(available)

        print("\n" + "=" * 80)
        print("DEMO COMPLETE")
        print("=" * 80)
        print("\nModule loader is ready to use!")
        print("\nExample usage:")
        print("  reasoner = load_all_optimized()")
        print("  result = reasoner(question='How does photosynthesis work?')")
        print("  print(result.answer, result.reasoning_mode)")
        print()

    else:
        print("\nNo optimized modules found.")
        print("Train modules first using:")
        print(
            "  uv run python -m thinking.optimizations.chain_of_thought.training"
            " --budget light --examples 20"
        )
        print()


if __name__ == "__main__":
    main()
