# Breadth/Depth Scoring Experimental Framework

This directory contains a comprehensive experimental framework for testing and validating the breadth/depth scoring hypothesis from SHOPIFY.md. The framework empirically evaluates whether dimensional routing (breadth + depth scores) improves upon traditional single-mode classification.

##  Research Question

**Does routing based on breadth/depth scores outperform confidence-based routing for complex question answering?**

Where:
- **Breadth**: Interconnectedness/complexity of the problem space
- **Depth**: Foundational depth of required understanding

##  Framework Overview

### Phase 1: Routing Efficiency Testing
**File**: `experiments/evaluation/routing_efficiency_test.py`

Tests breadth/depth router performance across all threshold combinations (0.4-0.8 in 0.1 steps = 25 configurations) using 180 labeled training examples.

```bash
# First, validate your setup
python experiments/validate_setup.py

# Complete evaluation workflow (requires OPENROUTER_API_KEY)
export OPENROUTER_API_KEY='your-key-here'

# 1. Test routing efficiency across threshold combinations
python experiments/evaluation/routing_efficiency_test.py --quick

# 2. Compare breadth/depth vs baseline routing methods
python experiments/evaluation/comparative_routing_test.py

# 3. Generate reports and performance visualizations
python experiments/evaluation/generate_reports.py --dashboard

# 4. Get threshold optimization recommendations
python experiments/evaluation/threshold_optimization.py
```

**Outputs**: `experiments/results/routing_efficiency_results.json`

### Phase 2: Comparative Analysis
**File**: `experiments/evaluation/comparative_routing_test.py`

Compares breadth/depth router against baseline methods on identical test data.

**Routers Compared**:
- `BreadthDepth` - Experimental dimensional routing
- `AdaptiveReasoner` - Current baseline (single-mode)
- `MultiStrategy` - Confidence-based multi-routing
- `MultiStrategy_Aggressive` - Lower confidence threshold (0.4)
- `MultiStrategy_Conservative` - Higher confidence threshold (0.8)

```bash
python experiments/evaluation/comparative_routing_test.py
```

**Outputs**:
- `experiments/results/comparative_routing_analysis.json`
- `experiments/results/comparative_routing_analysis_confusion.json`

### Phase 3: Reports & Visualizations
**File**: `experiments/evaluation/generate_reports.py`

Generates comprehensive reports and performance dashboards.

```bash
# Generate reports only
python experiments/evaluation/generate_reports.py

# Generate reports + dashboard visualizations
python experiments/evaluation/generate_reports.py --dashboard
```

**Outputs**:
- `experiments/results/routing_efficiency_report.txt`
- `experiments/results/comparative_routing_report.txt`
- `experiments/results/dashboard/` (if --dashboard flag used)
  - `accuracy_heatmap.png`
  - `router_comparison.png`
  - `latency_accuracy_tradeoff.png`

### Phase 4: Threshold Optimization
**File**: `experiments/evaluation/threshold_optimization.py`

Analyzes results to recommend optimal threshold configurations.

```bash
# Balanced optimization (recommended)
python experiments/evaluation/threshold_optimization.py --criteria balanced

# Maximum accuracy optimization
python experiments/evaluation/threshold_optimization.py --criteria accuracy

# Stability-focused optimization
python experiments/evaluation/threshold_optimization.py --criteria stability
```

**Outputs**:
- `experiments/results/threshold_optimization_report.txt`
- `experiments/results/threshold_matrix.json`

##  Quick Start Workflow

```bash
# 1. Run routing efficiency test
python experiments/evaluation/routing_efficiency_test.py --quick

# 2. Compare against baselines
python experiments/evaluation/comparative_routing_test.py

# 3. Generate reports and visualizations
python experiments/evaluation/generate_reports.py --dashboard

# 4. Get optimization recommendations
python experiments/evaluation/threshold_optimization.py
```

##  Key Metrics Tracked

### Accuracy Metrics
- **Routing Accuracy**: % correct mode predictions (primary metric)
- **Per-Mode Accuracy**: Performance breakdown by reasoning mode
- **Threshold Sensitivity**: How accuracy varies with threshold settings

### Performance Metrics
- **Average Latency**: Response time per routing decision
- **Mode Distribution**: How often each reasoning mode is selected
- **Confusion Patterns**: Which modes are frequently confused

### Stability Metrics
- **Threshold Robustness**: Consistency across threshold combinations
- **Score Correlation**: How well breadth/depth scores predict optimal routing

##  Test Data

**Source**: `optimizations/*/training_examples.jsonl` (180 examples)
- **DIRECT**: 30 examples (factual/simple questions)
- **COT**: 30 examples (step-by-step reasoning)
- **TOT**: 30 examples (multiple paths/creative)
- **GOT**: 30 examples (interconnected/systemic)
- **AOT**: 30 examples (first principles/foundational)
- **COMBINED**: 30 examples (complex multi-faceted)

