"""Reasoning Modes: Different strategies for answering questions.

Each mode represents a different cognitive approach:
- DIRECT: Simple retrieval/generation with no explicit reasoning
- COT: Chain of Thought - sequential step-by-step reasoning
- TOT: Tree of Thoughts - branching exploration with evaluation
- GOT: Graph of Thoughts - non-linear reasoning with interconnected concepts
- AOT: Atom of Thoughts - first-principles decomposition and reconstruction
- COMBINED: Hybrid approach using multiple strategies

Note: These implementations are intentionally lightweight proof-of-concept versions.
"""

from __future__ import annotations

import concurrent.futures

import dspy

from .reasoning_signatures import (
    AtomizeQuestion,
    DecomposeToNodes,
    EvaluateThought,
    FindConnection,
    GenerateThoughts,
    ValidateAtom,
)


class DirectAnswer(dspy.Module):
    """No reasoning: direct retrieval/generation for simple factual questions."""

    def __init__(self):
        super().__init__()
        self.generate = dspy.Predict("question -> answer")

    def forward(self, question: str):
        result = self.generate(question=question)
        return dspy.Prediction(answer=result.answer)


class ChainOfThought(dspy.Module):
    """Basic sequential reasoning: step-by-step thinking."""

    def __init__(self):
        super().__init__()
        self.reason = dspy.ChainOfThought("question -> answer")

    def forward(self, question: str):
        result = self.reason(question=question)
        return dspy.Prediction(answer=result.answer, reasoning=result.get("rationale", ""))


class TreeOfThoughts(dspy.Module):
    """Branching exploration with evaluation: consider multiple paths."""

    def __init__(self, branches: int = 5, depth: int = 3):
        super().__init__()
        self.branches = branches
        self.depth = depth
        self.generate_paths = dspy.Predict(GenerateThoughts)
        self.evaluate_path = dspy.Predict(EvaluateThought)
        self.synthesize = dspy.ChainOfThought("question, best_path -> answer")

    def forward(self, question: str):
        # Start with the question itself
        paths = [{"path": question, "depth": 0}]
        all_paths: list[dict] = []
        trace: list[str] = ["Started Tree of Thoughts exploration"]

        # Generate branching thoughts
        for depth in range(self.depth):
            trace.append(f"Depth {depth}: Processing {len(paths)} paths")
            new_paths = []
            for path_info in paths:
                try:
                    result = self.generate_paths(question=question, context=path_info["path"])
                    branches = str(result.thought_branches).split("\n")[: self.branches]
                    valid_branches = [b.strip() for b in branches if b.strip()]
                    trace.append(
                        f"Generated {len(valid_branches)} branches from '{path_info['path'][:30]}...'"
                    )

                    for branch in valid_branches:
                        new_paths.append(
                            {"path": f"{path_info['path']} {branch}", "depth": depth + 1}
                        )
                except Exception as e:
                    trace.append(f"Error generating branches: {e}")
                    # Fallback: keep the current path
                    new_paths.append(path_info)

            paths = new_paths if new_paths else paths
            all_paths.extend(paths)

        # Evaluate paths (evaluate last layer candidates)
        best_path = question
        best_score = 0.0

        candidates = all_paths[-self.branches :] if all_paths else [{"path": question}]
        trace.append(f"Evaluating {len(candidates)} candidate paths")

        for path_info in candidates:
            try:
                eval_result = self.evaluate_path(question=question, thought_path=path_info["path"])
                try:
                    score = float(str(eval_result.score).split()[0])
                except Exception:
                    score = 0.5

                trace.append(f"Path score {score:.2f}: ...{path_info['path'][-30:]}")
                if score > best_score:
                    best_score = score
                    best_path = path_info["path"]
            except Exception as e:
                trace.append(f"Error evaluating path: {e}")

        # Synthesize final answer
        result = self.synthesize(question=question, best_path=best_path)
        return dspy.Prediction(
            answer=result.answer,
            reasoning="Tree Search Summary:\n" + "\n".join(trace),
            trace=trace,
        )


