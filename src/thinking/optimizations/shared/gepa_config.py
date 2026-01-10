"""GEPA optimizer configuration for different reasoning modules.

This module provides optimized GEPA parameters based on module type,
complexity, and resource constraints.
"""

from __future__ import annotations

from typing import Dict, Literal


ModuleType = Literal[
    "direct",
    "chain_of_thought",
    "tree_of_thoughts",
    "graph_of_thoughts",
    "atom_of_thoughts",
    "combined",
]

ComplexityLevel = Literal["low", "medium", "high"]


def get_gepa_params_for_module(
    module_name: ModuleType, complexity: ComplexityLevel = "medium"
) -> Dict[str, str | int]:
    """Get optimized GEPA parameters based on module type and complexity.

    Args:
        module_name: Type of reasoning module being optimized
        complexity: Expected complexity of the optimization task

    Returns:
        Dictionary of GEPA parameters

    Examples:
        >>> get_gepa_params_for_module("direct", "medium")
        {'auto': 'light', 'max_bootstrapped_demos': 8}
    """
    base_params: Dict[str, str | int] = {
        "auto": "light",
        "max_bootstrapped_demos": 8,
    }

    # Module-specific tuning
    if module_name == "graph_of_thoughts":
        # GOT is complex, reduce optimization intensity to save resources
        base_params.update(
            {
                "auto": "light",
                "max_bootstrapped_demos": 4,
            }
        )
    elif module_name == "tree_of_thoughts":
        # ToT involves branching, moderate intensity
        base_params.update(
            {
                "auto": "light",
                "max_bootstrapped_demos": 6,
            }
        )
    elif module_name == "chain_of_thought":
        # CoT is straightforward, can use higher intensity
        base_params.update(
            {
                "auto": "medium",
                "max_bootstrapped_demos": 10,
            }
        )
    elif module_name == "atom_of_thoughts":
        # AoT is atomic, can handle moderate intensity
        base_params.update(
            {
                "auto": "light",
                "max_bootstrapped_demos": 8,
            }
        )
    elif module_name == "combined":
        # Combined is very complex, use conservative settings
        base_params.update(
            {
                "auto": "light",
                "max_bootstrapped_demos": 4,
            }
        )

    # Complexity-based adjustments
    if complexity == "low":
        base_params["auto"] = "light"
        base_params["max_bootstrapped_demos"] = max(
            4, int(base_params["max_bootstrapped_demos"]) - 2
        )
    elif complexity == "high":
        if base_params["auto"] == "light":
            base_params["auto"] = "medium"
        base_params["max_bootstrapped_demos"] = (
            int(base_params["max_bootstrapped_demos"]) + 4
        )

    return base_params


def get_complexity_from_data_size(num_examples: int) -> ComplexityLevel:
    """Estimate task complexity based on training data size.

    Args:
        num_examples: Number of training examples

    Returns:
        Complexity level (low, medium, high)
    """
    if num_examples <= 10:
        return "low"
    elif num_examples <= 50:
        return "medium"
    else:
        return "high"


def get_gepa_params_auto(
    module_name: ModuleType, num_examples: int
) -> Dict[str, str | int]:
    """Automatically determine GEPA parameters based on module and data size.

    Args:
        module_name: Type of reasoning module
        num_examples: Number of training examples

    Returns:
        Optimized GEPA parameters
    """
    complexity = get_complexity_from_data_size(num_examples)
    return get_gepa_params_for_module(module_name, complexity)


def validate_gepa_params(params: Dict[str, str | int]) -> bool:
    """Validate GEPA parameters for correctness.

    Args:
        params: Dictionary of GEPA parameters

    Returns:
        True if parameters are valid, False otherwise
    """
    valid_budgets = ["light", "medium", "heavy"]

    if "auto" in params and params["auto"] not in valid_budgets:
        return False

    if "max_bootstrapped_demos" in params:
        demos = int(params["max_bootstrapped_demos"])
        if demos < 0 or demos > 50:
            return False

    return True


def print_gepa_config(params: Dict[str, str | int]) -> None:
    """Print GEPA configuration in human-readable format.

    Args:
        params: GEPA parameters dictionary
    """
    print("GEPA Configuration:")
    print("=" * 50)
    for key, value in sorted(params.items()):
        print(f"  {key}: {value}")
    print("=" * 50)
