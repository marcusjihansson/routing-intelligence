# Optimization Testing

This directory contains tools for testing whether GEPA optimization has successfully improved your reasoning modules and classifier.

##  Purpose

After training modules with GEPA, it's crucial to verify that optimization actually improved performance. This framework lets you:

1. **Compare baseline vs optimized** - Test if GEPA made your modules better
2. **Evaluate routing accuracy** - Check if the classifier routes queries correctly
3. **Identify weaknesses** - Find misclassification patterns to guide further training
4. **Generate reports** - Document optimization results

##  Files

- `baseline_comparison.py` - Compare optimized modules against unoptimized baselines
- `routing_evaluation.py` - Evaluate classifier routing accuracy
- `test_optimization.py` - Main test script (run this!)
- `__init__.py` - Package exports

##  Quick Start

### 1. Train a Module

First, train a module with GEPA:

```bash
# Train chain of thought module
uv run python -m thinking.optimizations.chain_of_thought.training --budget light --examples 20
```

This will save an optimized module in the current directory (e.g., `cot_optimized_20240101_120000/`).

### 2. Test the Optimization

Compare the optimized module against baseline:

```bash
# Test specific module
uv run python -m thinking.optimizations.optimization.test_optimization --module cot

# Test all available modules
uv run python -m thinking.optimizations.optimization.test_optimization --module all

# Test classifier
uv run python -m thinking.optimizations.optimization.test_optimization --module classifier
```

### 3. Review Results

The test will output:
-  **Accuracy comparison**: Baseline vs Optimized
-  **Latency analysis**: Speed comparison
-  **Improvement metrics**: Percentage gains/losses
-  **Detailed report**: Saved as JSON

##  Example Output

```
================================================================================
COMPARING BASELINE VS OPTIMIZED: COT
================================================================================

1. Testing baseline module (10 examples)...
  Progress: 10/10

2. Testing optimized module (10 examples)...
  Progress: 10/10

================================================================================
COMPARISON RESULTS
================================================================================

 COT Performance:
  Baseline Accuracy:  65.00%
  Optimized Accuracy: 78.00%
  Improvement:  +13.00% (+20.0%)

  Latency:
  Baseline Avg:  245.3ms
  Optimized Avg: 198.7ms

 Optimization SUCCESSFUL - 20.0% improvement!

================================================================================
```

##  Usage Examples

### Test a Single Module

```bash
uv run python -m thinking.optimizations.optimization.test_optimization --module cot
```

### Test Classifier Routing

```bash
uv run python -m thinking.optimizations.optimization.test_optimization --module classifier
```

### Test All Modules

```bash
uv run python -m thinking.optimizations.optimization.test_optimization --module all
```

### Specify Custom Search Directory

If you saved modules in a different location:

```bash
uv run python -m thinking.optimizations.optimization.test_optimization \
  --module all \
  --search-dir ./my_trained_modules
```

##  Python API

### Compare Module Versions

```python
from thinking.optimizations.optimization.baseline_comparison import run_comparison_suite
from thinking.optimizations.chain_of_thought.evaluation import create_cot_test_suite
from thinking.core.reasoning_modes import ChainOfThought
from thinking.optimizations.shared.openrouter_config import configure_openrouter_lm
import dspy

# Configure LM (requires OPENROUTER_API_KEY)
lm = configure_openrouter_lm(model='openrouter/openai/gpt-4o')
dspy.settings.configure(lm=lm)

# Create baseline
baseline = ChainOfThought()

# Create test suite
test_cases = create_cot_test_suite()
test_suite = [dspy.Example(question=tc["question"]).with_inputs("question") for tc in test_cases]

# Run comparison
result = run_comparison_suite(
  module_name="cot",
  baseline_module=baseline,
  optimized_module_path="./cot_optimized_20240101_120000",
  module_class=ChainOfThought,
  test_suite=test_suite,
  metric_fn=reasoning_quality_metric,
  verbose=True
)

print(f"Improvement: {result.improvement_pct:.1f}%")
```

