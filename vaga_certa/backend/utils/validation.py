"""
Sistema de validação multi-camada com confidence scoring.
Implementa validação estrutural, semântica e heurística.
"""
from typing import List
from dataclasses import dataclass
import re


def _normalize_generic_term(value: str) -> str:
    """Normaliza termos para comparação em listas de genéricos."""
    return re.sub(r"[^a-z0-9]+", "", value.lower())


@dataclass
class ValidationResult:
    """Resultado de validação com score e razões."""
    is_valid: bool
    score: int  # 0-100
    reasons: List[str]


def validate_and_score_job_content(content: str) -> ValidationResult:
    """
    Valida e pontua conteúdo de vaga usando sistema multi-camadas.
    
    Camadas:
    1. Estrutural (30 pts): Tamanho e formato
    2. Semântica (40 pts): Palavras-chave de contexto
    3. Heurística (30 pts): Densidade lexical e coerência
    
    Threshold: 30/100 para aprovar (permitindo vagas menos detalhadas).
    
    Args:
        content: Conteúdo a ser validado
        
    Returns:
        ValidationResult com score e razões
    """
    reasons: List[str] = []
    score = 0
    
    if not content or len(content.strip()) == 0:
        return ValidationResult(False, 0, ["Conteúdo vazio"])
    
    length = len(content.strip())
    
    # === CAMADA 1: VALIDAÇÃO ESTRUTURAL (30 pontos) ===
    if length < 500:
        reasons.append(f"Conteúdo muito curto ({length} chars, mínimo 500)")
    elif length < 1000:
        score += 10
        reasons.append("Tamanho aceitável mas curto")
    elif length < 3000:
        score += 20
        reasons.append("Tamanho adequado")
    else:
        score += 30
        reasons.append("Tamanho excelente")
    
    # === CAMADA 2: VALIDAÇÃO SEMÂNTICA (40 pontos) ===
    content_lower = content.lower()
    
    # Palavras-chave críticas de vagas
    critical_keywords = [
        "responsibilities", "requirements", "qualifications", "experience",
        "responsabilidades", "requisitos", "qualificações", "experiência"
    ]
    
    found_critical = sum(1 for kw in critical_keywords if kw in content_lower)
    critical_score = min(20, found_critical * 5)
    score += critical_score
    reasons.append(
        f"{found_critical}/{len(critical_keywords)} palavras-chave críticas encontradas ({critical_score} pts)"
    )
    
    # Contexto de recrutamento
    context_keywords = [
        "apply", "application", "candidate", "candidatar", "aplicar",
        "join", "team", "position", "role", "vaga", "cargo", "equipe"
    ]
    
    found_context = sum(1 for kw in context_keywords if kw in content_lower)
    context_score = min(20, found_context * 2)
    score += context_score
    reasons.append(
        f"{found_context}/{len(context_keywords)} palavras de contexto encontradas ({context_score} pts)"
    )
    
    # === CAMADA 3: VALIDAÇÃO HEURÍSTICA (30 pontos) ===
    
    # Densidade lexical (evita textos repetitivos)
    words = [w for w in content.split() if len(w) > 3]
    unique_words = set(w.lower() for w in words)
    
    if words:
        diversity_ratio = len(unique_words) / len(words)
        
        if diversity_ratio > 0.5:
            score += 15
            reasons.append(f"Boa diversidade lexical ({diversity_ratio*100:.1f}%)")
        elif diversity_ratio > 0.3:
            score += 8
            reasons.append(f"Diversidade lexical moderada ({diversity_ratio*100:.1f}%)")
        else:
            reasons.append(
                f"Baixa diversidade lexical ({diversity_ratio*100:.1f}%) - possível texto repetitivo"
            )
    
    # Detecta indicadores de erro
    error_indicators = [
        "page not found", "404", "error", "not available",
        "página não encontrada", "erro", "indisponível", "access denied"
    ]
    
    has_errors = any(indicator in content_lower for indicator in error_indicators)
    
    if has_errors:
        score = max(0, score - 30)
        reasons.append("⚠️ Detectados indicadores de erro na página")
    else:
        score += 15
        reasons.append("Nenhum indicador de erro detectado")
    
    # Verifica estrutura de lista
    has_list_structure = bool(
        re.search(r"[-•*]\s|^\d+\.\s", content, re.MULTILINE)
    )
    if has_list_structure:
        score = min(100, score + 5)
        reasons.append("✓ Estrutura de lista detectada (típico de vagas)")
    
    # Threshold reduzido para 30 pontos (aceita vagas menos detalhadas)
    is_valid = score >= 30
    
    return ValidationResult(is_valid, score, reasons)


def validate_and_score_job_details(
    job_title: str,
    company: str
) -> ValidationResult:
    """
    Valida e pontua título e empresa extraídos.
    
    Validação rigorosa com blacklist de termos genéricos.
    Threshold: 90/100 (requer ambos válidos).
    
    Args:
        job_title: Título da vaga
        company: Nome da empresa
        
    Returns:
        ValidationResult com score e razões
    """
    reasons: List[str] = []
    score = 0
    
    generic_terms = [
        "not found", "n/a", "na", "unknown", "tbd", "to be determined",
        "não encontrado", "desconhecido", "error", "none", "null", "company"
    ]
    normalized_generics = {_normalize_generic_term(term) for term in generic_terms}
    
    title_lower = (job_title or "").lower().strip()
    company_lower = (company or "").lower().strip()
    title_normalized = _normalize_generic_term(job_title or "")
    company_normalized = _normalize_generic_term(company or "")
    
    # Validação de título
    if not job_title or len(title_lower) == 0:
        return ValidationResult(False, 0, ["Título da vaga ausente"])
    
    if title_normalized in normalized_generics:
        return ValidationResult(
            False, 0, [f'Título genérico/inválido: "{job_title}"']
        )
    
    if len(title_lower) < 5:
        reasons.append(f'Título muito curto: "{job_title}"')
    elif len(title_lower) > 100:
        reasons.append(f'Título muito longo: "{job_title}"')
    else:
        score += 50
        reasons.append("✓ Título válido")
    
    # Validação de empresa
    if not company or len(company_lower) == 0:
        return ValidationResult(False, 0, ["Nome da empresa ausente"])
    
    if company_normalized in normalized_generics:
        return ValidationResult(
            False, 0, [f'Empresa genérica/inválida: "{company}"']
        )
    
    if len(company_lower) < 2:
        reasons.append(f'Nome da empresa muito curto: "{company}"')
    elif len(company_lower) > 100:
        reasons.append(f'Nome da empresa muito longo: "{company}"')
    else:
        score += 50
        reasons.append("✓ Empresa válida")
    
    is_valid = score >= 90  # Requer ambos válidos
    
    return ValidationResult(is_valid, score, reasons)

