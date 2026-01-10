"""Validation utilities for loaded optimized modules."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import dspy

from thinking.optimizations.shared.data_generation import SyntheticDataGenerator
from thinking.optimizations.shared.openrouter_config import configure_openrouter_lm


def _ensure_lm_configured() -> dspy.LM | None:
    """Ensure LM is configured, return None if not available."""
    if dspy.settings.lm is not None:
        return dspy.settings.lm

    lm = configure_openrouter_lm(verbose=False)
    if lm is None:
        print(
            "Warning: OPENROUTER_API_KEY not found - skipping actual validation tests."
        )
        print("Set it with: export OPENROUTER_API_KEY='sk-or-v1-...'\n")
    return lm


def validate_module_compatibility(
    classifier_path: str | None, module_paths_dict: dict[str, str], verbose: bool = True
) -> dict[str, Any]:
    """Validate that all modules exist and have valid structure.

    Args:
        classifier_path: Path to optimized classifier (or None)
        module_paths_dict: Dict mapping mode_name -> module_path
        verbose: Print validation details

    Returns:
        Dict with validation results including validity, errors, warnings, and details
    """
    result = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "details": {
            "classifier": {"exists": False, "valid": False, "errors": []},
            "modes": {},
        },
    }

    def _validate_path(path: str, expected_type: str | None = None) -> dict:
        """Validate a single module path."""
        local_result = {"exists": False, "valid": False, "errors": []}
        path_obj = Path(path)

        if not path_obj.exists():
            local_result["errors"].append(f"Path does not exist: {path}")
            return local_result

        local_result["exists"] = True

        module_file = path_obj / "module.json"
        metadata_file = path_obj / "metadata.json"

        if not module_file.exists():
            local_result["errors"].append(f"Missing module.json in {path}")
            return local_result

        if not metadata_file.exists():
            local_result["warnings"] = local_result.get("warnings", [])
            local_result["warnings"].append(f"Missing metadata.json in {path}")

        if expected_type:
            try:
                metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
                module_type = metadata.get("module_type")
                if module_type != expected_type:
                    local_result["errors"].append(
                        f"Module type mismatch: expected {expected_type}, got {module_type}"
                    )
                    return local_result
            except Exception as e:
                local_result["errors"].append(f"Failed to read metadata: {e}")
                return local_result

        local_result["valid"] = True
        if "warnings" in local_result and local_result["warnings"]:
            local_result["valid"] = True
        else:
            local_result["valid"] = not local_result["errors"]

        return local_result

    if classifier_path:
        if verbose:
            print(f"Validating classifier: {classifier_path}")
        classifier_result = _validate_path(classifier_path, "AdaptiveReasoner")
        result["details"]["classifier"] = classifier_result

        if not classifier_result["valid"]:
            result["valid"] = False
            result["errors"].extend(classifier_result["errors"])
        elif "warnings" in classifier_result:
            result["warnings"].extend(classifier_result.get("warnings", []))
    elif verbose:
        print("No classifier provided - skipping validation")

    for mode_name, mode_path in module_paths_dict.items():
        if verbose:
            print(f"Validating mode {mode_name}: {mode_path}")
        mode_result = _validate_path(mode_path)
        result["details"]["modes"][mode_name] = mode_result

        if not mode_result["valid"]:
            result["valid"] = False
            result["errors"].extend(mode_result["errors"])
        elif "warnings" in mode_result:
            result["warnings"].extend(mode_result.get("warnings", []))

    if verbose:
        if result["valid"]:
            print("✓ All modules validated successfully")
        else:
            print("✗ Validation failed:")
            for error in result["errors"]:
                print(f"  - {error}")
            for warning in result["warnings"]:
                print(f"  ! {warning}")

    return result


def validate_single_module(
    module: dspy.Module,
    module_name: str,
    num_test_questions: int = 3,
    verbose: bool = True,
) -> dict[str, Any]:
    """Validate a single module can execute on test questions.

    Args:
        module: Module instance to validate
        module_name: Name of the module (for test data generation)
        num_test_questions: Number of test questions to run
        verbose: Print validation details

    Returns:
        Dict with validation results
    """
    lm = _ensure_lm_configured()
    if lm is None:
        return {
            "valid": True,
            "success_rate": 1.0,
            "test_cases": 0,
            "successful": 0,
            "errors": [],
            "trace": [],
            "skipped": True,
            "skip_reason": "No LM configured (OPENROUTER_API_KEY not set)",
        }

    generator = SyntheticDataGenerator()

    mode_questions_map = {
        "direct": generator.generate_classifier_data(
            num_examples_per_mode=num_test_questions
        ),
        "cot": generator.generate_classifier_data(
            num_examples_per_mode=num_test_questions
        ),
        "tot": generator.generate_classifier_data(
            num_examples_per_mode=num_test_questions
        ),
        "got": generator.generate_classifier_data(
            num_examples_per_mode=num_test_questions
        ),
        "aot": generator.generate_classifier_data(
            num_examples_per_mode=num_test_questions
        ),
        "combined": generator.generate_classifier_data(
            num_examples_per_mode=num_test_questions
        ),
    }

    test_data = mode_questions_map.get(module_name, [])

    if not test_data:
        if verbose:
            print(f"Warning: No test data available for module '{module_name}'")

    result = {
        "valid": True,
        "success_rate": 0.0,
        "test_cases": len(test_data),
        "successful": 0,
        "errors": [],
        "trace": [],
    }

    for i, example in enumerate(test_data[:num_test_questions], 1):
        trace_entry = {
            "test_num": i,
            "question": example.question,
            "success": False,
            "error": None,
        }

        try:
            output = module(question=example.question)

            if hasattr(output, "answer") and output.answer:
                trace_entry["success"] = True
                result["successful"] += 1
            else:
                trace_entry["error"] = "No valid answer in output"
                result["errors"].append(
                    f"Test {i}: No valid answer for '{example.question}'"
                )

        except Exception as e:
            trace_entry["error"] = str(e)
            result["errors"].append(f"Test {i}: Exception - {e}")

        result["trace"].append(trace_entry)

        if verbose and i % 5 == 0:
            print(f"  Progress: {i}/{min(num_test_questions, len(test_data))}")

    result["success_rate"] = (
        result["successful"] / result["test_cases"] if result["test_cases"] else 1.0
    )
    result["valid"] = result["success_rate"] > 0.0

    if verbose:
        print(f"\nModule '{module_name}' validation:")
        print(
            f"  Success rate: {result['success_rate']:.1%} ({result['successful']}/{result['test_cases']})"
        )
        if result["valid"]:
            print(f"  ✓ Module validation passed")
        else:
            print(f"  ✗ Module validation failed:")
            for error in result["errors"][:5]:
                print(f"    - {error}")
            if len(result["errors"]) > 5:
                print(f"    ... and {len(result['errors']) - 5} more errors")

    return result


def validate_reasoner_composition(
    reasoner: dspy.Module,
    test_questions_per_mode: int = 3,
    verbose: bool = True,
) -> dict[str, Any]:
    """Validate complete composed reasoning system.

    Args:
        reasoner: OptimizedReasoner instance to validate
        test_questions_per_mode: Number of test questions per mode
        verbose: Print validation details

    Returns:
        Dict with validation results
    """
    lm = _ensure_lm_configured()
    if lm is None:
        return {
            "valid": True,
            "overall_success_rate": 1.0,
            "mode_success_rates": {},
            "test_cases": 0,
            "errors": [],
            "warnings": [],
            "trace": [],
            "skipped": True,
            "skip_reason": "No LM configured (OPENROUTER_API_KEY not set)",
        }

    generator = SyntheticDataGenerator()

    mode_questions_map = {
        "DIRECT": generator.generate_classifier_data(
            num_examples_per_mode=test_questions_per_mode
        ),
        "COT": generator.generate_classifier_data(
            num_examples_per_mode=test_questions_per_mode
        ),
        "TOT": generator.generate_classifier_data(
            num_examples_per_mode=test_questions_per_mode
        ),
        "GOT": generator.generate_classifier_data(
            num_examples_per_mode=test_questions_per_mode
        ),
        "AOT": generator.generate_classifier_data(
            num_examples_per_mode=test_questions_per_mode
        ),
        "COMBINED": generator.generate_classifier_data(
            num_examples_per_mode=test_questions_per_mode
        ),
    }

    result = {
        "valid": True,
        "overall_success_rate": 0.0,
        "mode_success_rates": {},
        "test_cases": 0,
        "errors": [],
        "warnings": [],
        "trace": [],
    }

    modes_used = {}

    for mode_name, test_data in mode_questions_map.items():
        successful = 0
        total = 0

        for example in test_data[:test_questions_per_mode]:
            trace_entry = {
                "mode": mode_name,
                "question": example.question,
                "success": False,
                "error": None,
            }

            try:
                output = reasoner(question=example.question)

                total += 1

                if hasattr(output, "answer") and output.answer:
                    trace_entry["success"] = True
                    successful += 1

                    predicted_mode = str(getattr(output, "reasoning_mode", "")).upper()
                    modes_used[predicted_mode] = modes_used.get(predicted_mode, 0) + 1

                    confidence = getattr(output, "confidence", None)
                    if confidence is not None:
                        try:
                            conf_val = float(confidence)
                            if not (0.0 <= conf_val <= 1.0):
                                result["warnings"].append(
                                    f"Invalid confidence score {conf_val} for mode {mode_name}"
                                )
                        except (ValueError, TypeError):
                            pass
                else:
                    trace_entry["error"] = "No valid answer in output"
                    result["errors"].append(
                        f"Mode {mode_name}: No valid answer for '{example.question}'"
                    )

            except Exception as e:
                trace_entry["error"] = str(e)
                result["errors"].append(f"Mode {mode_name}: Exception - {e}")

            result["trace"].append(trace_entry)

        mode_success_rate = successful / total if total else 1.0
        result["mode_success_rates"][mode_name] = mode_success_rate
        result["test_cases"] += total

        if verbose:
            print(f"  Mode {mode_name}: {mode_success_rate:.1%} ({successful}/{total})")

    total_successful = sum(int(entry["success"]) for entry in result["trace"])
    result["overall_success_rate"] = (
        total_successful / result["test_cases"] if result["test_cases"] else 1.0
    )

    result["valid"] = result["overall_success_rate"] > 0.0

    if verbose:
        print(f"\nOverall success rate: {result['overall_success_rate']:.1%}")
        if result["valid"]:
            print(f"✓ Reasoner validation passed")
        else:
            print(f"✗ Reasoner validation failed:")
            for error in result["errors"][:5]:
                print(f"  - {error}")
            if len(result["errors"]) > 5:
                print(f"  ... and {len(result['errors']) - 5} more errors")

        if result["warnings"]:
            print(f"\nWarnings:")
            for warning in result["warnings"][:3]:
                print(f"  ! {warning}")

    return result
