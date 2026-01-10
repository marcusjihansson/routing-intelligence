"""Quick test of module loader functionality."""

from thinking.optimizations.orchestrators import (
    load_gepa,
    load_all_optimized,
    list_available_modules,
    validate_single_module,
)

OPTIMIZATION_PATH = "src/thinking/optimizations/saved_modules"


def test_list_modules():
    """Test listing available modules."""
    available = list_available_modules(OPTIMIZATION_PATH)
    print(f"✓ Found {len(available)} available modules")
    assert len(available) > 0, "Should find at least one module"
    return available


def test_load_single_module(available):
    """Test loading a single module."""
    if "cot" not in available:
        print("⚠ Skipping single module test - COT not available")
        return None

    cot = load_gepa(optimization_path=OPTIMIZATION_PATH, module="cot")
    assert cot is not None, "Should load COT module"
    print(f"✓ Loaded single module: {type(cot).__name__}")
    return cot


def test_load_all_modules(available):
    """Test loading all modules into OptimizedReasoner."""
    reasoner = load_all_optimized(optimization_path=OPTIMIZATION_PATH)
    assert reasoner is not None, "Should load OptimizedReasoner"
    assert hasattr(reasoner, "get_optimized_modes"), (
        "Should have optimized modes method"
    )
    print(
        f"✓ Loaded OptimizedReasoner with {len(reasoner.get_optimized_modes())} optimized modes"
    )
    return reasoner


def test_optimized_reasoner_methods(reasoner):
    """Test OptimizedReasoner utility methods."""
    optimized = reasoner.get_optimized_modes()
    unoptimized = reasoner.get_unoptimized_modes()

    assert isinstance(optimized, list), "Optimized modes should be a list"
    assert isinstance(unoptimized, list), "Unoptimized modes should be a list"
    assert len(optimized) > 0, "Should have at least one optimized mode"

    print(f"✓ OptimizedReasoner methods work")
    print(f"  Optimized: {optimized}")
    print(f"  Unoptimized: {unoptimized}")


def test_metadata(reasoner):
    """Test metadata access."""
    metadata = reasoner.get_module_metadata()

    assert isinstance(metadata, dict), "Metadata should be a dict"
    assert "optimization_path" in metadata, "Should have optimization_path"

    print(f"✓ Metadata accessible")
    print(f"  Path: {metadata.get('optimization_path')}")


def test_validation_module(module):
    """Test validation (without API key)."""
    if module is None:
        print("⚠ Skipping validation - no module loaded")
        return

    result = validate_single_module(
        module=module, module_name="cot", num_test_questions=2, verbose=False
    )

    assert isinstance(result, dict), "Result should be a dict"
    assert "valid" in result, "Result should have 'valid' key"

    print(f"✓ Validation test passed (skipped if no API key)")


def main():
    """Run all tests."""
    print("Testing Module Loader\n")

    try:
        available = test_list_modules()
        cot = test_load_single_module(available)
        reasoner = test_load_all_modules(available)
        test_optimized_reasoner_methods(reasoner)
        test_metadata(reasoner)
        test_validation_module(cot)

        print("\n✓ All tests passed!")
        return 0

    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
