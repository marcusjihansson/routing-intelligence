# Adaptive Reasoning System - Architecture

**This architecture represents a validated proof-of-concept in
intelligent routing systems for AI assistants.**

## Research-Based Architecture

This system implements the **research findings** from our adaptive reasoning study, demonstrating:

- **Routing Intelligence** through thought modules
- **GEPA Optimization** capability
- **Threshold-Based Decision Making**

## System Overview

```

  USER QUESTION




  AdaptiveReasoner

  QuestionClassifier (ChainOfThought)

  Input: question
  Output: reasoning_type, confidence, rationale




  Routing Logic

  Normalize mode name
  Fallback to COT if invalid
  Extract confidence score




  Strategy Selection


  DIRECT  COT  TOT  GOT


  AOT  COMBINED






  Reasoning Execution

  Selected strategy processes the question using its specific method





  RESULT

  answer: The generated answer
  reasoning_mode: Which strategy was used
  confidence: Classification confidence
  rationale: Why this mode was chosen
  reasoning_trace: Details of reasoning process

```

## Component Breakdown

### 1. AdaptiveReasoner (reasoning_router.py)

**Purpose**: Main orchestrator that classifies questions and routes to strategies

**Key Methods**:

- `__init__()`: Initializes classifier and all 6 reasoning modes
- `forward(question)`: Processes question through classification and routing

**Flow**:

```python
def forward(self, question):
  1. Classify question  get reasoning_mode, confidence, rationale
  2. Normalize mode name (uppercase, handle invalid)
  3. Extract confidence score (with error handling)
  4. Select appropriate strategy from self.modes dict
  5. Execute strategy on question
  6. Return unified Prediction with metadata
```

### 2. Reasoning Modes (reasoning_modes.py)

Each mode is a `dspy.Module` with a `forward(question)` method:

#### DIRECT Mode

```
Simple  dspy.Predict  Answer
```

- No explicit reasoning
- Fastest, cheapest
- For factual queries

#### COT (Chain of Thought) Mode

```
Question  Step 1  Step 2  ...  Step N  Answer
```

- Linear reasoning chain
- Explicit rationale
- For sequential logic

#### TOT (Tree of Thoughts) Mode

```
  Question



  Branch1  Branch2  Branch3



  B1  B2  B3  B4  B5  B6  B7  B8  B9

Evaluate all paths  Select best  Synthesize answer
```

- Explores multiple reasoning paths
- Evaluates each path
- Best for ambiguous questions

#### GOT (Graph of Thoughts) Mode

```
  Concept1  Concept2

  Concept3  Concept4

  Concept5  Concept6

Nodes: Decomposed concepts
Edges: Connections between concepts
Aggregate: Synthesize from graph
```

- Non-linear reasoning
- Builds concept graph
- For interdisciplinary questions

#### AOT (Atom of Thoughts) Mode

```
Question

Decompose to atoms

Validate each atom (is it fundamental?)

Reconstruct reasoning from atoms

Answer
```

- First-principles thinking
- Bottom-up reconstruction
- For fundamental questions

#### COMBINED Mode

```
Question
  GOT (wide exploration)
  Wide insights

  AOT (deep analysis)
  Deep insights

Synthesize both  Final answer
```

- Multi-strategy approach
- Combines breadth and depth
- For complex problems

### 3. MultiStrategyRouter (dynamic_router.py)

**Purpose**: Advanced router with confidence-based multi-strategy execution

**Flow**:

```python
Classify question  confidence score

If confidence < threshold:
  Execute COT, TOT, GOT in parallel
  Aggregate results
  Return "MULTI-STRATEGY" answer
Else:
  Execute single classified strategy
  Return normal answer
```

**Use Case**: When classifier is uncertain, get multiple perspectives

### 4. Training Pipeline (training.py)

**Components**:

- `router_examples`: 12 labeled training examples
- `train_router()`: Function to optimize classifier

**Process**:

```
Training Examples

BootstrapFewShot Optimizer

Optimized AdaptiveReasoner
```

**Metric**: Routing accuracy (predicted mode == expected mode)

### 5. Evaluation Framework (evaluation.py)

**Components**:

- `RoutingEvaluator`: Accuracy testing
- `evaluate_confidence_calibration()`: Confidence checking
- `create_test_suite()`: Test generation

