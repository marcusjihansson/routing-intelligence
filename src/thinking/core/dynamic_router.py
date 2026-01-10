"""Dynamic Router: Advanced routing with multi-strategy aggregation.

This module provides enhanced routing capabilities including:
- Low-confidence multi-strategy execution
- Result aggregation from multiple reasoning modes
- Adaptive fallback mechanisms

Note: This is a proof-of-concept implementation.
"""

from __future__ import annotations

import dspy

from .signatures import QuestionClassifier
from .reasoning_modes import ChainOfThought, GraphOfThoughts, TreeOfThoughts


class MultiStrategyRouter(dspy.Module):
    """Execute multiple strategies when classification confidence is low."""

    def __init__(self, confidence_threshold: float = 0.7):
        super().__init__()
        self.confidence_threshold = confidence_threshold
        self.classifier = dspy.ChainOfThought(QuestionClassifier)

        # Modes to try when confidence is low (lighter variants)
        self.fallback_modes = {
            "COT": ChainOfThought(),
            "TOT": TreeOfThoughts(branches=2, depth=1),
            "GOT": GraphOfThoughts(max_nodes=3),
        }

        self.aggregator = dspy.ChainOfThought("question, answers_list -> best_answer, reasoning")

    def forward(self, question: str):
        classification = self.classifier(question=question)

        try:
            confidence = float(str(classification.confidence).split()[0])
        except Exception:
            confidence = 0.7

        # If low confidence, try multiple approaches
        if confidence < self.confidence_threshold:
            results = []
            for mode_name, mode in self.fallback_modes.items():
                try:
                    result = mode(question=question)
                    results.append(f"[{mode_name}] {result.answer}")
                except Exception as e:
                    results.append(f"[{mode_name}] Error: {e}")

            answers_text = "\n\n".join(results)
            aggregated = self.aggregator(question=question, answers_list=answers_text)

            return dspy.Prediction(
                answer=aggregated.best_answer,
                reasoning_mode="MULTI-STRATEGY",
                confidence=confidence,
                reasoning_trace=(
                    f"Low confidence ({confidence:.2f}); aggregated strategies: {', '.join(self.fallback_modes.keys())}"
                ),
                strategies_used=list(self.fallback_modes.keys()),
            )

        # High confidence, use single classified mode (limited to fallback modes)
        reasoning_mode = str(classification.reasoning_type).upper()
        mode = self.fallback_modes.get(reasoning_mode, self.fallback_modes["COT"])
        result = mode(question=question)

        return dspy.Prediction(
            answer=result.answer,
            reasoning_mode=reasoning_mode,
            confidence=confidence,
            reasoning_trace=f"High confidence ({confidence:.2f}); single strategy",
        )
