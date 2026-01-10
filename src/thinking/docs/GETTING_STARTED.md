# Getting Started with Adaptive Reasoning System

## What has been built

I have created an **intelligent question-answering system** that automatically adapts its reasoning strategy based on question complexity.
Think of it as having six different "thinking modes" that get selected automatically:

1. **DIRECT** - Quick factual answers
2. **COT** (Chain of Thought) - Step-by-step reasoning
3. **TOT** (Tree of Thoughts) - Exploring multiple possibilities
4. **GOT** (Graph of Thoughts) - Connecting interdisciplinary concepts
5. **AOT** (Atom of Thoughts) - First-principles thinking
6. **COMBINED** - Using multiple strategies together

## Quick Start Guide

### Option 1: See It Work (No API Keys Needed)

Run the proof of concept demo with mock responses:

```bash
uv sync
uv run python -m thinking.scripts.demo_proof_of_concept
```

This shows how different question types route to different reasoning strategies.

### Option 2: Use with Real AI Models

#### Step 1: Install dependencies

If you're running from this repository, use `uv`:

```bash
uv sync
```

If you're installing into your own environment, prefer a virtualenv (or `uv pip`) rather than system Python.

#### Step 2: Set Up OpenRouter (Recommended)

**Why OpenRouter?** Access to many models (OpenAI, Anthropic, Google, etc.) through one API, with free options!