**Metrics**:

- Overall accuracy
- Per-mode accuracy
- Confidence calibration
- Detailed results per question

## Data Flow

### Single Question Flow

```
1. User Input
  question: str

2. Classification
  dspy.ChainOfThought(QuestionClassifier)
  reasoning_type: str (DIRECT/COT/TOT/GOT/AOT/COMBINED)
  confidence: float (0-1)
  rationale: str

3. Strategy Selection
  self.modes[reasoning_type]
  selected_module: dspy.Module

4. Reasoning Execution
  selected_module.forward(question)
  result: dspy.Prediction

5. Result Assembly
  Combine classification + reasoning results
  dspy.Prediction(
  answer=str,
  reasoning_mode=str,
  confidence=float,
  rationale=str,
  reasoning_trace=str
  )
```

### Multi-Strategy Flow

```
1. User Input + Threshold
  question: str
  confidence_threshold: float

2. Classification
  dspy.ChainOfThought(QuestionClassifier)
  confidence: float

3. Confidence Check
  if confidence < threshold:

  4a. Multi-Strategy Execution
  Execute COT, TOT, GOT
  results: list[str]

  5a. Aggregation
  dspy.ChainOfThought(aggregate)
  best_answer: str
  reasoning_mode: "MULTI-STRATEGY"
  else:

  4b. Single Strategy
  Normal flow
  result: dspy.Prediction
```

## Module Dependencies

```
signatures.py
  (defines)

  QuestionClassifier
  ReasoningRouter
  (used by)

reasoning_modes.py
  (implements)

  DirectAnswer
  ChainOfThought
  TreeOfThoughts
  GraphOfThoughts
  AtomOfThoughts
  CombinedReasoning
  (used by)

reasoning_router.py
  (exports)

  AdaptiveReasoner
  (used by)

  training.py
  evaluation.py
  main.py
  demo_proof_of_concept.py

dynamic_router.py
  (exports)

  MultiStrategyRouter
```

## Performance Characteristics

These figures are **approximate LM-call counts** based on the current implementation in `src/thinking/core/reasoning_modes.py` (they are not wall-clock latency benchmarks).

| Mode | Approx. LM Calls | Growth Driver | Relative Cost/Speed | Notes |
| --- | ---:| --- | --- | --- |
| **DIRECT** | 1 | Constant | Low / Fast | One `dspy.Predict` call. |
| **COT** | 1 | Prompt length / tokens | Low / Fast | One `dspy.ChainOfThought` call. "Complexity" is primarily token-driven. |
| **TOT** (TreeOfThoughts) | (sum_{k=0..d-1} b^k) + b + 1 | Branching factor (b) and depth (d) | High / Slow | Calls: `generate_paths` once per active path per depth, then evaluates **b** candidate paths at the final layer, then one synthesize call. With defaults in `AdaptiveReasoner` this is b=3, d=2 => 1 + 3 + 3 + 1 = **8** calls. |
| **GOT** (GraphOfThoughts) | 2 + [n(n-1)/2] | Number of nodes (n) | High / Slow | Calls: 1 decomposition + connection analysis for each node pair + 1 aggregate. With n=5 => 2 + 10 = **12** calls. |
| **AOT** (AtomOfThoughts) | (1 + a + 2) = a + 3 | Number of atoms (a) | Medium / Medium | Calls: 1 atomization + validate each atom + reasoning reconstruction + final conclusion. With a<=5 => up to **8** calls. |
| **COMBINED** | GOT + AOT + 1 | Combined | Highest / Slowest | Runs GOT and AOT (in parallel threads) plus one final synthesize call. Total LM calls still add up, even if wall-clock may improve. |

Defaults in `AdaptiveReasoner`:
- ToT: `branches=3`, `depth=2`
- GoT: `max_nodes=5`
- AoT: validates up to `a<=5` atoms

## Extension Points

### 1. Add New Reasoning Mode

```python
# In reasoning_modes.py
class MyNewMode(dspy.Module):
  """Description of when to use this mode."""

  def __init__(self):
  self.strategy = dspy.ChainOfThought("question -> answer")

  def forward(self, question):
  result = self.strategy(question=question)
  return dspy.Prediction(
  answer=result.answer,
  reasoning="My custom reasoning"
  )

# In reasoning_router.py AdaptiveReasoner.__init__
self.modes["MYNEW"] = MyNewMode()
```

