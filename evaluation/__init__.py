"""
Evaluation Module for Zero-Hallucination RAG Framework

This module provides experimental evaluation capabilities for:
- Retrieval parameter optimization
- Hallucination rate measurement
- Verification agent effectiveness
- Cross-domain generalization testing

Use these experiments to:
1. Validate system behavior on new domains
2. Tune hyperparameters (k, chunk size, etc.)
3. Generate research metrics for publications
4. Demonstrate research methodology
"""

from .experiment_retrieval import (
    run_full_experiment,
    generate_sample_results,
    TEST_QUERIES,
    K_VALUES,
)

__all__ = [
    "run_full_experiment",
    "generate_sample_results", 
    "TEST_QUERIES",
    "K_VALUES",
]
