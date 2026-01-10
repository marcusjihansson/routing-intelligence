"""Breadth/Depth test cases.

Curated examples designed to exercise different breadth/depth score combinations.
Used to validate the breadth/depth routing hypothesis.
"""

from __future__ import annotations

from typing import List

import dspy


def get_breadth_depth_test_cases() -> List[dspy.Example]:
    """Return curated test cases representing different breadth/depth profiles."""

    return [
        # High breadth, low depth -> GOT
        dspy.Example(
            question=(
                "How do nutrition, exercise, sleep, and stress management interact to affect weight loss?"
            ),
            reasoning_mode="GOT",
            expected_breadth=0.8,
            expected_depth=0.3,
            category="interconnected_systems",
        ),
        dspy.Example(
            question=(
                "What factors influence housing prices in a city: economy, demographics, government policy, and construction costs?"
            ),
            reasoning_mode="GOT",
            expected_breadth=0.9,
            expected_depth=0.4,
            category="economic_systems",
        ),
        # High depth, low breadth -> AOT
        dspy.Example(
            question="What is the fundamental nature of consciousness and why does it exist?",
            reasoning_mode="AOT",
            expected_breadth=0.2,
            expected_depth=0.9,
            category="foundational_philosophy",
        ),
        dspy.Example(
            question="Why do objects fall to the ground? Explain from first principles.",
            reasoning_mode="AOT",
            expected_breadth=0.1,
            expected_depth=0.95,
            category="physical_fundamentals",
        ),
        # Both high -> COMBINED
        dspy.Example(
            question=(
                "Design a comprehensive business strategy that addresses market analysis, competitive positioning, operational efficiency, and long-term sustainability - "
                "break it down from first principles while considering all interconnections."
            ),
            reasoning_mode="COMBINED",
            expected_breadth=0.85,
            expected_depth=0.8,
            category="complex_business_strategy",
        ),
        dspy.Example(
            question=(
                "How should society balance individual freedom, collective responsibility, economic growth, and environmental protection? "
                "Explore the fundamental principles and interconnected consequences."
            ),
            reasoning_mode="COMBINED",
            expected_breadth=0.9,
            expected_depth=0.85,
            category="societal_philosophy",
        ),
        # Balanced/low -> COT/DIRECT
        dspy.Example(
            question="What are the steps to bake chocolate chip cookies?",
            reasoning_mode="COT",
            expected_breadth=0.3,
            expected_depth=0.2,
            category="procedural_knowledge",
        ),
        dspy.Example(
            question="What is the capital of France?",
            reasoning_mode="DIRECT",
            expected_breadth=0.1,
            expected_depth=0.1,
            category="factual_knowledge",
        ),
        # Creative/multiple paths -> TOT
        dspy.Example(
            question="What are different creative ways to approach solving world hunger?",
            reasoning_mode="TOT",
            expected_breadth=0.6,
            expected_depth=0.5,
            category="creative_problem_solving",
        ),
        dspy.Example(
            question="How could someone learn to play guitar? Consider different methods and paths.",
            reasoning_mode="TOT",
            expected_breadth=0.5,
            expected_depth=0.4,
            category="learning_methodology",
        ),
    ]


def get_edge_case_test_cases() -> List[dspy.Example]:
    """Return edge cases that might challenge breadth/depth scoring."""

    return [
        dspy.Example(
            question="Tell me about quantum physics.",
            reasoning_mode="AOT",
            expected_breadth=0.7,
            expected_depth=0.8,
            category="ambiguous_depth_breadth",
        ),
        dspy.Example(
            question="Why?",
            reasoning_mode="DIRECT",
            expected_breadth=0.1,
            expected_depth=0.1,
            category="minimal_input",
        ),
        dspy.Example(
            question="What is the time complexity of quicksort in the average case?",
            reasoning_mode="COT",
            expected_breadth=0.2,
            expected_depth=0.6,
            category="technical_narrow",
        ),
        dspy.Example(
            question="What are some marketing strategies for small businesses?",
            reasoning_mode="TOT",
            expected_breadth=0.8,
            expected_depth=0.3,
            category="broad_shallow",
        ),
    ]


def generate_synthetic_breadth_depth_data(num_examples: int = 100) -> List[dspy.Example]:
    """Generate simple synthetic examples labeled with expected breadth/depth.

    This is intentionally a placeholder generator; it's useful for demos/tests,
    but should be replaced with real labeled data for serious evaluation.
    """

    synthetic_examples: list[dspy.Example] = []

    breadth_ranges = [(0.0, 0.3), (0.3, 0.6), (0.6, 1.0)]
    depth_ranges = [(0.0, 0.3), (0.3, 0.6), (0.6, 1.0)]

    for breadth_min, breadth_max in breadth_ranges:
        for depth_min, depth_max in depth_ranges:
            expected_breadth = (breadth_min + breadth_max) / 2
            expected_depth = (depth_min + depth_max) / 2

            if expected_breadth > 0.6 and expected_depth < 0.4:
                mode = "GOT"
            elif expected_depth > 0.6 and expected_breadth < 0.4:
                mode = "AOT"
            elif expected_breadth > 0.6 and expected_depth > 0.6:
                mode = "COMBINED"
            else:
                mode = "COT"

            question = (
                f"Synthetic question with breadth {expected_breadth:.1f} and depth {expected_depth:.1f}"
            )

            synthetic_examples.append(
                dspy.Example(
                    question=question,
                    reasoning_mode=mode,
                    expected_breadth=expected_breadth,
                    expected_depth=expected_depth,
                )
            )

    return synthetic_examples[:num_examples]
