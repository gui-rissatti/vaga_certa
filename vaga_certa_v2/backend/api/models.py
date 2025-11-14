"""
Modelos Pydantic para validação de requisições e respostas da API.
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class GroundingSource(BaseModel):
    """Fonte de informação usada na geração."""
    uri: str
    title: str


class CompatibilityInsightsResponse(BaseModel):
    """Resumo heurístico da compatibilidade candidato-vaga."""
    score: int = Field(..., ge=0, le=100)
    label: str
    strengths: List[str]
    gaps: List[str]
    coverage_ratio: float = Field(..., ge=0.0, le=1.0)


# BUG FIX: Modelo separado para extração que não requer CV
class JobExtractionRequest(BaseModel):
    """Requisição para extrair detalhes de uma vaga (não requer CV)."""
    job_url: str = Field(..., description="URL da vaga de emprego")


class UserInputRequest(BaseModel):
    """Requisição de entrada do usuário (inclui CV para geração completa)."""
    cv: str = Field(..., min_length=50, description="Currículo do usuário")
    job_url: str = Field(..., description="URL da vaga de emprego")
    tone: str = Field(default="Profissional mas entusiasmado", description="Tom desejado")
    language: str = Field(default="Português Brasileiro", description="Idioma alvo")
    custom_context: str = Field(default="", description="Contexto adicional do usuário")


class JobDetailsResponse(BaseModel):
    """Resposta com detalhes da vaga extraída."""
    job_title: str
    company: str
    job_description: str
    validation: dict
    source: str
    content_score: Optional[int] = None  # Score de validação do conteúdo (0-100)


class GeneratedContentResponse(BaseModel):
    """Resposta com materiais gerados."""
    optimized_cv: str
    cover_letter: str
    networking_message: str
    interview_tips: str
    sources: List[GroundingSource]
    compatibility: CompatibilityInsightsResponse
    metadata: dict


class GenerateMaterialsRequest(BaseModel):
    """Requisição para gerar materiais."""
    cv: str = Field(..., min_length=50)
    job_title: str = Field(..., min_length=3)
    company: str = Field(..., min_length=2)
    job_description: str = Field(..., min_length=100)
    tone: str = Field(default="Profissional mas entusiasmado")
    language: str = Field(default="Português Brasileiro")
    custom_context: str = Field(default="")
    use_thinking_mode: bool = Field(default=False, description="Usar modo de raciocínio (mais lento, mais preciso)")


class ErrorResponse(BaseModel):
    """Resposta de erro padronizada."""
    error: str
    detail: Optional[str] = None
    error_code: Optional[str] = None