### Evaluate Routing Accuracy

```python
from thinking.optimizations.optimization.routing_evaluation import (
  evaluate_routing_accuracy,
  generate_test_suite_for_routing
)
from thinking.core.reasoning_router import AdaptiveReasoner

# Create classifier
classifier = AdaptiveReasoner()

# Generate test suite
test_suite = generate_test_suite_for_routing(num_examples_per_mode=20)

# Evaluate
result = evaluate_routing_accuracy(classifier, test_suite, verbose=True)

print(f"Overall accuracy: {result.accuracy:.2%}")
print(f"Per-mode accuracy: {result.per_mode_accuracy}")
```

### Compare Classifier Versions

```python
from thinking.optimizations.optimization.routing_evaluation import compare_classifier_versions
from thinking.core.reasoning_router import AdaptiveReasoner
from thinking.optimizations.shared.model_persistence import load_optimized_module

# Baseline
baseline = AdaptiveReasoner()

# Load optimized
optimized, _ = load_optimized_module(
  "./classifier_optimized_20240101_120000",
  AdaptiveReasoner
)

# Compare
comparison = compare_classifier_versions(
  baseline_classifier=baseline,
  optimized_classifier=optimized,
  test_suite=test_suite,
  verbose=True
)
```

##  Understanding Results

### Module Comparison

- **Improvement > 1%**:  Optimization was successful
- **-1% < Improvement < 1%**:  Minimal impact
- **Improvement < -1%**:  Optimization degraded performance

### Routing Accuracy

- **Overall Accuracy**: Percentage of queries routed correctly
- **Per-Mode Accuracy**: How well each mode is recognized
- **Confusion Matrix**: Which modes are confused with each other
- **Misclassifications**: Specific examples where routing failed

##  Interpretation Guide

### Good Results
- Improvement > 5%
- All modes show positive or neutral changes
- Routing accuracy > 80%

### Needs Work
- Improvement < 0% (degradation)
- Some modes show significant drops
- Routing accuracy < 70%
- High confusion between specific mode pairs

### Next Steps

If optimization didn't help:
1. **Train with more examples** - Try 50-100 instead of 20-30
2. **Use a heavier budget** - Try `--budget medium` or `--budget heavy`
3. **Improve training data** - Replace synthetic data with real examples
4. **Check for overfitting** - Test on different data than training
5. **Tune hyperparameters** - Experiment with different max_bootstrapped_demos

##  Troubleshooting

### "No saved modules found"

Train a module first:
```bash
uv run python -m thinking.optimizations.chain_of_thought.training --budget light --examples 20
```

### "Module file not found"

The saved module directory may be incomplete. Check that it contains:
- `module.json` - The saved model
- `metadata.json` - Training information

### "ImportError" or "ModuleNotFoundError"

Make sure you're running from the correct directory:
```bash
uv run python -m thinking.optimizations.optimization.test_optimization --module all
```

##  Report Format

The generated `optimization_report.json` contains:

```json
{
  "total_modules": 3,
  "overall_improvement": 0.082,
  "modules": [
  {
  "module_name": "cot",
  "baseline_accuracy": 0.65,
  "optimized_accuracy": 0.78,
  "improvement": 0.13,
  "improvement_pct": 20.0,
  "test_cases": 10
  }
  ],
  "summary": {
  "improved": 2,
  "degraded": 0,
  "neutral": 1
  }
}
```

##  Best Practices

1. **Always compare against baseline** - Don't assume optimization helped
2. **Use consistent test data** - Same test set for fair comparison
3. **Test on unseen examples** - Don't use training data for evaluation
4. **Run multiple times** - LLMs can be stochastic
5. **Document results** - Save reports for tracking progress
6. **Iterate** - Use results to guide next training iteration

##  Related

- `../training_orchestrator.py` - Train all modules
- `../shared/model_persistence.py` - Save/load modules
- `../shared/metrics.py` - Evaluation metrics
- `../SHOPIFY_DEMO.md` - Production deployment guide
