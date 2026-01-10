# Adaptive Reasoning System - Quick Reference

##  One-Minute Overview

**What it does**: Automatically routes questions to the best reasoning strategy.

**How it works**: Question  Classifier  Select from 6 reasoning modes  Answer

##  Instant Start

### Option 1: With OpenRouter (Recommended)
```bash
# One-time setup
uv sync

# Run
export OPENROUTER_API_KEY='sk-or-v1-your-key'
uv run python -m thinking.scripts.lm_proof_of_concept
```

### Option 2: In Your Code
```python
import dspy
from thinking.core.reasoning_router import AdaptiveReasoner
from thinking.scripts.lm_proof_of_concept import configure_openrouter_lm

# 1. Configure OpenRouter (free!)
lm = configure_openrouter_lm()

# 2. Create reasoner
reasoner = AdaptiveReasoner()

# 3. Ask anything
result = reasoner(question="Your question here")
print(f"{result.reasoning_mode}: {result.answer}")
```

### Option 3: Direct API
```python
from thinking.scripts.lm_proof_of_concept import configure_openrouter_lm

# Uses OPENROUTER_API_KEY
configure_openrouter_lm(model="openrouter/openai/gpt-4o")
```

##  The 6 Reasoning Modes

| Mode | When to Use | Example |
|------|-------------|---------|
| **DIRECT** | Simple facts | "What is 2+2?" |
| **COT** | Step-by-step | "Why did Rome fall?" |
| **TOT** | Multiple paths | "All meanings of this poem?" |
| **GOT** | Connected concepts | "How do climate & economics relate?" |
| **AOT** | First principles | "Why does gravity exist?" |
| **COMBINED** | Complex problems | "Design 2050 transportation" |

##  Key Files

| File | Purpose | Use When |
|------|---------|----------|
| `reasoning_router.py` | Main system | **Start here** |
| `demo_proof_of_concept.py` | No-API demo | Testing without keys |
| `main.py` | Examples | Learning usage |
| `training.py` | Optimization | Improving accuracy |
| `evaluation.py` | Testing | Checking performance |
| `README.md` | Full docs | Deep dive |
| `GETTING_STARTED.md` | Tutorial | Step-by-step guide |

##  Common Tasks

### Test Without API Keys
```bash
python -m thinking.scripts.demo_proof_of_concept
```

### Run Examples
```python
from main import quick_test, demo_basic_routing
quick_test()
```

### Train for Better Accuracy
```python
from training import train_router
optimized = train_router(lm)
```

### Evaluate Performance
```python
from evaluation import evaluate_with_training_examples
evaluate_with_training_examples()
```

### Use Multi-Strategy
```python
from thinking.core.dynamic_router import MultiStrategyRouter
router = MultiStrategyRouter(confidence_threshold=0.7)
result = router(question="Hard question")
```

### Add Custom Mode
```python
class MyMode(dspy.Module):
  def forward(self, question):
  # Your logic
  return dspy.Prediction(answer="...")

reasoner.modes["MYMODE"] = MyMode()
```

##  Pro Tips

1. **Start with simple questions** to verify setup
2. **Use DIRECT/COT for most queries** (fewer LM calls, faster)
3. **Train the router** with your domain questions
4. **Monitor which modes are used** to optimize LM call efficiency
5. **Cache results** for repeated questions
6. **Lower confidence threshold** for better accuracy (more LM calls)

##  Troubleshooting

| Problem | Solution |
|---------|----------|
| "No LM configured" | Run `dspy.settings.configure(lm=...)` first |
| Wrong mode selected | Train with more examples |
| Too slow | Use lighter modes or reduce parameters |
| High LM usage | Use COT instead of TOT/GOT/COMBINED |
| API errors | Check keys, rate limits, quotas |

##  What You Get Back

```python
result = reasoner(question="...")

result.answer  # The answer
result.reasoning_mode  # Which mode was used
result.confidence  # Classifier confidence (0-1)
result.rationale  # Why this mode?
result.reasoning_trace  # Details about reasoning
```

##  Learning Path

1. **Day 1**: Run `demo_proof_of_concept.py`, read `GETTING_STARTED.md`
2. **Day 2**: Configure real LM, try `main.py` examples
3. **Day 3**: Test with your questions, evaluate performance
4. **Day 4**: Train router, tune parameters
5. **Day 5**: Deploy and monitor in your application

##  Need More?

- **Quick start**: `GETTING_STARTED.md`
- **Full documentation**: `README.md`
- **Project overview**: `PROJECT_SUMMARY.md`
- **Code examples**: `main.py`, `training.py`, `evaluation.py`

---

**Remember**: The system automatically selects the best reasoning strategy. You just ask questions! 
