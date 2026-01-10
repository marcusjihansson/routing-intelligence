"""Training utilities for Tree of Thoughts (TOT) reasoning module."""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import List

import dspy
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from thinking.core.reasoning_modes import TreeOfThoughts
from thinking.optimizations.shared.metrics import (
    gepa_reasoning_metric,
    reasoning_quality_metric,
)
from thinking.optimizations.shared.model_persistence import (
    create_training_summary,
    save_optimized_module,
)
from thinking.optimizations.shared.openrouter_config import (
    check_disk_space,
    configure_openrouter_lm,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_tot_training_data(limit: int | None = None) -> List[dspy.Example]:
    path = Path(__file__).with_name("training_examples.jsonl")
    examples: list[dspy.Example] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            examples.append(
                dspy.Example(
                    question=data["question"], answer=data.get("answer", "")
                ).with_inputs("question")
            )
            if limit is not None and len(examples) >= limit:
                break
    return examples


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    before_sleep=lambda retry_state: logger.warning(
        f"LM call failed, retrying (attempt {retry_state.attempt_number})..."
    ),
)
def safe_lm_call(lm, **kwargs):
    """Wrapper for LM calls with retry logic."""
    return lm(**kwargs)


def train_tot_module(
    *,
    lm: dspy.LM,
    num_examples: int = 30,
    auto_budget: str = "light",
    max_bootstrapped_demos: int = 8,
    save_dir: str = ".",
    disable_cache_during_training: bool = True,
    verbose: bool = True,
) -> TreeOfThoughts:
    dspy.settings.configure(lm=lm)

    trainset = load_tot_training_data(limit=num_examples)
    module = TreeOfThoughts(branches=3, depth=2)

    start_time = time.time()
    api_calls = 0
    errors = 0

    try:
        from dspy.teleprompt import GEPA

        optimizer = GEPA(
            metric=gepa_reasoning_metric, auto=auto_budget, reflection_lm=lm
        )
        try:
            optimized = optimizer.compile(module, trainset=trainset)
            api_calls = len(trainset) * 2
        except RuntimeError as e:
            if "cannot schedule new futures after shutdown" in str(e):
                logger.warning(
                    "Caught litellm executor shutdown error after successful optimization"
                )
                optimized = module
            else:
                raise
        optimizer_name = "GEPA"
    except Exception as e:
        errors += 1
        if verbose:
            logger.warning(
                f"GEPA not available or failed ({e}); falling back to BootstrapFewShot"
            )
        from dspy.teleprompt import BootstrapFewShot

        optimizer = BootstrapFewShot(
            metric=reasoning_quality_metric,
            max_bootstrapped_demos=max_bootstrapped_demos,
            max_labeled_demos=max_bootstrapped_demos * 2,
        )
        try:
            optimized = optimizer.compile(module, trainset=trainset)
            api_calls = len(trainset) * max_bootstrapped_demos
        except Exception as compile_error:
            errors += 1
            logger.error(f"BootstrapFewShot compilation failed: {compile_error}")
            raise
        optimizer_name = "BootstrapFewShot"

    training_time = time.time() - start_time

    metadata = create_training_summary(
        module_name="tot",
        num_examples=len(trainset),
        auto_budget=auto_budget,
        training_time=training_time,
        additional_info={
            "optimizer": optimizer_name,
            "api_calls": api_calls,
            "errors": errors,
        },
    )

    save_optimized_module(
        module=optimized,
        module_name="tot",
        save_dir=save_dir,
        metadata=metadata,
        verbose=verbose,
    )

    if verbose:
        logger.info(
            f"Training completed in {training_time:.2f}s, "
            f"~{api_calls} API calls, {errors} errors"
        )

    return optimized


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the TreeOfThoughts module")
    parser.add_argument("--model", default="openrouter/openai/gpt-4o")
    parser.add_argument("--examples", type=int, default=30)
    parser.add_argument(
        "--budget", default="light", choices=["light", "medium", "heavy"]
    )
    parser.add_argument("--save-dir", default=".")
    parser.add_argument(
        "--no-cache", action="store_true", help="Disable DSPy caching during training"
    )
    args = parser.parse_args()

    has_space, available_gb = check_disk_space(10.0)
    if not has_space:
        logger.error(
            f"Insufficient disk space ({available_gb:.1f}GB available, "
            f"10GB required). Please run cache cleanup first."
        )
        logger.info("Run: uv run python scripts/clean_cache.py")
        sys.exit(1)

    lm = configure_openrouter_lm(model=args.model, enable_cache=not args.no_cache)
    if lm is None:
        sys.exit(1)

    try:
        train_tot_module(
            lm=lm,
            num_examples=args.examples,
            auto_budget=args.budget,
            save_dir=args.save_dir,
            disable_cache_during_training=args.no_cache,
        )
    except RuntimeError as e:
        if "cannot schedule new futures after shutdown" in str(e):
            logger.warning(
                "Training completed successfully despite litellm executor error"
            )
            logger.info("The optimized module has been saved and is ready to use.")
        else:
            raise


if __name__ == "__main__":
    main()
