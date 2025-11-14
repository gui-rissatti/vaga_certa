"""
Configuração global do pytest.
Fixtures compartilhadas entre todos os testes.
"""
import pytest
import sys
from pathlib import Path

# Adiciona o backend ao path para imports
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))


@pytest.fixture
def mock_google_api_key(monkeypatch):
    """Mock da API key do Google para testes."""
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key-mock-12345")


@pytest.fixture
def mock_langchain_disabled(monkeypatch):
    """Desabilita LangSmith em testes."""
    monkeypatch.setenv("LANGCHAIN_TRACING_V2", "false")
    monkeypatch.setenv("LANGCHAIN_API_KEY", "")


@pytest.fixture
def sample_cv_text():
    """CV de exemplo para testes."""
    return """
    João Silva
    Desenvolvedor Full Stack
    
    Experiência:
    - Empresa XYZ (2020-2023): Desenvolvedor Python/React
    - Startup ABC (2018-2020): Desenvolvedor Junior
    
    Habilidades:
    Python, FastAPI, React, TypeScript, Docker, AWS
    
    Formação:
    Ciência da Computação - USP (2014-2018)
    """


@pytest.fixture
def sample_job_url():
    """URL de vaga de exemplo para testes."""
    return "https://example.com/vaga-desenvolvedor-python"


@pytest.fixture
def sample_job_details():
    """Detalhes de vaga de exemplo para testes."""
    return {
        "title": "Desenvolvedor Python Sênior",
        "company": "Tech Corp",
        "description": "Procuramos desenvolvedor Python com experiência em FastAPI e microserviços.",
        "requirements": [
            "5+ anos de experiência com Python",
            "Experiência com FastAPI",
            "Conhecimento de Docker e Kubernetes",
            "Inglês avançado"
        ],
        "location": "São Paulo, SP (Remoto)",
        "type": "CLT"
    }

