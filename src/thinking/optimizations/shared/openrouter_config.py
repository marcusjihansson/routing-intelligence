"""OpenRouter configuration utilities.

This module provides a consistent OpenRouter setup for training/evaluation scripts.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Tuple

import dspy


def check_disk_space(min_available_gb: float = 10.0) -> Tuple[bool, float]:
    """Check if sufficient disk space is available.

    Args:
        min_available_gb: Minimum required disk space in GB

    Returns:
        (has_sufficient_space, available_gb)
    """
    try:
        result = subprocess.run(
            ["df", "-h", "/System/Volumes/Data"],
            capture_output=True,
            text=True,
            check=True,
        )
        lines = result.stdout.strip().split("\n")
        if len(lines) >= 2:
            parts = lines[1].split()
            available_str = parts[3]

            # Parse size string to GB
            available_gb = 0.0
            if available_str.endswith("Gi"):
                available_gb = float(available_str[:-2])
            elif available_str.endswith("Gi"):
                available_gb = float(available_str[:-2])
            elif available_str.endswith("G"):
                available_gb = float(available_str[:-1])

            return (available_gb >= min_available_gb, available_gb)
    except (subprocess.CalledProcessError, IndexError, ValueError):
        pass
    return (False, 0.0)


def configure_openrouter_lm(
    model: str = "openrouter/openai/gpt-4o",
    *,
    cache_dir: str | None = None,
    enable_cache: bool = True,
    verbose: bool = True,
) -> dspy.LM | None:
    """Configure DSPy with OpenRouter.

    Args:
        model: Model identifier string
        cache_dir: Path to cache directory (default: ~/.cache/dspy_optimized)
        enable_cache: Whether to enable DSPy caching
        verbose: Whether to print configuration messages

    Returns:
        A configured `dspy.LM` or `None` if no OPENROUTER_API_KEY is present.
    """

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        if verbose:
            print("Warning: OPENROUTER_API_KEY not found in environment")
            print("Set it with: export OPENROUTER_API_KEY='sk-or-v1-...'\n")
            print("Get a key at: https://openrouter.ai/keys")
        return None

    # Configure cache directory
    if enable_cache and cache_dir is None:
        cache_dir = str(Path.home() / ".cache" / "dspy_optimized")

    # Create cache directory if needed
    if enable_cache and cache_dir:
        cache_path = Path(cache_dir).expanduser()
        try:
            cache_path.mkdir(parents=True, exist_ok=True)
            if verbose:
                print(f"DSPy cache directory: {cache_path}")
        except OSError as e:
            if verbose:
                print(f"Warning: Could not create cache directory: {e}")
                print("Caching will be disabled.")
            cache_dir = None

    # Configure LM with or without caching
    if enable_cache and cache_dir:
        lm = dspy.LM(
            model=model,
            api_key=api_key,
            api_base="https://openrouter.ai/api/v1",
            cache_dir=cache_dir,
        )
    else:
        lm = dspy.LM(
            model=model, api_key=api_key, api_base="https://openrouter.ai/api/v1"
        )

    dspy.settings.configure(lm=lm)

    if verbose:
        cache_status = "enabled" if enable_cache and cache_dir else "disabled"
        print(
            f"Configured DSPy with OpenRouter model: {model} (caching {cache_status})"
        )

    return lm


def get_recommended_models() -> dict[str, str]:
    return {
        "free": "openrouter/google/gemini-2.0-flash-exp:free",
        "fast": "openrouter/openai/gpt-4o",
        "balanced": "openrouter/google/gemini-pro",
        "quality": "openrouter/anthropic/claude-3.5-sonnet",
        "default": "openrouter/openai/gpt-4o",
    }


def get_model_for_task(task: str = "default") -> str:
    models = get_recommended_models()
    return models.get(task, models["default"])


def check_openrouter_setup() -> Tuple[bool, str]:
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        return False, "OPENROUTER_API_KEY not set in environment"
    if len(api_key.strip()) < 10:
        return False, "OPENROUTER_API_KEY appears too short to be valid"
    return True, "OpenRouter configuration looks good"


def print_setup_instructions() -> None:
    print("\n" + "=" * 80)
    print("OPENROUTER SETUP INSTRUCTIONS")
    print("=" * 80)
    print("\n1) Get an API key from https://openrouter.ai/keys")
    print("\n2) Set the environment variable:")
    print("   export OPENROUTER_API_KEY='sk-or-v1-...'\n")
    print("3) Choose a model:")
    for k, v in get_recommended_models().items():
        print(f"   - {k}: {v}")
    print("\n4) Configure in your script:")
    print(
        "   from thinking.optimizations.shared.openrouter_config import configure_openrouter_lm"
    )
    print("   lm = configure_openrouter_lm()")
    print("=" * 80 + "\n")
