# OpenRouter Setup Guide

## Quick Setup

### 1. Get Your API Key

1. Go to [OpenRouter](https://openrouter.ai/)
2. Sign up or log in
3. Navigate to [Keys](https://openrouter.ai/keys)
4. Create a new API key
5. Copy your key (starts with `sk-or-v1-...`)

### 2. Set Environment Variable

**Linux/Mac:**

```bash
export OPENROUTER_API_KEY='sk-or-v1-your-key-here'
```

**Windows (PowerShell):**

```powershell
$env:OPENROUTER_API_KEY='sk-or-v1-your-key-here'
```

**Windows (Command Prompt):**

```cmd
set OPENROUTER_API_KEY=sk-or-v1-your-key-here
```

### 3. Run the Demo

```bash
python -m thinking.scripts.lm_proof_of_concept
```

## Recommended Models

The system is configured to work with OpenRouter, which provides access to many models:

### Free Models (Great for Testing)

```python
"openrouter/openai/gpt-4o"  # Default in this repository
"openrouter/google/gemini-flash-1.5:free"  # Also good
```

### Paid Models (Better Quality)

```python
# Best Quality
"openrouter/anthropic/claude-3.5-sonnet"  # Excellent reasoning
"openrouter/openai/gpt-4o"  # Very capable

# Good Balance (Quality vs Cost)
"openrouter/google/gemini-pro"  # Good performance
"openrouter/anthropic/claude-3-haiku"  # Fast and cheap

# Budget Options
"openrouter/openai/gpt-4o"  # Default in this repository
"openrouter/meta-llama/llama-3.1-8b-instruct"  # Open source
```

## Changing Models

Edit `lm_proof_of_concept.py` and change the model parameter:

```python
lm = configure_openrouter_lm(model="openrouter/anthropic/claude-3.5-sonnet")
```

## Why OpenRouter?

**Access to multiple providers** - OpenAI, Anthropic, Google, Meta, etc.
**Unified API** - One interface for all models
**Free tier available** - Test without paying
**Pay-as-you-go** - Only pay for what you use
**DSPy compatible** - Works seamlessly via litellm

## Cost Estimation

For the proof of concept demo (6 test cases):

- **Free models**: $0.00 (yes, really free!)
- **GPT-3.5-Turbo**: ~$0.01-0.02
- **GPT-4**: ~$0.10-0.20
- **Claude-3.5-Sonnet**: ~$0.05-0.10

The adaptive system helps reduce costs by using simpler reasoning for simple questions!

## Troubleshooting

### "OPENROUTER_API_KEY not found"

**Solution**: Set the environment variable (see step 2 above)

### "Adapter JSONAdapter failed to parse"

**Solution**: This is why we use OpenRouter! It properly formats responses for DSPy.

### "API key invalid"

**Solution**:

1. Check your key starts with `sk-or-v1-`
2. Verify it's correctly copied (no extra spaces)
3. Try generating a new key

### "Rate limit exceeded"

**Solution**:

1. Use free models (they have higher limits)
2. Add delays between calls
3. Upgrade your OpenRouter account

### "Model not found"

**Solution**: Check the model name format: `openrouter/provider/model-name`

## Configuration Options

### Basic Setup

```python
from thinking.scripts.lm_proof_of_concept import configure_openrouter_lm

# Use default model
lm = configure_openrouter_lm()

# Use specific model
lm = configure_openrouter_lm(model="openrouter/anthropic/claude-4-haiku")
```

### Advanced Setup

```python
import dspy
import os

lm = dspy.LM(
  model="openrouter/openai/gpt-4o",
  api_key=os.environ.get('OPENROUTER_API_KEY'),
  api_base="https://openrouter.ai/api/v1",
  temperature=0.7,  # Control randomness
  max_tokens=1000,  # Limit response length
)

dspy.settings.configure(lm=lm)
```

## Using in Your Code

Once configured, use it anywhere:

```python
import dspy
from thinking.core.reasoning_router import AdaptiveReasoner
from thinking.scripts.lm_proof_of_concept import configure_openrouter_lm

# Setup
lm = configure_openrouter_lm()
reasoner = AdaptiveReasoner()

# Use it!
result = reasoner(question="How does photosynthesis work?")
print(f"Mode: {result.reasoning_mode}")
print(f"Answer: {result.answer}")
```

## Best Practices

1. **Start with free models** - Test your system first
2. **Monitor costs** - Check OpenRouter dashboard regularly
3. **Use appropriate complexity** - Don't use expensive models for simple questions
4. **Cache results** - Store answers to repeated questions
5. **Set token limits** - Prevent unexpectedly long responses
6. **Handle errors gracefully** - API calls can fail

## Security Notes

**Never commit API keys to git!**

Add to `.gitignore`:

```
.env
*.key
*_key.txt
```

Use environment variables or config files (not in git) to store keys.

## Alternative: Local Models

Don't want to use API keys? Use local models via Ollama:

```python
# Install Ollama first: https://ollama.ai
# Then: ollama pull llama3

import dspy

lm = dspy.LM(model="ollama/llama3")
dspy.settings.configure(lm=lm)
```

No API keys needed, but slower and requires good hardware.

## Support

- **OpenRouter Docs**: https://openrouter.ai/docs
- **DSPy Docs**: https://dspy-docs.vercel.app/
- **This Project**: See README.md and GETTING_STARTED.md

---

**Quick Start Command:**

```bash
export OPENROUTER_API_KEY='your-key-here' && python -m thinking.scripts.lm_proof_of_concept
```