**Format**: `{"question": "...", "answer": "..."}` with mode implicit in directory

##  SHOPIFY.md Hypothesis Testing

The framework directly tests the core hypothesis:

```
IF breadth_score > threshold AND depth_score < threshold:
  Use Graph of Thoughts (GOT)
ELIF depth_score > threshold AND breadth_score < threshold:
  Use Atom of Thoughts (AOT)
ELIF both scores high:
  Use Hybrid Approach (COMBINED)
ELSE:
  Use Standard Reasoning (COT)
```

**Success Criteria**:
-  Routing accuracy >75% on optimal threshold configuration
-  Improved performance vs. baseline `AdaptiveReasoner` (baseline varies by model/dataset; see `src/thinking/experiments/results/` for bundled runs)
-  Consistent results across threshold ranges
-  Intuitive score correlations with reasoning mode complexity

##  Configuration Options

### Breadth/Depth Router Settings
```python
router = BreadthDepthRouter(
  breadth_threshold=0.6,  # 0.4-0.8 range tested
  depth_threshold=0.6  # 0.4-0.8 range tested
)
```

### Threshold Testing Ranges
- **Quick Test**: 3×3 = 9 configurations (breadth/depth: 0.5, 0.6, 0.7)
- **Full Test**: 5×5 = 25 configurations (breadth/depth: 0.4, 0.5, 0.6, 0.7, 0.8)

##  Directory Structure

```
experiments/
 core/
  breadth_depth_router.py  # Main experimental router
 evaluation/
  routing_efficiency_test.py  # Phase 1: Threshold sweep testing
  comparative_routing_test.py  # Phase 2: Baseline comparisons
  generate_reports.py  # Phase 3: Reports & visualizations
  threshold_optimization.py  # Phase 4: Analysis & optimization
 data/
  breadth_depth_test_cases.py  # Test case generation utilities
 results/  # Output directory for all results
  routing_efficiency_results.json
  comparative_routing_analysis.json
  *_report.txt
  dashboard/
  accuracy_heatmap.png
  ...
```

##  Demo Scripts

**Breadth/Depth Focused Demo**:
```bash
python scripts/lm_proof_of_concept_scoring.py
```

**Integrated Demo** (shows both routing approaches):
```bash
# Standard routing
python scripts/lm_proof_of_concept.py

# Breadth/depth routing
python scripts/lm_proof_of_concept.py --breadth-depth
```

##  Expected Outcomes

Based on SHOPIFY.md hypothesis, we expect:
1. **Improved Accuracy**: Breadth/depth routing outperforms single-mode classification
2. **Better Mode Selection**: More appropriate reasoning strategies for complex questions
3. **Threshold Tunability**: Optimal settings can be found for different use cases
4. **Stability**: Consistent performance across threshold ranges

##  Next Steps After Testing

**If Results Support Hypothesis**:
- Integrate breadth/depth router into `core/`
- Add threshold optimization to training pipeline
- Deploy A/B test in production environment

**If Results Don't Support Hypothesis**:
- Analyze failure modes and confusion patterns
- Refine scoring mechanisms or threshold logic
- Consider alternative dimensional approaches
- Archive as validated experimental approach

##  Prerequisites

- **OpenRouter API Key**: Set `OPENROUTER_API_KEY` environment variable
- **Test Data**: 180 labeled examples in `src/thinking/optimizations/*/training_examples.jsonl`
- **Optional**: matplotlib/seaborn for visualizations

##  Model Configuration

All evaluation scripts automatically configure the OpenRouter language model. The default model is `openrouter/openai/gpt-4o`, but you can specify different models:

```bash
# Use different models for evaluation
uv run python -m thinking.experiments.evaluation.routing_efficiency_test --model openrouter/google/gemini-pro
uv run python -m thinking.experiments.evaluation.comparative_routing_test --model openrouter/anthropic/claude-3.5-sonnet

# Available models:
# - openrouter/openai/gpt-4o (default, fast)
# - openrouter/google/gemini-pro (good balance)
# - openrouter/anthropic/claude-3.5-sonnet (best quality)
```

##  Performance Baselines

- **Baseline**: Compare against `AdaptiveReasoner` on your chosen dataset/model.
- **Bundled run**: See `src/thinking/experiments/results/comparative_routing_report.txt`.
- **Target Improvement**: >75% with breadth/depth routing (project goal)
- **Latency Budget**: <2x increase vs. baseline routing

---

**Status**:  Complete experimental framework ready for empirical validation of SHOPIFY.md breadth/depth scoring hypothesis.