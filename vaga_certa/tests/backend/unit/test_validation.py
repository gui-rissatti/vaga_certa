"""
Testes unitários para o módulo de validação.
"""
import pytest
from utils.validation import (
    ValidationResult,
    validate_and_score_job_content,
    validate_and_score_job_details
)


@pytest.mark.unit
class TestValidationResult:
    """Testes da classe ValidationResult."""
    
    def test_validation_result_valid(self):
        """Teste de resultado de validação válido."""
        result = ValidationResult(
            is_valid=True,
            score=0.85,
            validation_errors=[],
            suggestions=["Adicionar mais detalhes"]
        )
        
        assert result.is_valid
        assert result.score == 0.85
        assert len(result.validation_errors) == 0
        assert len(result.suggestions) == 1
    
    def test_validation_result_invalid(self):
        """Teste de resultado de validação inválido."""
        result = ValidationResult(
            is_valid=False,
            score=0.3,
            validation_errors=["Conteúdo muito curto"],
            suggestions=[]
        )
        
        assert not result.is_valid
        assert result.score == 0.3
        assert len(result.validation_errors) == 1


@pytest.mark.unit
class TestJobContentValidation:
    """Testes de validação de conteúdo de vagas."""
    
    def test_validate_valid_job_content(self):
        """Teste com conteúdo de vaga válido."""
        content = """
        Desenvolvedor Python Sênior
        
        A Tech Corp está contratando um desenvolvedor Python experiente.
        
        Responsabilidades:
        - Desenvolver APIs REST com FastAPI
        - Trabalhar com microserviços
        - Mentoria de desenvolvedores júnior
        
        Requisitos:
        - 5+ anos de experiência com Python
        - Experiência com FastAPI e Docker
        - Conhecimento de bancos de dados SQL e NoSQL
        - Inglês fluente
        
        Benefícios:
        - Salário competitivo
        - Home office
        - Vale alimentação e refeição
        """
        
        result = validate_and_score_job_content(content)
        
        assert result.is_valid
        assert result.score > 0.6
        assert len(result.validation_errors) == 0
    
    def test_validate_short_job_content(self):
        """Teste com conteúdo muito curto."""
        content = "Vaga de Python"
        
        result = validate_and_score_job_content(content)
        
        assert not result.is_valid
        assert result.score < 0.3
        assert any("curto" in error.lower() for error in result.validation_errors)
    
    def test_validate_empty_job_content(self):
        """Teste com conteúdo vazio."""
        content = ""
        
        result = validate_and_score_job_content(content)
        
        assert not result.is_valid
        assert result.score == 0.0
        assert len(result.validation_errors) > 0
    
    def test_validate_medium_quality_content(self):
        """Teste com conteúdo de qualidade média."""
        content = """
        Desenvolvedor Python
        Empresa de tecnologia contrata desenvolvedor Python.
        Requisitos: Python, FastAPI, Docker
        """
        
        result = validate_and_score_job_content(content)
        
        # Pode ser válido ou inválido dependendo dos critérios
        assert 0.3 <= result.score <= 0.7
        assert len(result.suggestions) > 0


@pytest.mark.unit
class TestJobDetailsValidation:
    """Testes de validação de detalhes estruturados de vagas."""
    
    def test_validate_complete_job_details(self):
        """Teste com detalhes completos de vaga."""
        details = {
            "title": "Desenvolvedor Python Sênior",
            "company": "Tech Corp",
            "description": "Desenvolver APIs REST com FastAPI e trabalhar com microserviços.",
            "requirements": [
                "5+ anos de experiência com Python",
                "Experiência com FastAPI",
                "Conhecimento de Docker e Kubernetes"
            ],
            "location": "São Paulo, SP (Remoto)",
            "type": "CLT",
            "salary": "R$ 10.000 - R$ 15.000"
        }
        
        result = validate_and_score_job_details(details)
        
        assert result.is_valid
        assert result.score > 0.8
        assert len(result.validation_errors) == 0
    
    def test_validate_missing_required_fields(self):
        """Teste com campos obrigatórios faltando."""
        details = {
            "title": "Desenvolvedor Python"
            # Falta company, description, requirements
        }
        
        result = validate_and_score_job_details(details)
        
        assert not result.is_valid
        assert result.score < 0.5
        assert len(result.validation_errors) > 0
    
    def test_validate_minimal_valid_details(self):
        """Teste com detalhes mínimos mas válidos."""
        details = {
            "title": "Desenvolvedor Python",
            "company": "Tech Corp",
            "description": "Desenvolver aplicações Python para sistemas internos.",
            "requirements": ["Python", "FastAPI"]
        }
        
        result = validate_and_score_job_details(details)
        
        assert result.is_valid
        assert 0.5 <= result.score <= 0.8
    
    def test_validate_empty_requirements(self):
        """Teste com lista de requisitos vazia."""
        details = {
            "title": "Desenvolvedor Python",
            "company": "Tech Corp",
            "description": "Desenvolver aplicações Python.",
            "requirements": []
        }
        
        result = validate_and_score_job_details(details)
        
        # Pode ser válido mas com score baixo
        assert result.score < 0.7
        assert any("requisitos" in sugg.lower() for sugg in result.suggestions)

