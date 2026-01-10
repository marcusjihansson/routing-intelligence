import dspy


class QuestionClassifier(dspy.Signature):
 """Classify the reasoning complexity needed for a question."""

 question = dspy.InputField()
 reasoning_type = dspy.OutputField(
 desc="One of: DIRECT (simple fact), COT (step-by-step), TOT (multiple valid paths/creative), GOT (interconnected/systemic), AOT (first principles/fundamental truths), COMBINED (complex/multi-faceted)"
 )
 confidence = dspy.OutputField(desc="Confidence score 0-1")
 rationale = dspy.OutputField(desc="Why this reasoning type?")


class ReasoningRouter(dspy.Signature):
 """Classify which reasoning mode a question requires."""

 question: str = dspy.InputField()
 reasoning_mode: str = dspy.OutputField(
 desc="One of: DIRECT, COT, TOT, GOT, AOT, COMBINED"
 )
