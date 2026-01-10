"""
Shared utilities for training and evaluation across all reasoning modules.
"""

from .data_generation import SyntheticDataGenerator
from .metrics import (
 classifier_accuracy_metric,
 reasoning_quality_metric,
)
from .openrouter_config import (
 configure_openrouter_lm,
 get_recommended_models,
 get_model_for_task,
 check_openrouter_setup,
 print_setup_instructions,
)
from .model_persistence import (
 save_optimized_module,
 load_optimized_module,
 list_saved_modules,
 get_latest_module,
 create_training_summary,
 print_saved_modules_summary,
)

__all__ = [
 'SyntheticDataGenerator',
 'classifier_accuracy_metric',
 'reasoning_quality_metric',
 'configure_openrouter_lm',
 'get_recommended_models',
 'get_model_for_task',
 'check_openrouter_setup',
 'print_setup_instructions',
 'save_optimized_module',
 'load_optimized_module',
 'list_saved_modules',
 'get_latest_module',
 'create_training_summary',
 'print_saved_modules_summary',
]
