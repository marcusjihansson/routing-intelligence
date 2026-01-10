"""Demo: Adaptive Reasoning System (no external API calls).

Run:
  python -m thinking.scripts.demo_proof_of_concept

This script configures a minimal mock LM so that the routing + reasoning
pipeline can be demonstrated without credentials.
"""

from __future__ import annotations

import dspy

from thinking.core.dynamic_router import MultiStrategyRouter
from thinking.core.reasoning_router import AdaptiveReasoner


class MockLM(dspy.LM):
    """A minimal LM that returns deterministic placeholder outputs.

    DSPy calls LMs with a `messages=[...]` style interface. For a demo, we
    return a constant string.
    """

    def __init__(self):
        super().__init__(model="mock")

    def __call__(self, messages=None, **kwargs):  # type: ignore[override]
        # DSPy adapters expect structured fields in the text output.
        # Return a minimal, parseable response that includes the fields
        # used by the classifier and the reasoning modules.
        # DSPy v3 ChatAdapter expects fields as:
        # [[ ## field_name ## ]]
        # value
        return [
            (
                "[[ ## reasoning ## ]]\nmock reasoning\n\n"
                "[[ ## reasoning_type ## ]]\nCOT\n\n"
                "[[ ## confidence ## ]]\n0.7\n\n"
                "[[ ## rationale ## ]]\nmock rationale\n\n"
                "[[ ## answer ## ]]\n[MOCK ANSWER]\n"
            )
        ]


def main() -> None:
    dspy.settings.configure(lm=MockLM())

    reasoner = AdaptiveReasoner()
    multi = MultiStrategyRouter(confidence_threshold=0.7)

    test_questions = [
        "What is 2+2?",
        "Explain why the sky is blue.",
        "Compare two approaches to improving conversion rate.",
    ]

    print("Adaptive Reasoning System Demo (Mock LM)")
    print("=" * 60)

    for q in test_questions:
        print(f"\nQuestion: {q}")
        r = reasoner(question=q)
        print(f"Routed mode: {r.reasoning_mode} (confidence: {r.confidence})")
        print(f"Answer: {r.answer}")

    print("\nMulti-strategy demo (low-confidence aggregation)")
    print("-" * 60)
    q = "What is consciousness?"
    r = multi(question=q)
    print(f"Question: {q}")
    print(f"Mode: {r.reasoning_mode} (confidence: {r.confidence})")
    print(f"Answer: {r.answer}")


if __name__ == "__main__":
    main()
