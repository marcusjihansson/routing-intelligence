"""
Chain of Thought (COT) reasoning module training and evaluation.
"""

from .training import train_cot_module, load_cot_training_data
from .evaluation import evaluate_cot_module, create_cot_test_suite

__all__ = [
    "train_cot_module",
    "load_cot_training_data",
    "evaluate_cot_module",
    "create_cot_test_suite",
]
