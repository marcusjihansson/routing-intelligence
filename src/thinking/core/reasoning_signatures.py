import dspy

class GenerateThoughts(dspy.Signature):
 """Generate diverse branching thoughts or next steps based on the context."""
 
 question = dspy.InputField()
 context = dspy.InputField(desc="Previous thoughts or partial path")
 thought_branches = dspy.OutputField(
 desc="A newline-separated list of 3-5 distinct next steps or alternative perspectives. Do not write a paragraph."
 )

class EvaluateThought(dspy.Signature):
 """Evaluate the promise of a thought path for answering the question."""
 
 question = dspy.InputField()
 thought_path = dspy.InputField()
 score = dspy.OutputField(desc="A float score between 0.0 and 1.0 indicating promise")
 reasoning = dspy.OutputField(desc="Brief justification for the score")

class DecomposeToNodes(dspy.Signature):
 """Decompose a complex question into key concepts or thought nodes."""
 
 question = dspy.InputField()
 thought_nodes = dspy.OutputField(
 desc="A newline-separated list of 5-8 key concepts, entities, or sub-problems. Do not write a paragraph."
 )

class FindConnection(dspy.Signature):
 """Analyze the relationship between two thought nodes."""
 
 question = dspy.InputField()
 node_a = dspy.InputField()
 node_b = dspy.InputField()
 connection = dspy.OutputField(desc="Description of the relationship or link")
 strength = dspy.OutputField(desc="A float score between 0.0 and 1.0 indicating connection strength")

class AtomizeQuestion(dspy.Signature):
 """Decompose a question into its most fundamental atomic truths or premises."""
 
 question = dspy.InputField()
 atoms = dspy.OutputField(
 desc="A newline-separated list of 3-5 fundamental facts or premises. Do not write a paragraph."
 )

class ValidateAtom(dspy.Signature):
 """Check if a premise is truly fundamental and irreducible."""
 
 atom = dspy.InputField()
 is_fundamental = dspy.OutputField(desc="True or False")
 explanation = dspy.OutputField(desc="Why it is or isn't fundamental")
