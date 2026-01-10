# Quick Start Guide - Modular Training & Evaluation

##  Quick Examples

### Train a Single Module

```python
import dspy
from thinking.optimizations.chain_of_thought.training import train_cot_module

# Configure your language model
lm = dspy.LM(model='gpt-3.5-turbo')

# Train the Chain of Thought module
optimized_cot = train_cot_module(
  lm=lm,
  num_examples=30,
  max_iterations=10
)
```

### Train All Modules at Once

```python
import dspy
from thinking.optimizations.orchestrators.training_orchestrator import TrainingOrchestrator

# Configure your language model
lm = dspy.LM(model='gpt-3.5-turbo')

# Train everything: classifier + all reasoning modules
orchestrator = TrainingOrchestrator(lm=lm)
results = orchestrator.run_training(max_iterations=15)

print(f"Training complete. Keys: {list(results.keys())}")
```

### Evaluate a Single Module

```python
import dspy
from thinking.optimizations.chain_of_thought.evaluation import evaluate_cot_module
from thinking.core.reasoning_modes import ChainOfThought
from thinking.optimizations.shared.openrouter_config import configure_openrouter_lm

# Configure your language model
configure_openrouter_lm(model="openrouter/openai/gpt-4o")

# Evaluate
module = ChainOfThought()
results = evaluate_cot_module(module, verbose=True)

print(f"Success: {results['successful']}/{results['total_tests']}")
```

### Evaluate Complete System

```python
import dspy
from thinking.optimizations.orchestrators.evaluation_orchestrator import EvaluationOrchestrator
from thinking.optimizations.shared.openrouter_config import configure_openrouter_lm

# Configure your language model
configure_openrouter_lm(model="openrouter/openai/gpt-4o")

# Evaluate everything
orchestrator = EvaluationOrchestrator(lm=dspy.settings.lm)
results = orchestrator.run_evaluation(verbose=True)

print("Evaluation complete")
```

##  Available Modules

| Module | Purpose | Use Case |
|--------|---------|----------|
| **direct** | Simple factual answers | "What is the capital of France?" |
| **chain_of_thought** | Step-by-step reasoning | "Explain how photosynthesis works" |
| **tree_of_thoughts** | Multiple solution paths | "What are different ways to reduce traffic?" |
| **graph_of_thoughts** | Interconnected systems | "How do sleep, stress, and performance interconnect?" |
| **atom_of_thoughts** | First-principles thinking | "From first principles, why does gravity exist?" |
| **combined** | Complex multi-strategy | "Design a comprehensive education system" |

##  Common Tasks

### 1. Train Just One Module You Care About

```python
from thinking.optimizations.graph_of_thoughts.training import train_got_module
from thinking.optimizations.shared.openrouter_config import configure_openrouter_lm

lm = configure_openrouter_lm(model="openrouter/openai/gpt-4o")
optimized_got = train_got_module(lm=lm, num_examples=30)
```

### 2. Generate Training Data for a Module

```python
from thinking.optimizations.chain_of_thought.training import generate_cot_training_data

# Get 50 training examples for COT
training_data = generate_cot_training_data(num_examples=50)
print(f"Generated {len(training_data)} examples")
```

### 3. Create a Custom Test Suite

```python
from thinking.optimizations.tree_of_thoughts.evaluation import create_tot_test_suite

# Get the default test suite
test_suite = create_tot_test_suite()

# Or create your own
custom_tests = [
  {
  "question": "What are different approaches to learning a new language?",
  "expected_mode": "TOT",
  "category": "learning",
  "difficulty": "medium"
  }
]
```

### 4. Use Shared Utilities

```python
from thinking.optimizations.shared.data_generation import SyntheticDataGenerator
from thinking.optimizations.shared.metrics import classifier_accuracy_metric

# Generate classifier training data
generator = SyntheticDataGenerator()
data = generator.generate_classifier_data(num_examples_per_mode=20)

# Use metrics
score = classifier_accuracy_metric(example, prediction)
```

##  Configuration Options

### Training Parameters

```python
train_cot_module(
  lm=lm,  # Language model instance
  num_examples=30,  # Training examples to generate
  max_iterations=10,  # GEPA optimization iterations
  verbose=True  # Print detailed progress
)
```

### Evaluation Parameters

```python
evaluate_cot_module(
  module=my_module,  # Module instance to evaluate
  test_suite=None,  # Use default or provide custom tests
  verbose=True  # Print detailed results
)
```

##  File Organization

Each module follows the same structure:

```
module_name/
 __init__.py  # Public API exports
 training.py  # Training logic and data generation
 evaluation.py  # Evaluation logic and test suites
```

##  Troubleshooting

### Import Errors

Make sure you're running from the correct directory:

```bash
uv sync
uv run python -c "from thinking.optimizations.chain_of_thought.training import train_cot_module"
```

### Missing Dependencies

Ensure DSPy is installed:

```bash
uv sync
```

### GEPA Not Available

If GEPA optimizer is not available in your DSPy version, the system will automatically fall back to BootstrapFewShot optimizer.

##  Next Steps

1. Read `thinking/optimizations/docs/QUICKSTART.md` for the supported entrypoints
2. Check individual module files for specific examples
3. Explore the orchestrators for batch operations
4. Customize training data for your use case

##  Pro Tips

- Start with a small number of examples to test quickly
- Use verbose=True during development to see what's happening
- Each module can be trained independently in parallel
- Save trained modules using DSPy's built-in serialization
- The shared utilities make it easy to add new modules

Happy training! 