class GraphOfThoughts(dspy.Module):
    """Non-linear reasoning with node connections: for interconnected concepts."""

    def __init__(self, max_nodes: int = 8):
        super().__init__()
        self.max_nodes = max_nodes
        self.decompose = dspy.Predict(DecomposeToNodes)
        self.find_connections = dspy.Predict(FindConnection)
        self.aggregate = dspy.ChainOfThought("question, nodes, connections -> answer")

    def forward(self, question: str):
        trace: list[str] = ["Started Graph of Thoughts analysis"]

        # Generate thought nodes
        decomp_result = self.decompose(question=question)
        nodes_text = str(decomp_result.thought_nodes)
        nodes = [n.strip() for n in nodes_text.split("\n") if n.strip()][: self.max_nodes]
        if not nodes:
            nodes = [question]

        trace.append(f"Identified {len(nodes)} thought nodes: {', '.join(nodes[:3])}...")

        # Build graph connections
        connections: list[str] = []
        trace.append(f"Analyzing connections between {len(nodes)} nodes")

        for i, node_a in enumerate(nodes):
            for node_b in nodes[i + 1 :]:
                try:
                    conn = self.find_connections(node_a=node_a, node_b=node_b, question=question)
                    try:
                        strength = float(str(conn.strength).split()[0])
                    except Exception:
                        strength = 0.6

                    if strength > 0.5:
                        connections.append(f"{node_a} <-> {node_b}: {conn.connection}")
                        trace.append(
                            f"Linked '{node_a[:15]}...' <-> '{node_b[:15]}...' (Strength: {strength:.1f})"
                        )
                except Exception:
                    continue

        nodes_str = "\n".join(f"- {node}" for node in nodes)
        conn_str = (
            "\n".join(f"- {c}" for c in connections) if connections else "No strong connections found"
        )
        result = self.aggregate(question=question, nodes=nodes_str, connections=conn_str)

        return dspy.Prediction(
            answer=result.answer,
            reasoning="Graph Analysis Summary:\n" + "\n".join(trace),
            trace=trace,
        )


class AtomOfThoughts(dspy.Module):
    """First-principles decomposition and reconstruction."""

    def __init__(self):
        super().__init__()
        self.atomize = dspy.Predict(AtomizeQuestion)
        self.validate_atom = dspy.Predict(ValidateAtom)
        self.reason_from_atoms = dspy.ChainOfThought("question, validated_atoms -> reconstructed_reasoning")
        self.conclude = dspy.ChainOfThought("question, reasoning -> answer")

    def forward(self, question: str):
        trace: list[str] = ["Started Atom of Thoughts decomposition"]

        raw_result = self.atomize(question=question)
        atoms_text = str(raw_result.atoms)
        raw_atoms = [a.strip() for a in atoms_text.split("\n") if a.strip()][:5]
        if not raw_atoms:
            raw_atoms = [question]

        trace.append(f"Decomposed into {len(raw_atoms)} initial atoms")

        validated: list[str] = []
        for atom in raw_atoms:
            try:
                check = self.validate_atom(atom=atom)
                is_fund = str(check.is_fundamental).lower()
                if "true" in is_fund or "yes" in is_fund:
                    validated.append(atom)
                    trace.append(f"Validated atom: {atom[:30]}...")
                else:
                    simplified = f"{atom} (needs simplification)"
                    validated.append(simplified)
                    trace.append(f"Atom rejected/simplified: {atom[:30]}...")
            except Exception as e:
                validated.append(atom)
                trace.append(f"Validation error for {atom[:10]}...: {e}")

        validated_str = "\n".join(f"- {v}" for v in validated)
        trace.append("Reconstructing reasoning from fundamental atoms")

        reasoning_result = self.reason_from_atoms(question=question, validated_atoms=validated_str)
        final_result = self.conclude(
            question=question,
            reasoning=reasoning_result.reconstructed_reasoning,
        )

        return dspy.Prediction(
            answer=final_result.answer,
            reasoning="First-Principles Analysis:\n" + "\n".join(trace),
            trace=trace,
        )


class CombinedReasoning(dspy.Module):
    """Hybrid: wide exploration (GOT) + deep validation (AOT)."""

    def __init__(self):
        super().__init__()
        self.got = GraphOfThoughts(max_nodes=4)
        self.aot = AtomOfThoughts()
        self.synthesize = dspy.ChainOfThought("question, wide_analysis, deep_analysis -> answer")

    def forward(self, question: str):
        # Parallel execution of strategies
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future_got = executor.submit(self.got, question=question)
            future_aot = executor.submit(self.aot, question=question)
            wide_result = future_got.result()
            deep_result = future_aot.result()

        trace: list[str] = ["Started Combined Reasoning (Parallel Execution)"]
        if hasattr(wide_result, "trace"):
            trace.append("\n--- Graph of Thoughts Trace ---")
            trace.extend(wide_result.trace)
        if hasattr(deep_result, "trace"):
            trace.append("\n--- Atom of Thoughts Trace ---")
            trace.extend(deep_result.trace)

        result = self.synthesize(
            question=question,
            wide_analysis=wide_result.answer,
            deep_analysis=deep_result.answer,
        )

        return dspy.Prediction(
            answer=result.answer,
            reasoning="Combined Analysis Summary:\n" + "\n".join(trace),
            trace=trace,
        )
