"""Adaptive Reasoning Router: Classifies questions and routes to appropriate reasoning modes.

This is the main entry point for the adaptive reasoning system.
"""

from __future__ import annotations

import dspy

from .signatures import QuestionClassifier
from .reasoning_modes import (
    AtomOfThoughts,
    ChainOfThought,
    CombinedReasoning,
    DirectAnswer,
    GraphOfThoughts,
    TreeOfThoughts,
)


class AdaptiveReasoner(dspy.Module):
    """Route questions to an appropriate reasoning strategy based on classification."""

    def __init__(self):
        super().__init__()
        self.classifier = dspy.ChainOfThought(QuestionClassifier)

        # Initialize all reasoning modes
        self.modes = {
            "DIRECT": DirectAnswer(),
            "COT": ChainOfThought(),
            "TOT": TreeOfThoughts(branches=3, depth=2),
            "GOT": GraphOfThoughts(max_nodes=5),
            "AOT": AtomOfThoughts(),
            "COMBINED": CombinedReasoning(),
        }

    def forward(self, question: str):
        """Process a question through the adaptive reasoning system."""
        # Classify the question to determine reasoning mode
        classification = self.classifier(question=question)
        reasoning_mode = str(classification.reasoning_type).upper()

        # Fallback to COT if invalid mode
        if reasoning_mode not in self.modes:
            reasoning_mode = "COT"

        # Get confidence (handle various output formats)
        try:
            confidence = float(str(classification.confidence).split()[0])
        except Exception:
            confidence = 0.7

        # Route to appropriate reasoning module
        selected_module = self.modes[reasoning_mode]
        result = selected_module(question=question)

        # Return with metadata
        return dspy.Prediction(
            answer=result.answer,
            reasoning_mode=reasoning_mode,
            confidence=confidence,
            reasoning_trace=result.get("reasoning", ""),
            rationale=getattr(classification, "rationale", ""),
        )
