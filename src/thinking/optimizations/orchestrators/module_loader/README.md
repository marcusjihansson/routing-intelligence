# Module Loader

Load optimized reasoning modules from `saved_modules/` and compose them into a complete reasoning system.

## Purpose

This loader provides a flexible system for loading individual or all optimized GEPA reasoning modules. It enables:

- Loading single optimized modules (e.g., only `cot` module)
- Loading all optimized modules and composing them into a complete `OptimizedReasoner`
- Validating loaded modules to ensure they work correctly
- Saving composed systems for easy reuse

## Quick Start

```python
from thinking.optimizations.orchestrators.module_loader import load_all_optimized

# Load all available optimized modules
reasoner = load_all_optimized()

# Use it immediately
result = reasoner(question="How does photosynthesis work?")
print(result.answer, result.reasoning_mode)
```

## Python API

### Load All Modules

```python
from thinking.optimizations.orchestrators.module_loader import load_all_optimized

# Load all available optimized modules + classifier
reasoner = load_all_optimized()

# Check what's loaded
print("Optimized modes:", reasoner.get_optimized_modes())
print("Unoptimized modes:", reasoner.get_unoptimized_modes())
```

### Load Single Module

```python
from thinking.optimizations.orchestrators.module_loader import load_gepa

# Load only the optimized ChainOfThought
cot_module = load_gepa(module="cot")

# Use directly
result = cot_module(question="How does photosynthesis work?")
print(result.answer)
```

### Load Specific Modules

```python
from thinking.optimizations.orchestrators.module_loader import (
    load_gepa, OptimizedReasoner
)

# Load individual modules
cot = load_gepa(module="cot")
got = load_gepa(module="got")

# Compose manually into a reasoner
classifier = load_gepa()  # Load optimized classifier
reasoner = OptimizedReasoner(
    classifier=classifier,
    optimized_modes={"COT": cot, "GOT": got}
)
```

### List Available Modules

```python
from thinking.optimizations.orchestrators.module_loader import list_available_modules

# Get all available optimized modules
available = list_available_modules()

for module_name, path in available.items():
    print(f"{module_name}: {path}")
```

### Validate Modules

```python
from thinking.optimizations.orchestrators.module_loader import (
    load_all_optimized, validate_reasoner_composition
)

reasoner = load_all_optimized()

# Run validation on the complete system
validation = validate_reasoner_composition(
    reasoner,
    test_questions_per_mode=5
)

if validation["valid"]:
    print("✓ All tests passed!")
    print(f"Overall success rate: {validation['overall_success_rate']:.1%}")
else:
    print("✗ Validation failed:")
    for error in validation["errors"]:
        print(f"  - {error}")
```

### Validate Single Module

```python
from thinking.optimizations.orchestrators.module_loader import (
    load_gepa, validate_single_module
)

cot = load_gepa(module="cot")

# Validate the module
validation = validate_single_module(
    module=cot,
    module_name="cot",
    num_test_questions=5,
    verbose=True
)

print(f"Success rate: {validation['success_rate']:.1%}")
```

### Access Module Metadata

```python
reasoner = load_all_optimized()

# Get metadata about loaded modules
metadata = reasoner.get_module_metadata()

print("Optimization path:", metadata.get("optimization_path"))
print("Classifier path:", metadata.get("classifier_path"))
print("Optimized modes:", metadata.get("optimized_modes"))
```

## CLI Usage

### List Available Modules

```bash
uv run python -m thinking.optimizations.orchestrators.module_loader.loader_orchestrator --list
```

Output:
```
Available optimized modules in saved_modules:
  ✓ classifier → classifier_optimized_20251219_005646
  ✓ cot       → cot_optimized_20251218_152631
  ✗ direct    → No saved modules found
  ✗ tot       → No saved modules found
  ...
```

### Load All Modules

```bash
uv run python -m thinking.optimizations.orchestrators.module_loader.loader_orchestrator \
  --load-all
```

### Load and Validate

```bash
uv run python -m thinking.optimizations.orchestrators.module_loader.loader_orchestrator \
  --load-all \
  --validate \
  --test-questions 5 \
  --verbose
```

### Load Specific Modules

```bash
# Load only cot and got modules
uv run python -m thinking.optimizations.orchestrators.module_loader.loader_orchestrator \
  --module cot \
  --module got \
  --validate
```

### Save Composed System

```bash
uv run python -m thinking.optimizations.orchestrators.module_loader.loader_orchestrator \
  --load-all \
  --validate \
  --save-to ./production_system
```

This creates a new directory like `./production_system/optimized_system_20251226_123456/` containing:
- `module.json` - DSPy serialization of the composed reasoner
- `metadata.json` - Information about loaded modules and validation results

