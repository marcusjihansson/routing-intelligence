"""
Optimization testing and baseline comparison utilities.

This module provides tools to compare GEPA-optimized modules against baseline versions
to verify if optimization has actually improved performance.
"""

from .baseline_comparison import (
 compare_baseline_vs_optimized,
 run_comparison_suite,
 generate_comparison_report,
)
from .routing_evaluation import (
 evaluate_routing_accuracy,
 compare_classifier_versions,
 analyze_misclassifications,
)

__all__ = [
 'compare_baseline_vs_optimized',
 'run_comparison_suite',
 'generate_comparison_report',
 'evaluate_routing_accuracy',
 'compare_classifier_versions',
 'analyze_misclassifications',
]
