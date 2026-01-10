"""Model persistence utilities for saving/loading optimized DSPy modules."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


def save_optimized_module(
    *,
    module: Any,
    module_name: str,
    save_dir: str = ".",
    metadata: Optional[Dict[str, Any]] = None,
    verbose: bool = True,
) -> str:
    """Save an optimized DSPy module to disk.

    The module is saved into a timestamped folder containing:
    - module.json (DSPy serialization)
    - metadata.json (training/config metadata)
    """

    save_path = Path(save_dir)
    save_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    module_dir = save_path / f"{module_name}_optimized_{timestamp}"
    module_dir.mkdir(exist_ok=True)

    module_file = module_dir / "module.json"
    module.save(str(module_file))

    meta: Dict[str, Any] = dict(metadata or {})
    meta.update(
        {
            "module_name": module_name,
            "timestamp": timestamp,
            "saved_at": datetime.now().isoformat(),
            "module_type": type(module).__name__,
        }
    )

    metadata_file = module_dir / "metadata.json"
    metadata_file.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    if verbose:
        print(f"Saved module to: {module_dir}")

    return str(module_dir)


def load_optimized_module(
    *,
    module_path: str,
    module_class: type,
    verbose: bool = True,
) -> Tuple[Any, Dict[str, Any]]:
    """Load a saved DSPy module given a module class."""

    module_dir = Path(module_path)
    if not module_dir.exists():
        raise FileNotFoundError(f"Module directory not found: {module_path}")

    module_file = module_dir / "module.json"
    if not module_file.exists():
        raise FileNotFoundError(f"Module file not found: {module_file}")

    module = module_class()
    module.load(str(module_file))

    metadata: Dict[str, Any] = {}
    metadata_file = module_dir / "metadata.json"
    if metadata_file.exists():
        metadata = json.loads(metadata_file.read_text(encoding="utf-8"))

    if verbose:
        print(f"Loaded module from: {module_dir}")

    return module, metadata


def list_saved_modules(*, module_name: Optional[str] = None, save_dir: str = ".") -> list[Dict[str, Any]]:
    save_path = Path(save_dir)
    if not save_path.exists():
        return []

    pattern = f"{module_name}_optimized_*" if module_name else "*_optimized_*"

    modules: list[Dict[str, Any]] = []
    for module_dir in save_path.glob(pattern):
        if not module_dir.is_dir():
            continue

        metadata_file = module_dir / "metadata.json"
        if metadata_file.exists():
            meta = json.loads(metadata_file.read_text(encoding="utf-8"))
            meta["path"] = str(module_dir)
            modules.append(meta)

    modules.sort(key=lambda x: x.get("saved_at", ""), reverse=True)
    return modules


def get_latest_module(*, module_name: str, save_dir: str = ".") -> Optional[str]:
    modules = list_saved_modules(module_name=module_name, save_dir=save_dir)
    return modules[0]["path"] if modules else None


def create_training_summary(
    *,
    module_name: str,
    num_examples: int,
    auto_budget: str,
    training_time: float,
    final_metric: Optional[float] = None,
    additional_info: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    summary: Dict[str, Any] = {
        "module_name": module_name,
        "training_config": {
            "num_examples": num_examples,
            "auto_budget": auto_budget,
            "training_time_seconds": training_time,
        },
    }

    if final_metric is not None:
        summary["final_metric"] = final_metric

    if additional_info:
        summary.update(additional_info)

    return summary


def print_saved_modules_summary(*, save_dir: str = ".") -> None:
    modules = list_saved_modules(save_dir=save_dir)
    if not modules:
        print(f"No saved modules found in {save_dir}")
        return

    print("=" * 80)
    print(f"SAVED MODULES IN {save_dir}")
    print("=" * 80)

    for i, meta in enumerate(modules, 1):
        print(f"\n{i}. {str(meta.get('module_name', 'unknown')).upper()}")
        print(f"   Path: {meta.get('path', 'unknown')}")
        print(f"   Saved: {meta.get('saved_at', 'unknown')}")
        print(f"   Type: {meta.get('module_type', 'unknown')}")

        cfg = meta.get("training_config", {})
        if cfg:
            t = cfg.get("training_time_seconds", 0.0)
            print(
                f"   Training: {cfg.get('num_examples', '?')} examples, {cfg.get('auto_budget', '?')} budget, {float(t):.1f}s"
            )

    print("\n" + "=" * 80)
