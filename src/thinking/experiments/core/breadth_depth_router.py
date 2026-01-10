"""Breadth/Depth Router: experimental routing based on breadth and depth scores.

Implements the breadth/depth scoring mechanism described in the research notes.
This is intentionally a proof-of-concept and is primarily used by the
`thinking.experiments.evaluation.*` scripts.
"""

from __future__ import annotations

import dspy

from ...core.reasoning_modes import (
    AtomOfThoughts,
    ChainOfThought,
    CombinedReasoning,
    DirectAnswer,
    GraphOfThoughts,
    TreeOfThoughts,
)


class BreadthDepthClassifier(dspy.Signature):
    """Classifier that outputs breadth/depth scores plus a suggested reasoning mode."""

    question = dspy.InputField()

    reasoning_type = dspy.OutputField(
        desc=(
            "One of: DIRECT, COT, TOT, GOT, AOT, COMBINED. "
            "DIRECT=simple fact; COT=step-by-step; TOT=multiple valid paths/creative; "
            "GOT=interconnected/systemic; AOT=first principles; COMBINED=multi-faceted."
        )
    )

    breadth_score = dspy.OutputField(
        desc="Score 0-1 indicating breadth/interconnectedness of the problem space"
    )
    depth_score = dspy.OutputField(
        desc="Score 0-1 indicating depth/foundational complexity of the question"
    )
    confidence = dspy.OutputField(desc="Overall confidence score 0-1")
    rationale = dspy.OutputField(desc="Why this reasoning type and scoring?")


class BreadthDepthRouter(dspy.Module):
    """Route questions using breadth/depth thresholds.

    Routing logic:
    - breadth high, depth low  -> GOT
    - depth high, breadth low  -> AOT
    - both high               -> COMBINED
    - else                    -> COT (default)
    """

    def __init__(self, breadth_threshold: float = 0.6, depth_threshold: float = 0.6):
        super().__init__()
        self.breadth_threshold = breadth_threshold
        self.depth_threshold = depth_threshold

        self.classifier = dspy.ChainOfThought(BreadthDepthClassifier)

        self.modes = {
            "DIRECT": DirectAnswer(),
            "COT": ChainOfThought(),
            "TOT": TreeOfThoughts(branches=3, depth=2),
            "GOT": GraphOfThoughts(max_nodes=5),
            "AOT": AtomOfThoughts(),
            "COMBINED": CombinedReasoning(),
        }

    def forward(self, question: str):
        classification = self.classifier(question=question)

        def _to_float(value, default: float) -> float:
            try:
                return float(str(value).split()[0])
            except Exception:
                return default

        breadth_score = _to_float(getattr(classification, "breadth_score", None), 0.5)
        depth_score = _to_float(getattr(classification, "depth_score", None), 0.5)
        confidence = _to_float(getattr(classification, "confidence", None), 0.7)

        if breadth_score > self.breadth_threshold and depth_score < self.depth_threshold:
            selected_mode = "GOT"
            routing_rationale = (
                f"High breadth ({breadth_score:.2f}) with low depth ({depth_score:.2f})"
            )
        elif depth_score > self.depth_threshold and breadth_score < self.breadth_threshold:
            selected_mode = "AOT"
            routing_rationale = (
                f"High depth ({depth_score:.2f}) with low breadth ({breadth_score:.2f})"
            )
        elif breadth_score > self.breadth_threshold and depth_score > self.depth_threshold:
            selected_mode = "COMBINED"
            routing_rationale = (
                f"Both breadth ({breadth_score:.2f}) and depth ({depth_score:.2f}) high"
            )
        else:
            selected_mode = "COT"
            routing_rationale = (
                f"Balanced scores (breadth: {breadth_score:.2f}, depth: {depth_score:.2f})"
            )

        reasoning_module = self.modes.get(selected_mode, self.modes["COT"])
        result = reasoning_module(question=question)

        return dspy.Prediction(
            answer=result.answer,
            reasoning_mode=selected_mode,
            breadth_score=breadth_score,
            depth_score=depth_score,
            confidence=confidence,
            routing_rationale=routing_rationale,
            classifier_rationale=getattr(classification, "rationale", ""),
            reasoning_trace=result.get("reasoning", ""),
        )
