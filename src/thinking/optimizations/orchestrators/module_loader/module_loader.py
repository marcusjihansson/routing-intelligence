"""Core module loader for loading optimized reasoning modules."""

from __future__ import annotations

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
from thinking.optimizations.shared.model_persistence import (
    get_latest_module,
    load_optimized_module,
    list_saved_modules,
)


_MODULE_CLASS_MAP = {
    "direct": DirectAnswer,
    "cot": ChainOfThought,
    "tot": TreeOfThoughts,
    "got": GraphOfThoughts,
    "aot": AtomOfThoughts,
    "combined": CombinedReasoning,
    "classifier": AdaptiveReasoner,
}


def get_latest_module_path(optimization_path: str, module_name: str) -> str:
    """Find the latest timestamped directory for a given module name.

    Args:
        optimization_path: Base path to search for saved modules
        module_name: Name of the module to find (e.g., "cot", "classifier")

    Returns:
        Full path to the latest optimized module directory

    Raises:
        FileNotFoundError: If no optimized module found for the given name
    """
    latest = get_latest_module(module_name=module_name, save_dir=optimization_path)
    if latest is None:
        raise FileNotFoundError(
            f"No optimized module found for '{module_name}' in {optimization_path}. "
            f"Expected pattern: {module_name}_optimized_*"
        )
    return latest


def list_available_modules(optimization_path: str = "saved_modules") -> dict[str, str]:
    """List all available optimized modules.

    Args:
        optimization_path: Base path to search for saved modules

    Returns:
        Dict mapping module_name to latest_path
    """
    available = {}
    for module_name in _MODULE_CLASS_MAP.keys():
        try:
            path = get_latest_module_path(optimization_path, module_name)
            available[module_name] = path
        except FileNotFoundError:
            pass
    return available


def load_module_by_name(optimization_path: str, module_name: str):
    """Load a single optimized module by name.

    Args:
        optimization_path: Base path to search for saved modules
        module_name: Name of the module to load

    Returns:
        Loaded module instance

    Raises:
        FileNotFoundError: If no optimized module found
        ValueError: If module fails to load or is invalid
    """
    if module_name not in _MODULE_CLASS_MAP:
        raise ValueError(
            f"Unknown module name: '{module_name}'. "
            f"Valid options: {list(_MODULE_CLASS_MAP.keys())}"
        )

    module_class = _MODULE_CLASS_MAP[module_name]
    latest_path = get_latest_module_path(optimization_path, module_name)

    module, _metadata = load_optimized_module(
        module_path=latest_path, module_class=module_class, verbose=False
    )

    return module


def load_classifier(optimization_path: str) -> AdaptiveReasoner:
    """Load the optimized classifier.

    Args:
        optimization_path: Base path to search for saved modules

    Returns:
        AdaptiveReasoner instance with optimized classifier

    Raises:
        FileNotFoundError: If no optimized classifier found
    """
    latest_path = get_latest_module_path(optimization_path, "classifier")
    classifier, _metadata = load_optimized_module(
        module_path=latest_path, module_class=AdaptiveReasoner, verbose=False
    )
    return classifier


def load_gepa(optimization_path: str = "saved_modules", module: str | None = None):
    """Load optimized reasoning modules.

    If module is specified, loads only that specific optimized module.
    If module is None, loads all available optimized modules and composes them
    into an OptimizedReasoner instance.

    Args:
        optimization_path: Base path to search for saved modules
        module: Specific module name to load (e.g., "cot"), or None for all

    Returns:
        If module is specified: Standalone module instance
        If module is None: OptimizedReasoner instance with all modules

    Raises:
        FileNotFoundError: If requested module not found
        ValueError: If invalid module name or loading fails
    """
    if module is not None:
        return load_module_by_name(optimization_path, module)

    available = list_available_modules(optimization_path)

    if not available:
        raise FileNotFoundError(
            f"No optimized modules found in {optimization_path}. "
            f"Train modules first using the training scripts."
        )

    optimized_modes = {}
    metadata = {
        "classifier_path": None,
        "optimized_modes": {},
        "optimization_path": optimization_path,
    }

    if "classifier" in available:
        classifier = load_classifier(optimization_path)
        metadata["classifier_path"] = available["classifier"]
    else:
        classifier = None

    for mode_name, module_name in [
        ("DIRECT", "direct"),
        ("COT", "cot"),
        ("TOT", "tot"),
        ("GOT", "got"),
        ("AOT", "aot"),
        ("COMBINED", "combined"),
    ]:
        if module_name in available:
            mode_module = load_module_by_name(optimization_path, module_name)
            optimized_modes[mode_name] = mode_module
            metadata["optimized_modes"][mode_name] = available[module_name]

    reasoner = OptimizedReasoner(
        classifier=classifier, optimized_modes=optimized_modes, metadata=metadata
    )

    return reasoner


def load_all_optimized(optimization_path: str = "saved_modules") -> "OptimizedReasoner":
    """Load all available optimized modules and compose into a reasoner.

    Convenience wrapper for load_gepa(module=None).

    Args:
        optimization_path: Base path to search for saved modules

    Returns:
        OptimizedReasoner instance with all loaded modules

    Raises:
        FileNotFoundError: If no modules found
    """
    return load_gepa(optimization_path=optimization_path, module=None)


class OptimizedReasoner(AdaptiveReasoner):
    """AdaptiveReasoner composed of pre-optimized reasoning modules."""

    def __init__(self, classifier=None, optimized_modes=None, metadata=None):
        """Initialize OptimizedReasoner.

        Args:
            classifier: Optimized classifier (AdaptiveReasoner with optimized classifier)
            optimized_modes: Dict mapping mode_name -> optimized_module instances
            metadata: Dict with module paths, versions, and validation results
        """
        super().__init__()

        if classifier is not None:
            self.classifier = classifier.classifier

        if optimized_modes:
            for mode_name, module in optimized_modes.items():
                if mode_name in self.modes:
                    self.modes[mode_name] = module

        self._metadata = metadata or {}

    def get_module_metadata(self):
        """Return metadata about loaded optimized modules."""
        return self._metadata

    def get_optimized_modes(self):
        """Return list of mode names that use optimized modules."""
        return list(self._metadata.get("optimized_modes", {}).keys())

    def get_unoptimized_modes(self):
        """Return list of mode names still using default modules."""
        optimized = set(self.get_optimized_modes())
        return [mode for mode in self.modes if mode not in optimized]
