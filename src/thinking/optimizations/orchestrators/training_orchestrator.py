"""Orchestrator for training the classifier and/or reasoning modules.

This provides a single entrypoint for training tasks.
"""

from __future__ import annotations

import argparse
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

import dspy

from thinking.core.reasoning_router import AdaptiveReasoner
from thinking.optimizations.atom_of_thoughts.training import train_aot_module
from thinking.optimizations.chain_of_thought.training import train_cot_module
from thinking.optimizations.combined.training import train_combined_module
from thinking.optimizations.direct.training import train_direct_module
from thinking.optimizations.graph_of_thoughts.training import train_got_module
from thinking.optimizations.tree_of_thoughts.training import train_tot_module
from thinking.optimizations.shared.data_generation import SyntheticDataGenerator
from thinking.optimizations.shared.metrics import classifier_accuracy_metric, gepa_classifier_metric
from thinking.optimizations.shared.model_persistence import (
    create_training_summary,
    save_optimized_module,
)
from thinking.optimizations.shared.openrouter_config import configure_openrouter_lm


@dataclass(frozen=True)
class TrainingResults:
    classifier: Optional[AdaptiveReasoner]
    modules: Dict[str, Any]


def train_classifier(
    *,
    lm: dspy.LM,
    num_examples: int = 120,
    auto_budget: str = "medium",
    max_bootstrapped_demos: int = 8,
    save_dir: str = ".",
    verbose: bool = True,
) -> AdaptiveReasoner:
    """Train/optimize the AdaptiveReasoner classifier prompt."""

    dspy.settings.configure(lm=lm)

    generator = SyntheticDataGenerator()
    trainset = generator.generate_classifier_data(num_examples_per_mode=max(1, num_examples // 6))

    split_point = int(0.8 * len(trainset))
    train_examples = trainset[:split_point]
    val_examples = trainset[split_point:]

    reasoner = AdaptiveReasoner()

    start_time = time.time()

    try:
        from dspy.teleprompt import GEPA

        optimizer = GEPA(metric=gepa_classifier_metric, auto=auto_budget, reflection_lm=lm)
        optimized_classifier = optimizer.compile(
            reasoner.classifier, trainset=train_examples, valset=val_examples
        )
        reasoner.classifier = optimized_classifier
        optimizer_name = "GEPA"
    except Exception as e:
        if verbose:
            print(f"GEPA not available or failed ({e}); falling back to BootstrapFewShot")
        from dspy.teleprompt import BootstrapFewShot

        optimizer = BootstrapFewShot(
            metric=classifier_accuracy_metric,
            max_bootstrapped_demos=max_bootstrapped_demos,
            max_labeled_demos=max_bootstrapped_demos * 2,
        )
        optimized_classifier = optimizer.compile(reasoner.classifier, trainset=train_examples)
        reasoner.classifier = optimized_classifier
        optimizer_name = "BootstrapFewShot"

    training_time = time.time() - start_time

    metadata = create_training_summary(
        module_name="classifier",
        num_examples=len(train_examples),
        auto_budget=auto_budget,
        training_time=training_time,
        additional_info={"optimizer": optimizer_name},
    )

    save_optimized_module(
        module=reasoner,
        module_name="classifier",
        save_dir=save_dir,
        metadata=metadata,
        verbose=verbose,
    )

    return reasoner


class TrainingOrchestrator:
    def __init__(self, *, lm: dspy.LM):
        self.lm = lm

    def run_training(
        self,
        *,
        include_classifier: bool = True,
        include_modules: bool = True,
        num_examples: int = 120,
        auto_budget: str = "medium",
        save_dir: str = ".",
        verbose: bool = True,
    ) -> Dict[str, Any]:
        """Train classifier and/or all reasoning modules."""

        dspy.settings.configure(lm=self.lm)

        out: Dict[str, Any] = {}

        if include_classifier:
            out["classifier"] = train_classifier(
                lm=self.lm,
                num_examples=num_examples,
                auto_budget=auto_budget,
                save_dir=save_dir,
                verbose=verbose,
            )

        if include_modules:
            out["direct"] = train_direct_module(lm=self.lm, save_dir=save_dir, verbose=verbose)
            out["cot"] = train_cot_module(lm=self.lm, save_dir=save_dir, verbose=verbose)
            out["tot"] = train_tot_module(lm=self.lm, save_dir=save_dir, verbose=verbose)
            out["got"] = train_got_module(lm=self.lm, save_dir=save_dir, verbose=verbose)
            out["aot"] = train_aot_module(lm=self.lm, save_dir=save_dir, verbose=verbose)
            out["combined"] = train_combined_module(lm=self.lm, save_dir=save_dir, verbose=verbose)

        return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Train classifier/modules via orchestrator")
    parser.add_argument("--model", default="openrouter/openai/gpt-4o")
    parser.add_argument("--save-dir", default=".")
    parser.add_argument("--budget", default="medium", choices=["light", "medium", "heavy"])
    parser.add_argument("--no-classifier", action="store_true")
    parser.add_argument("--no-modules", action="store_true")
    args = parser.parse_args()

    lm = configure_openrouter_lm(model=args.model)
    if lm is None:
        raise SystemExit("OPENROUTER_API_KEY not set")

    orchestrator = TrainingOrchestrator(lm=lm)
    orchestrator.run_training(
        include_classifier=not args.no_classifier,
        include_modules=not args.no_modules,
        auto_budget=args.budget,
        save_dir=args.save_dir,
        verbose=True,
    )


if __name__ == "__main__":
    main()
