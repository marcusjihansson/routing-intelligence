"""Orchestrator for evaluating reasoning modules and the router."""

from __future__ import annotations

import argparse
from typing import Any, Dict

import dspy

from thinking.core.reasoning_router import AdaptiveReasoner
from thinking.core.reasoning_modes import (
    AtomOfThoughts,
    ChainOfThought,
    CombinedReasoning,
    DirectAnswer,
    GraphOfThoughts,
    TreeOfThoughts,
)
from thinking.optimizations.atom_of_thoughts.evaluation import evaluate_aot_module
from thinking.optimizations.chain_of_thought.evaluation import evaluate_cot_module
from thinking.optimizations.combined.evaluation import evaluate_combined_module
from thinking.optimizations.direct.evaluation import evaluate_direct_module
from thinking.optimizations.graph_of_thoughts.evaluation import evaluate_got_module
from thinking.optimizations.tree_of_thoughts.evaluation import evaluate_tot_module
from thinking.optimizations.shared.data_generation import SyntheticDataGenerator
from thinking.optimizations.shared.openrouter_config import configure_openrouter_lm


class EvaluationOrchestrator:
    def __init__(self, *, lm: dspy.LM):
        self.lm = lm

    def run_evaluation(self, *, verbose: bool = True) -> Dict[str, Any]:
        dspy.settings.configure(lm=self.lm)

        results: Dict[str, Any] = {}

        # Evaluate reasoning modules
        results["direct"] = evaluate_direct_module(DirectAnswer(), verbose=verbose)
        results["cot"] = evaluate_cot_module(ChainOfThought(), verbose=verbose)
        results["tot"] = evaluate_tot_module(TreeOfThoughts(branches=3, depth=2), verbose=verbose)
        results["got"] = evaluate_got_module(GraphOfThoughts(max_nodes=5), verbose=verbose)
        results["aot"] = evaluate_aot_module(AtomOfThoughts(), verbose=verbose)
        results["combined"] = evaluate_combined_module(CombinedReasoning(), verbose=verbose)

        # Evaluate routing accuracy on a synthetic suite
        gen = SyntheticDataGenerator()
        testset = gen.generate_classifier_data(num_examples_per_mode=10)
        router = AdaptiveReasoner()

        correct = 0
        for ex in testset:
            pred = router(question=ex.question)
            if str(pred.reasoning_mode).upper() == str(ex.reasoning_mode).upper():
                correct += 1

        results["router"] = {
            "total": len(testset),
            "correct": correct,
            "accuracy": (correct / len(testset)) if testset else 0.0,
        }

        if verbose:
            print("=" * 80)
            print("ROUTER EVALUATION")
            print("=" * 80)
            print(
                f"Synthetic routing accuracy: {results['router']['accuracy']:.1%} "
                f"({correct}/{len(testset)})"
            )

        return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate modules via orchestrator")
    parser.add_argument("--model", default="openrouter/openai/gpt-4o")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    lm = configure_openrouter_lm(model=args.model, verbose=not args.quiet)
    if lm is None:
        raise SystemExit("OPENROUTER_API_KEY not set")

    orchestrator = EvaluationOrchestrator(lm=lm)
    orchestrator.run_evaluation(verbose=not args.quiet)


if __name__ == "__main__":
    main()