### Custom Path

```bash
uv run python -m thinking.optimizations.orchestrators.module_loader.loader_orchestrator \
  --load-all \
  --path /custom/path/to/saved_modules
```

## CLI Arguments

| Argument | Description |
|----------|-------------|
| `--path` | Base path for saved modules (default: `saved_modules`) |
| `--module NAME` | Load specific module (can be used multiple times) |
| `--load-all` | Load all available optimized modules |
| `--list` | List available modules and exit |
| `--validate` | Run validation after loading |
| `--test-questions N` | Number of test questions per mode for validation (default: 3) |
| `--save-to PATH` | Save composed reasoner to this path |
| `--verbose, -v` | Verbose output |

## Validation Details

### Module Compatibility Validation

Validates that:
- All paths exist and contain `module.json` and `metadata.json`
- Module types in metadata match expected classes
- Timestamp formats are valid

### Single Module Validation

Validates a single module can execute:
- Runs test questions through the module
- Checks for exceptions and valid output format
- Returns success rate and detailed trace

### Reasoner Composition Validation

Validates the complete reasoning system:
- Generates test questions for each reasoning mode
- Runs questions through the reasoner
- Validates output contains expected fields
- Checks routing assigns reasonable confidence scores (0-1)
- Ensures each reasoning mode is used

## Module Names

Valid module names for loading:

| Name | Reasoning Mode | Class |
|------|----------------|-------|
| `classifier` | Classifier | `AdaptiveReasoner` |
| `direct` | DIRECT | `DirectAnswer` |
| `cot` | COT | `ChainOfThought` |
| `tot` | TOT | `TreeOfThoughts` |
| `got` | GOT | `GraphOfThoughts` |
| `aot` | AOT | `AtomOfThoughts` |
| `combined` | COMBINED | `CombinedReasoning` |

## OptimizedReasoner

The `OptimizedReasoner` class extends `AdaptiveReasoner` and is a drop-in replacement. It provides additional methods:

```python
reasoner.get_module_metadata()  # Dict with module paths and info
reasoner.get_optimized_modes()  # List of mode names using optimized modules
reasoner.get_unoptimized_modes()  # List of mode names using defaults
```

## Error Handling

The loader fails immediately if a requested module cannot be found or fails to load, providing descriptive error messages:

```python
# Module not found
FileNotFoundError: No optimized module found for 'cot' in saved_modules.
Expected pattern: cot_optimized_*

# Invalid module name
ValueError: Unknown module name: 'invalid'.
Valid options: ['direct', 'cot', 'tot', 'got', 'aot', 'combined', 'classifier']
```

## Exit Codes

- `0`: Success
- `1`: Error (module not found, load failed, validation failed)
- `2`: No modules found

## Troubleshooting

### "No optimized modules found"

Train modules first:
```bash
uv run python -m thinking.optimizations.chain_of_thought.training \
  --budget light --examples 20
```

### "Module not found"

Check that modules are saved in the correct directory structure:
```
saved_modules/
  cot_optimized_20251218_152631/
    module.json
    metadata.json
  classifier_optimized_20251219_005646/
    module.json
    metadata.json
```

### Validation Fails

- Increase test questions with `--test-questions 10`
- Check module output formats are correct
- Verify modules were trained successfully
- Try retraining with different parameters

### Import Errors

Make sure you're running from the project root:
```bash
cd /path/to/thinking
uv run python -m thinking.optimizations.orchestrators.module_loader.loader_orchestrator --list
```

## Advanced Usage

### Partial Optimization

Load only some modes optimized, others use defaults:

```python
from thinking.optimizations.orchestrators.module_loader import (
    load_gepa, OptimizedReasoner
)

# Only load cot and aot
cot = load_gepa(module="cot")
aot = load_gepa(module="aot")

# Compose reasoner with partial optimization
reasoner = OptimizedReasoner(
    optimized_modes={"COT": cot, "AOT": aot}
)

# Other modes (DIRECT, TOT, GOT, COMBINED) use defaults
```

### Save and Load Composed System

```python
# Save a composed system
reasoner = load_all_optimized()
reasoner.save("./my_system/optimized_system/module.json")

# Load it back later
from thinking.core.reasoning_router import AdaptiveReasoner

loaded = AdaptiveReasoner()
loaded.load("./my_system/optimized_system/module.json")
```

## Related

- `../../shared/model_persistence.py` - Save/load utilities
- `../../training_orchestrator.py` - Train all modules
- `../../../core/reasoning_modes.py` - Reasoning module definitions
- `../../../core/reasoning_router.py` - AdaptiveReasoner
