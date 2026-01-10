"""Shared synthetic data generation utilities.

These are meant for demos and experimentation. For production, replace with real,
human-labeled (or otherwise verified) data.
"""

from __future__ import annotations

import random
from typing import List

import dspy


class SyntheticDataGenerator:
    """Generate synthetic training examples for classifier/module optimization."""

    @staticmethod
    def generate_classifier_data(num_examples_per_mode: int = 20) -> List[dspy.Example]:
        examples: list[dspy.Example] = []

        direct_questions = [
            "What is photosynthesis?",
            "Define machine learning",
            "Who is Albert Einstein?",
            "When did World War II happen?",
            "Where is the Eiffel Tower?",
            "How many continents are there?",
            "What year was the internet invented?",
            "What is 15 + 27?",
            "What is the capital of France?",
            "Who wrote Romeo and Juliet?",
            "What is the speed of light?",
            "Define artificial intelligence",
            "When did the moon landing occur?",
            "How many planets are in our solar system?",
            "What is the largest ocean?",
            "Who painted the Mona Lisa?",
        ]

        cot_questions = [
            "Explain how the water cycle works",
            "Why does gravity occur?",
            "How does a combustion engine function step by step?",
            "What causes climate change?",
            "Walk me through solving a quadratic equation",
            "Describe the process of cell division",
            "What are the reasons for economic inflation?",
            "How does photosynthesis convert light into energy?",
            "Explain the process of evolution",
            "Why do seasons change?",
            "How does the immune system fight infections?",
            "What causes earthquakes?",
            "Explain how vaccines work",
            "Why does ice float on water?",
            "How do airplanes generate lift?",
        ]

        tot_questions = [
            "What are all possible solutions for traffic congestion?",
            "Generate different endings for this story",
            "What could be multiple interpretations of this poem?",
            "Explore alternative explanations for the Fermi paradox",
            "What are various approaches to conflict resolution?",
            "Consider different perspectives on artificial consciousness",
            "What are different ways to interpret the ending of Inception?",
            "Generate alternative solutions for reducing plastic waste",
            "What could be multiple meanings of this ambiguous statement?",
            "Explore different approaches to solving homelessness",
            "What are various perspectives on the trolley problem?",
            "Consider alternative explanations for the placebo effect",
            "What are different possible causes of the Big Bang?",
            "Generate multiple strategies for dealing with procrastination",
        ]

        got_questions = [
            "How do climate, economics, and politics interconnect in energy policy?",
            "What are the relationships between social media and mental health?",
            "How does education influence income through social mobility?",
            "Explain the network of connections between genetics, environment, and behavior",
            "What is the web of relationships in the global financial system?",
            "How do sleep, stress, and cognitive performance interconnect?",
            "What are the relationships between nutrition, exercise, and longevity?",
            "How do technology, culture, and society influence each other?",
            "Explain the connections between quantum mechanics and consciousness",
            "How do language, thought, and perception interact?",
            "What are the relationships between AI, ethics, and policy?",
            "How do microbiome, immunity, and mental health interconnect?",
            "Explain the network between supply chains, labor, and inflation",
        ]

        aot_questions = [
            "From first principles, why does consciousness exist?",
            "What is mathematics at the most fundamental level?",
            "Derive the concept of ownership from basic assumptions",
            "What are the foundational elements of language?",
            "Break down democracy to its atomic components",
            "What is the essence of justice?",
            "From first principles, why does gravity exist?",
            "What is time at the most fundamental level?",
            "Derive the concept of money from basic assumptions",
            "What are the foundational elements of music?",
            "Break down morality to its atomic components",
            "What is the essence of intelligence?",
            "From first principles, why do numbers exist?",
            "What is causality at the most fundamental level?",
        ]

        combined_questions = [
            "Design a comprehensive education system for the 21st century",
            "Create a holistic solution to urban poverty",
            "Develop a complete strategy for Mars colonization",
            "Build an end-to-end plan for pandemic preparedness",
            "Design a full framework for sustainable agriculture",
            "Create a comprehensive solution for global water scarcity",
            "Develop a complete strategy for reversing climate change",
            "Design a holistic approach to reforming healthcare",
            "Build an end-to-end plan for achieving energy independence",
            "Create a comprehensive framework for ethical AI development",
            "Design a complete solution for modernizing transportation infrastructure",
            "Develop a holistic strategy for reducing income inequality",
            "Build a comprehensive plan for sustainable urban development",
        ]

        def add(questions: list[str], mode: str) -> None:
            for _ in range(num_examples_per_mode):
                q = random.choice(questions)
                examples.append(dspy.Example(question=q, reasoning_mode=mode).with_inputs("question"))

        add(direct_questions, "DIRECT")
        add(cot_questions, "COT")
        add(tot_questions, "TOT")
        add(got_questions, "GOT")
        add(aot_questions, "AOT")
        add(combined_questions, "COMBINED")

        random.shuffle(examples)
        return examples
