"""
Utilitários para validação, logging e outras funções auxiliares.
"""

from .validation import (
    ValidationResult,
    validate_and_score_job_content,
    validate_and_score_job_details
)
from .compatibility import CompatibilityInsights, calculate_compatibility

__all__ = [
    "ValidationResult",
    "validate_and_score_job_content",
    "validate_and_score_job_details",
    "CompatibilityInsights",
    "calculate_compatibility"
]