1. Get API key from [OpenRouter](https://openrouter.ai/keys)
2. Set environment variable:

```bash
export OPENROUTER_API_KEY='sk-or-v1-your-key-here'
```

#### Step 3: Run the Real LM Demo

```bash
export OPENROUTER_API_KEY='sk-or-v1-your-key-here'
uv run python -m thinking.scripts.lm_proof_of_concept
```

This uses OpenAI GPT-4o by default!

#### Step 4: Use in Your Code

```python
import dspy
from thinking.core.reasoning_router import AdaptiveReasoner
from thinking.scripts.lm_proof_of_concept import configure_openrouter_lm

# Configure OpenRouter (defaults to openrouter/openai/gpt-4o)
lm = configure_openrouter_lm()

# Create reasoner
reasoner = AdaptiveReasoner()

# Ask questions!
result = reasoner(question="What is 2+2?")
print(f"Mode: {result.reasoning_mode}")
print(f"Answer: {result.answer}")

result = reasoner(question="Explain why the sky is blue")
print(f"Mode: {result.reasoning_mode}")
print(f"Answer: {result.answer}")
```

#### Alternative: Direct Model Configuration

**For OpenAI:**

```python
from thinking.scripts.lm_proof_of_concept import configure_openrouter_lm

# Uses OPENROUTER_API_KEY
configure_openrouter_lm(model="openrouter/openai/gpt-4o")
```

**For Anthropic:**

```python
from thinking.scripts.lm_proof_of_concept import configure_openrouter_lm

# Uses OPENROUTER_API_KEY
configure_openrouter_lm(model="openrouter/anthropic/claude-3.5-sonnet")
```

**For Local Models (Ollama):**

```bash
# Install Ollama first from https://ollama.ai
ollama pull llama3
```

```python
dspy.settings.configure(lm=dspy.LM(model='ollama/llama3'))
```

**For more details, see [OPENROUTER_SETUP.md](OPENROUTER_SETUP.md)**

## Understanding the Output

When you ask a question, you get back:

```python
result = reasoner(question="Your question here")

# Access different parts:
print(result.reasoning_mode)  # Which strategy was used (DIRECT, COT, etc.)
print(result.confidence)  # How confident the classifier was (0-1)
print(result.rationale)  # Why this mode was chosen
print(result.answer)  # The actual answer
print(result.reasoning_trace)  # Details about the reasoning process
```

## Example Questions for Each Mode

### DIRECT Mode

- "What is the capital of France?"
- "What is 2+2?"
- "Who wrote Hamlet?"

### COT Mode

- "Why did the Roman Empire fall?"
- "How does photosynthesis work?"
- "Explain the water cycle"

### TOT Mode

- "What are all possible interpretations of this poem?"
- "What could be different meanings of this ambiguous statement?"
- "Generate alternative solutions to this problem"

### GOT Mode

- "How do climate change, economics, and politics interconnect?"
- "What are the relationships between AI, ethics, and society?"
- "How do nutrition, exercise, and sleep affect each other?"

### AOT Mode

- "From first principles, why does gravity exist?"
- "What is the fundamental nature of time?"
- "Derive the concept of number from first principles"

### COMBINED Mode

- "Design a comprehensive urban transportation system for 2050"
- "Create a strategy to solve world hunger"
- "Develop a holistic education system for the future"

## Testing Different Modes

See how different strategies work on the same question:

```python
from thinking.core.reasoning_modes import DirectAnswer, ChainOfThought, GraphOfThoughts

question = "Why is the sky blue?"

# Try with different strategies
direct = DirectAnswer()
print("DIRECT:", direct(question).answer)

cot = ChainOfThought()
print("COT:", cot(question).answer)

got = GraphOfThoughts()
print("GOT:", got(question).answer)
```

## Next Steps

### 1. Reproduce the repository experiments

This repository includes scripts under `thinking/experiments/` and `thinking/optimizations/`.
A few entrypoints to explore:

```bash
# Basic environment validation
python -m thinking.experiments.validate_setup

# Threshold evaluation
python -m thinking.experiments.evaluation.threshold_optimization

# Router comparison
python -m thinking.experiments.evaluation.comparative_routing_test
```

### 2. Use Multi-Strategy for Hard Questions

When the classifier isn't confident, aggregate multiple strategies:

```python
from thinking.core.dynamic_router import MultiStrategyRouter

router = MultiStrategyRouter(confidence_threshold=0.7)
result = router(question="What is consciousness?")
```

### 4. Add Custom Reasoning Modes

```python
import dspy

class AnalogyReasoning(dspy.Module):
  def __init__(self):
  self.reason = dspy.ChainOfThought("question -> analogy, answer")

  def forward(self, question):
  result = self.reason(question=question)
  return dspy.Prediction(
  answer=result.answer,
  reasoning=f"Used analogy: {result.analogy}"
  )

# Add to your reasoner
reasoner.modes["ANALOGY"] = AnalogyReasoning()
```

## Common Issues & Solutions

### Issue: "No language model configured"

**Solution:** Run `dspy.settings.configure(lm=...)` before using the reasoner.

### Issue: API rate limits

**Solution:** Use a local model with Ollama or implement caching.

### Issue: Wrong reasoning mode selected

**Solution:** Train the router with more examples or adjust confidence thresholds.

### Issue: Slow performance

**Solution:** Use lighter reasoning modes (reduce branches/depth in TOT, fewer nodes in GOT).

## File Structure Reference

Key locations in this repo:

- `src/thinking/core/`: core routers + reasoning modes
- `src/thinking/scripts/`: runnable demos (`python -m thinking.scripts...`)
- `src/thinking/experiments/`: evaluation harness + test cases
- `src/thinking/optimizations/`: optimization/training-related code

## Tips for Best Results

1. **Start Simple**: Test with DIRECT and COT modes first
2. **Use Appropriate Models**: GPT-4 or Claude Opus work best; GPT-3.5 uses fewer resources but may be less reliable for complex reasoning tasks. (Note: Model tier selection is separate from reasoning mode routing.)
3. **Tune for Your Use Case**: Adjust confidence thresholds and reasoning parameters
4. **Cache Results**: Store responses for repeated questions
5. **Monitor LM Usage**: Complex modes (TOT, GOT, COMBINED) make multiple LLM calls

## Need Help?

- Check the demos in `src/thinking/scripts/`
- See `src/thinking/experiments/README.md` for how to run evaluations
- See `src/thinking/optimizations/README.md` for optimization/training workflows
- Read `src/thinking/README.md` and `src/thinking/docs/` for documentation