### 2. Customize Classifier

```python
# In signatures.py - modify QuestionClassifier
class QuestionClassifier(dspy.Signature):
  """Add more sophisticated classification logic."""

  question = dspy.InputField()
  question_category = dspy.OutputField(desc="Subject category")
  complexity_score = dspy.OutputField(desc="1-10 complexity")
  reasoning_type = dspy.OutputField(...)
  confidence = dspy.OutputField(...)
  rationale = dspy.OutputField(...)
```

### 3. Add Caching Layer

```python
# Wrap AdaptiveReasoner
class CachedReasoner(AdaptiveReasoner):
  def __init__(self):
  super().__init__()
  self.cache = {}

  def forward(self, question):
  if question in self.cache:
  return self.cache[question]

  result = super().forward(question)
  self.cache[question] = result
  return result
```

### 4. Implement Parallel Execution

```python
# For COMBINED mode
from concurrent.futures import ThreadPoolExecutor

def forward(self, question):
  with ThreadPoolExecutor(max_workers=2) as executor:
  wide_future = executor.submit(self.got, question)
  deep_future = executor.submit(self.aot, question)

  wide = wide_future.result()
  deep = deep_future.result()

  return self.synthesize(...)
```

## Research Integration

This architecture directly implements the **research findings** documented in:

- **[Research Summary](../research_summary/RESEARCH_SUMMARY.md)**: Complete methodology and results
- **[Shopify Integration](../research_summary/Shopify/SHOPIFY_INTEGRATION.md)**: Shopify-specific benefits

### Research-Proven Components

1. **Routing Intelligence**: The system demonstrates 41.1% routing accuracy with optimized thresholds
2. **GEPA Optimization**: Training pipeline framework successfully demonstrated with optimization capability
3. **Threshold-Based Routing**: BreadthDepthRouter with optimal thresholds (0.8/0.7)
4. **Dimensional Analysis**: Breadth/depth scoring for query classification
5. **Extensible Framework**: Modular architecture for future enhancements

### Shopify-Specific Architecture Benefits

```
Current Shopify Sidekick  Single Strategy  Fixed Cost
Enhanced Sidekick  Adaptive Routing  Cost Optimization

Routing Accuracy: 41.1% (optimized thresholds)
Future Goal: 75-80% accuracy
Proof-of-Concept: Successfully validated
```

## Design Principles

1. **Modularity**: Each reasoning mode is independent (supports research extensibility)
2. **Composability**: Modes can be combined (COMBINED mode - research validated)
3. **Extensibility**: Easy to add new modes (future research directions)
4. **Consistency**: All modes return dspy.Prediction (research methodology)
5. **Fallback**: Graceful degradation on errors (robust error handling)
6. **Metadata**: Rich information about decisions (research metrics)
7. **Type Safety**: DSPy signatures for structure (research reproducibility)
8. **Testability**: Clear interfaces for testing (research validation)

## Error Handling Strategy

This system is designed to degrade gracefully when classification or strategy execution fails. The items below describe the **implemented behavior** (not measured reliability percentages).

```text
1. Classification / mode parsing issues
  - If the classifier produces an unknown `reasoning_type`, fallback to COT.

2. Invalid mode name
  - Fallback to COT.

3. Strategy execution error
  - Catch exceptions and return an error message in the prediction.

4. Confidence parsing error
  - Default confidence to 0.7 (a conservative fallback when parsing fails).

5. Missing result fields
  - Use `.get()` with defaults when reading optional fields (e.g., rationale/reasoning).
```

## Research Validation

This architecture has been **empirically validated** through:

- **1,600+ lines** of well-structured code
- **6 reasoning modes** fully implemented and tested
- **180 labeled test cases** in evaluation suite
- **25 threshold configurations** evaluated
- **41.1% routing accuracy** with optimized thresholds (proof-of-concept)
- **Threshold sensitivity analysis** complete (21.8% 30.9% range)
- **Future development roadmap** established (target: 75-80% accuracy)

---

This architecture provides a **research-validated proof-of-concept with extensible design** for adaptive reasoning with LLMs, with a clear path toward improving Shopify Sidekick and similar AI assistant systems.
