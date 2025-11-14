"""Utility helpers to estimate candidate-to-job compatibility."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple
from collections import Counter
import re
import unicodedata


_STOPWORDS = {
    "para",
    "com",
    "that",
    "with",
    "from",
    "sobre",
    "onde",
    "quando",
    "como",
    "have",
    "this",
    "your",
    "will",
    "de",
    "das",
    "dos",
    "the",
    "and",
    "por",
    "uma",
    "mais",
    "than",
    "then",
    "elas",
    "eles",
    "possui",
    "possuir",
    "atividades",
    "responsabilidades",
    "requirements",
    "requisitos",
    "qualificacoes",
}


def _normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    return normalized.encode("ascii", "ignore").decode("ascii")


def _extract_tokens(value: str) -> List[str]:
    normalized = _normalize_text(value).lower()
    tokens = re.findall(r"[a-z0-9\+#\.]{3,}", normalized)
    return [token for token in tokens if token not in _STOPWORDS]


def _extract_keywords(value: str) -> Tuple[Counter, List[str]]:
    tokens = _extract_tokens(value)
    return Counter(tokens), list(dict.fromkeys(tokens))


@dataclass
class CompatibilityInsights:
    """Represents a heuristic compatibility estimation."""

    score: int
    label: str
    strengths: List[str]
    gaps: List[str]
    coverage_ratio: float


def calculate_compatibility(cv: str, job_description: str) -> CompatibilityInsights:
    """Compute a lightweight compatibility score between CV and job description."""
    job_counter, job_tokens = _extract_keywords(job_description)
    cv_counter, cv_tokens = _extract_keywords(cv)

    if not job_counter:
        return CompatibilityInsights(
            score=50,
            label="Dados insuficientes",
            strengths=[],
            gaps=[],
            coverage_ratio=0.0,
        )

    # Considera apenas as 30 palavras-chave mais relevantes para evitar diluição
    ranked_job_keywords = [kw for kw, _ in job_counter.most_common(30)]
    job_keywords = set(ranked_job_keywords)
    cv_keywords = set(cv_tokens)

    if len(job_keywords) < 5 or sum(job_counter.values()) < 10:
        return CompatibilityInsights(
            score=50,
            label="Dados insuficientes",
            strengths=[],
            gaps=ranked_job_keywords[:5],
            coverage_ratio=0.0,
        )

    matched = job_keywords & cv_keywords
    missing = job_keywords - cv_keywords

    coverage_ratio = len(matched) / max(1, len(job_keywords))
    match_points = min(60, len(matched) * 12)
    coverage_points = min(40, round(coverage_ratio * 40))
    score = max(5, match_points + coverage_points)

    if score >= 75:
        label = "Alta compatibilidade"
    elif score >= 45:
        label = "Compatibilidade moderada"
    else:
        label = "Compatibilidade baixa"

    strengths = [kw for kw, _ in job_counter.most_common() if kw in matched][:5]
    gaps = [kw for kw, _ in job_counter.most_common() if kw in missing][:5]

    return CompatibilityInsights(
        score=score,
        label=label,
        strengths=strengths,
        gaps=gaps,
        coverage_ratio=round(coverage_ratio, 3),
    )

