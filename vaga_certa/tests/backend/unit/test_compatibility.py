"""
Testes unitários para o módulo de compatibilidade.
"""
import pytest
from utils.compatibility import calculate_compatibility, CompatibilityInsights


@pytest.mark.unit
class TestCompatibilityCalculation:
    """Testes de cálculo de compatibilidade."""
    
    def test_high_compatibility(self):
        """Teste com alta compatibilidade entre CV e vaga."""
        cv_text = """
        João Silva
        Desenvolvedor Python Sênior com 7 anos de experiência
        
        Experiências:
        - Tech Corp (2020-presente): Desenvolvedor Python Sênior
          * Desenvolvimento de APIs REST com FastAPI
          * Arquitetura de microserviços
          * Deploy com Docker e Kubernetes
          * Trabalho com AWS (EC2, S3, Lambda)
        
        Habilidades:
        Python, FastAPI, Docker, Kubernetes, AWS, PostgreSQL, Redis, Git
        
        Formação:
        Ciência da Computação - USP (2012-2016)
        """
        
        job_description = """
        Desenvolvedor Python Sênior
        
        Requisitos:
        - 5+ anos de experiência com Python
        - Experiência com FastAPI
        - Conhecimento de Docker e Kubernetes
        - Experiência com AWS
        - Bancos de dados relacionais
        """
        
        result = calculate_compatibility(cv_text, job_description)
        
        assert isinstance(result, CompatibilityInsights)
        assert result.score >= 0.7
        assert len(result.matching_skills) > 0
        assert len(result.strengths) > 0
    
    def test_medium_compatibility(self):
        """Teste com compatibilidade média."""
        cv_text = """
        Maria Santos
        Desenvolvedora Python Júnior com 2 anos de experiência
        
        Experiências:
        - Startup XYZ (2022-2024): Desenvolvedora Python
          * Desenvolvimento de scripts de automação
          * APIs simples com Flask
        
        Habilidades:
        Python, Flask, Git, MySQL
        """
        
        job_description = """
        Desenvolvedor Python Sênior
        
        Requisitos:
        - 5+ anos de experiência com Python
        - Experiência com FastAPI
        - Conhecimento de Docker e Kubernetes
        - Experiência com AWS
        """
        
        result = calculate_compatibility(cv_text, job_description)
        
        assert 0.3 <= result.score <= 0.6
        assert len(result.gaps) > 0
        assert len(result.suggestions) > 0
    
    def test_low_compatibility(self):
        """Teste com baixa compatibilidade."""
        cv_text = """
        Pedro Costa
        Designer Gráfico com 5 anos de experiência
        
        Habilidades:
        Photoshop, Illustrator, Figma, After Effects
        """
        
        job_description = """
        Desenvolvedor Python Sênior
        
        Requisitos:
        - 5+ anos de experiência com Python
        - Experiência com FastAPI
        - Conhecimento de Docker
        """
        
        result = calculate_compatibility(cv_text, job_description)
        
        assert result.score < 0.3
        assert len(result.gaps) > len(result.matching_skills)
        assert len(result.suggestions) > 0
    
    def test_empty_inputs(self):
        """Teste com entradas vazias."""
        result = calculate_compatibility("", "")
        
        assert result.score == 0.0
        assert len(result.matching_skills) == 0
        assert len(result.strengths) == 0
    
    def test_only_cv_provided(self):
        """Teste com apenas CV fornecido."""
        cv_text = "João Silva, Desenvolvedor Python"
        job_description = ""
        
        result = calculate_compatibility(cv_text, job_description)
        
        assert result.score < 0.3
        assert len(result.gaps) > 0
    
    def test_compatibility_insights_structure(self):
        """Teste da estrutura do resultado de compatibilidade."""
        cv_text = "Python, FastAPI, Docker"
        job_description = "Requisitos: Python, FastAPI, Docker"
        
        result = calculate_compatibility(cv_text, job_description)
        
        # Verifica que todos os campos esperados existem
        assert hasattr(result, 'score')
        assert hasattr(result, 'matching_skills')
        assert hasattr(result, 'gaps')
        assert hasattr(result, 'strengths')
        assert hasattr(result, 'suggestions')
        
        # Verifica tipos
        assert isinstance(result.score, (int, float))
        assert isinstance(result.matching_skills, list)
        assert isinstance(result.gaps, list)
        assert isinstance(result.strengths, list)
        assert isinstance(result.suggestions, list)
        
        # Score deve estar entre 0 e 1
        assert 0.0 <= result.score <= 1.0

