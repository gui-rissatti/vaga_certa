"""
Smoke Test E2E - Teste crítico para validação de produção.

Este teste valida o fluxo completo da aplicação:
1. Extração de conteúdo de vaga
2. Extração de detalhes estruturados
3. Geração de materiais (CV otimizado, carta, etc)
4. Validação de qualidade do output

Deve rodar após cada deploy para garantir que a funcionalidade 
principal está operacional.
"""
import pytest
import os
from fastapi.testclient import TestClient


@pytest.mark.smoke
@pytest.mark.requires_api
class TestGenerateCV_E2E:
    """Teste end-to-end da geração de CV."""
    
    @pytest.fixture(scope="class")
    def client(self):
        """Cliente de teste para API."""
        # Só importa app se API key estiver configurada
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key or "test" in api_key.lower() or "mock" in api_key.lower():
            pytest.skip("Requer GOOGLE_API_KEY real configurada")
        
        from api.main import app
        return TestClient(app)
    
    @pytest.fixture
    def real_cv_sample(self):
        """CV realista para teste."""
        return """
        Maria Silva Santos
        Desenvolvedora Full Stack Python/React
        Email: maria.silva@email.com | LinkedIn: /maria-silva-dev
        São Paulo, SP - Disponível para remoto
        
        RESUMO PROFISSIONAL
        Desenvolvedora Full Stack com 5 anos de experiência em desenvolvimento de 
        aplicações web escaláveis usando Python (FastAPI, Django) e React. Expertise 
        em arquitetura de microserviços, APIs REST, e deployment em cloud (AWS, Azure).
        
        EXPERIÊNCIA PROFISSIONAL
        
        Tech Solutions S.A. | Desenvolvedora Sênior | Mar 2021 - Presente
        - Desenvolvimento de APIs REST com FastAPI servindo 10k+ requisições/dia
        - Implementação de microserviços usando Docker e Kubernetes
        - Frontend React com TypeScript e Material-UI
        - Integração com serviços AWS (S3, Lambda, RDS)
        - Mentoria de 3 desenvolvedores júnior
        - Redução de 40% no tempo de resposta das APIs através de otimizações
        
        Startup Inovadora | Desenvolvedora Full Stack | Jan 2020 - Fev 2021
        - Desenvolvimento de MVP do zero usando Python + React
        - Implementação de autenticação JWT e autorização baseada em roles
        - Deploy automatizado com GitHub Actions e Heroku
        - Testes automatizados com pytest e Jest
        
        HABILIDADES TÉCNICAS
        - Backend: Python, FastAPI, Django, Flask, SQLAlchemy, Celery
        - Frontend: React, TypeScript, JavaScript, HTML5, CSS3, Tailwind
        - Banco de Dados: PostgreSQL, MySQL, MongoDB, Redis
        - DevOps: Docker, Kubernetes, GitHub Actions, AWS, Azure
        - Ferramentas: Git, Linux, Nginx, RabbitMQ
        
        FORMAÇÃO
        Ciência da Computação | Universidade de São Paulo (USP) | 2015-2019
        
        IDIOMAS
        Português: Nativo
        Inglês: Avançado (C1)
        
        CERTIFICAÇÕES
        - AWS Certified Developer Associate (2022)
        - Python Institute PCAP (2020)
        """
    
    @pytest.fixture
    def real_job_url_sample(self):
        """URL de vaga realista (pode ser mockada se necessário)."""
        # Em produção real, usar URL verdadeira
        # Para testes, podemos usar uma URL de exemplo
        return "https://www.linkedin.com/jobs/view/3234567890"
    
    def test_health_check_before_test(self, client):
        """Pre-check: API deve estar saudável antes do teste."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["config"]["google_api_configured"] is True
        assert data["config"]["agents_initialized"] is True
    
    def test_generate_complete_cv_flow(self, client, real_cv_sample):
        """
        SMOKE TEST CRÍTICO: Geração completa de CV deve funcionar.
        
        Este é o teste de validação de produção. Se falhar,
        a aplicação não está pronta para uso.
        """
        # Dados de entrada
        payload = {
            "cv_text": real_cv_sample,
            "job_url": "https://example.com/vaga-python-senior",
            "tone": "professional",
            "language": "pt-BR"
        }
        
        # Executa requisição
        response = client.post("/generate-complete", json=payload, timeout=60)
        
        # Validações críticas
        assert response.status_code == 200, f"Falha na geração: {response.text}"
        
        data = response.json()
        
        # Valida estrutura da resposta
        assert "job_details" in data, "job_details ausente na resposta"
        assert "generated_content" in data, "generated_content ausente na resposta"
        assert "compatibility" in data, "compatibility ausente na resposta"
        
        # Valida job_details
        job_details = data["job_details"]
        assert "title" in job_details, "title ausente em job_details"
        assert "company" in job_details, "company ausente em job_details"
        assert len(job_details.get("title", "")) > 0, "title está vazio"
        
        # Valida generated_content
        generated = data["generated_content"]
        assert "optimized_cv" in generated, "optimized_cv ausente"
        assert "cover_letter" in generated, "cover_letter ausente"
        assert "networking_message" in generated, "networking_message ausente"
        assert "interview_tips" in generated, "interview_tips ausente"
        
        # Valida qualidade do conteúdo gerado
        optimized_cv = generated["optimized_cv"]
        assert len(optimized_cv) > 200, "CV otimizado muito curto (< 200 chars)"
        assert len(optimized_cv) < 10000, "CV otimizado muito longo (> 10k chars)"
        
        cover_letter = generated["cover_letter"]
        assert len(cover_letter) > 100, "Carta muito curta (< 100 chars)"
        assert len(cover_letter) < 5000, "Carta muito longa (> 5k chars)"
        
        networking_message = generated["networking_message"]
        assert len(networking_message) > 50, "Mensagem muito curta (< 50 chars)"
        assert len(networking_message) < 1000, "Mensagem muito longa (> 1k chars)"
        
        interview_tips = generated["interview_tips"]
        assert isinstance(interview_tips, list), "interview_tips não é uma lista"
        assert len(interview_tips) >= 3, "Poucas dicas de entrevista (< 3)"
        
        # Valida compatibility
        compatibility = data["compatibility"]
        assert "score" in compatibility, "score ausente em compatibility"
        score = compatibility["score"]
        assert isinstance(score, (int, float)), "score não é numérico"
        assert 0.0 <= score <= 1.0, f"score fora do range [0,1]: {score}"
        
        # Log de sucesso para monitoramento
        print(f"✅ SMOKE TEST PASSOU - Score: {score:.2f}")
        print(f"   CV otimizado: {len(optimized_cv)} chars")
        print(f"   Carta: {len(cover_letter)} chars")
        print(f"   Dicas: {len(interview_tips)} itens")
    
    def test_extract_job_details_only(self, client):
        """Teste do fluxo de extração isolado."""
        payload = {
            "url": "https://example.com/vaga",
            "content": """
            Desenvolvedor Python Sênior
            
            A Tech Corp está contratando um desenvolvedor Python experiente para 
            trabalhar com FastAPI e microserviços.
            
            Requisitos:
            - 5+ anos de experiência com Python
            - Experiência com FastAPI
            - Docker e Kubernetes
            """
        }
        
        response = client.post("/extract-job-details", json=payload, timeout=30)
        
        assert response.status_code == 200
        data = response.json()
        assert "title" in data
        assert "company" in data or "description" in data
    
    def test_generate_materials_with_mock_job(self, client, real_cv_sample):
        """Teste de geração com job details mock."""
        payload = {
            "cv_text": real_cv_sample,
            "job_details": {
                "title": "Desenvolvedor Python Sênior",
                "company": "Tech Corp",
                "description": "Desenvolvimento de APIs REST com FastAPI",
                "requirements": [
                    "Python",
                    "FastAPI",
                    "Docker"
                ]
            },
            "tone": "professional",
            "language": "pt-BR"
        }
        
        response = client.post("/generate-materials", json=payload, timeout=60)
        
        assert response.status_code == 200
        data = response.json()
        assert "optimized_cv" in data
        assert len(data["optimized_cv"]) > 100


@pytest.mark.smoke
class TestProductionReadiness:
    """Testes de prontidão para produção."""
    
    def test_environment_variables_set(self):
        """Valida que variáveis críticas estão configuradas."""
        google_key = os.getenv("GOOGLE_API_KEY")
        
        if not google_key:
            pytest.skip("GOOGLE_API_KEY não configurada (OK para dev)")
        
        # Valida que não é placeholder
        assert "your_" not in google_key.lower()
        assert "example" not in google_key.lower()
        assert "test" not in google_key.lower()
        assert len(google_key) > 20
    
    def test_api_health_endpoint_accessible(self):
        """Valida que o health endpoint está acessível."""
        from api.main import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        response = client.get("/health")
        
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_required_modules_importable(self):
        """Valida que todos os módulos essenciais são importáveis."""
        try:
            import fastapi
            import langchain
            import langchain_google_genai
            import bs4
            import httpx
            import structlog
            import pydantic
            import uvicorn
        except ImportError as e:
            pytest.fail(f"Módulo essencial faltando: {e}")
        
        # Tudo OK
        assert True

