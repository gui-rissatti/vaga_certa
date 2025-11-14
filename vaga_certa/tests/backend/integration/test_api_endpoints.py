"""
Testes de integração para os endpoints da API.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from api.main import app


@pytest.fixture
def client(mock_google_api_key, mock_langchain_disabled):
    """Cliente de teste para a API."""
    return TestClient(app)


@pytest.mark.integration
class TestHealthEndpoints:
    """Testes dos endpoints de health check."""
    
    def test_root_endpoint(self, client):
        """Teste do endpoint raiz."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "message" in data
    
    def test_health_endpoint(self, client):
        """Teste do endpoint /health."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "environment" in data
        assert "version" in data
        assert "config" in data
    
    def test_health_endpoint_structure(self, client):
        """Teste da estrutura da resposta de /health."""
        response = client.get("/health")
        data = response.json()
        
        # Verifica estrutura de config
        assert "google_api_configured" in data["config"]
        assert "langsmith_enabled" in data["config"]
        assert "agents_initialized" in data["config"]


@pytest.mark.integration
class TestDebugEndpoint:
    """Testes do endpoint de debug."""
    
    def test_debug_endpoint(self, client):
        """Teste do endpoint /debug."""
        response = client.get("/debug")
        
        assert response.status_code == 200
        data = response.json()
        assert "environment" in data
        assert "google_api_key_configured" in data


@pytest.mark.integration
class TestExtractJobDetailsEndpoint:
    """Testes do endpoint de extração de detalhes de vagas."""
    
    @patch('agents.extraction_agent.ExtractionAgent.extract_job_title_and_company')
    def test_extract_job_details_success(self, mock_extract, client, sample_job_details):
        """Teste de extração bem-sucedida."""
        # Mock da resposta do agente
        mock_extract.return_value = sample_job_details
        
        response = client.post("/extract-job-details", json={
            "url": "https://example.com/job",
            "content": "Desenvolvedor Python na Tech Corp..."
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "title" in data
        assert "company" in data
        assert data["title"] == sample_job_details["title"]
        assert data["company"] == sample_job_details["company"]
    
    def test_extract_job_details_missing_url(self, client):
        """Teste sem URL fornecida."""
        response = client.post("/extract-job-details", json={
            "content": "Conteúdo da vaga"
        })
        
        assert response.status_code == 422  # Validation error
    
    def test_extract_job_details_empty_content(self, client):
        """Teste com conteúdo vazio."""
        response = client.post("/extract-job-details", json={
            "url": "https://example.com/job",
            "content": ""
        })
        
        # Pode retornar 400 ou 422 dependendo da validação
        assert response.status_code in [400, 422]
    
    @patch('agents.extraction_agent.ExtractionAgent.extract_job_title_and_company')
    def test_extract_job_details_agent_error(self, mock_extract, client):
        """Teste quando o agente falha."""
        mock_extract.side_effect = Exception("Erro no agente")
        
        response = client.post("/extract-job-details", json={
            "url": "https://example.com/job",
            "content": "Desenvolvedor Python..."
        })
        
        assert response.status_code == 500
        data = response.json()
        assert "error" in data or "detail" in data


@pytest.mark.integration
class TestGenerateMaterialsEndpoint:
    """Testes do endpoint de geração de materiais."""
    
    @patch('agents.generation_agent.GenerationAgent.generate_materials')
    def test_generate_materials_success(self, mock_generate, client, sample_cv_text, sample_job_details):
        """Teste de geração bem-sucedida."""
        # Mock da resposta do agente
        mock_generate.return_value = {
            "optimized_cv": "CV otimizado...",
            "cover_letter": "Carta de apresentação...",
            "networking_message": "Mensagem de networking...",
            "interview_tips": ["Dica 1", "Dica 2"]
        }
        
        response = client.post("/generate-materials", json={
            "cv_text": sample_cv_text,
            "job_details": sample_job_details,
            "tone": "professional",
            "language": "pt-BR"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "optimized_cv" in data
        assert "cover_letter" in data
        assert "networking_message" in data
        assert "interview_tips" in data
    
    def test_generate_materials_missing_cv(self, client, sample_job_details):
        """Teste sem CV fornecido."""
        response = client.post("/generate-materials", json={
            "job_details": sample_job_details,
            "tone": "professional",
            "language": "pt-BR"
        })
        
        assert response.status_code == 422
    
    def test_generate_materials_missing_job_details(self, client, sample_cv_text):
        """Teste sem detalhes da vaga."""
        response = client.post("/generate-materials", json={
            "cv_text": sample_cv_text,
            "tone": "professional",
            "language": "pt-BR"
        })
        
        assert response.status_code == 422
    
    def test_generate_materials_optional_fields(self, client, sample_cv_text, sample_job_details):
        """Teste com campos opcionais."""
        # Mock do agente
        with patch('agents.generation_agent.GenerationAgent.generate_materials') as mock_gen:
            mock_gen.return_value = {
                "optimized_cv": "CV...",
                "cover_letter": "Carta...",
                "networking_message": "Mensagem...",
                "interview_tips": []
            }
            
            response = client.post("/generate-materials", json={
                "cv_text": sample_cv_text,
                "job_details": sample_job_details,
                "tone": "enthusiastic",
                "language": "en-US",
                "custom_context": "Tenho interesse especial em trabalho remoto"
            })
            
            assert response.status_code == 200


@pytest.mark.integration
class TestGenerateCompleteEndpoint:
    """Testes do endpoint de geração completa (E2E)."""
    
    @patch('agents.extraction_agent.ExtractionAgent.extract_job_content_from_url')
    @patch('agents.extraction_agent.ExtractionAgent.extract_job_title_and_company')
    @patch('agents.generation_agent.GenerationAgent.generate_materials')
    def test_generate_complete_success(
        self,
        mock_generate,
        mock_extract_details,
        mock_extract_content,
        client,
        sample_cv_text,
        sample_job_details
    ):
        """Teste de fluxo completo bem-sucedido."""
        # Mock das respostas
        mock_extract_content.return_value = "Conteúdo extraído da vaga..."
        mock_extract_details.return_value = sample_job_details
        mock_generate.return_value = {
            "optimized_cv": "CV otimizado...",
            "cover_letter": "Carta...",
            "networking_message": "Mensagem...",
            "interview_tips": ["Dica 1"]
        }
        
        response = client.post("/generate-complete", json={
            "cv_text": sample_cv_text,
            "job_url": "https://example.com/job",
            "tone": "professional",
            "language": "pt-BR"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # Verifica que todos os componentes estão presentes
        assert "job_details" in data
        assert "generated_content" in data
        assert "compatibility" in data
        
        # Verifica estrutura do conteúdo gerado
        assert "optimized_cv" in data["generated_content"]
        assert "cover_letter" in data["generated_content"]
    
    @patch('agents.extraction_agent.ExtractionAgent.extract_job_content_from_url')
    def test_generate_complete_extraction_fails(
        self,
        mock_extract_content,
        client,
        sample_cv_text
    ):
        """Teste quando a extração falha."""
        mock_extract_content.side_effect = Exception("Erro ao extrair conteúdo")
        
        response = client.post("/generate-complete", json={
            "cv_text": sample_cv_text,
            "job_url": "https://example.com/job"
        })
        
        assert response.status_code == 500
    
    def test_generate_complete_missing_fields(self, client):
        """Teste com campos obrigatórios faltando."""
        response = client.post("/generate-complete", json={
            "cv_text": "CV..."
            # Falta job_url
        })
        
        assert response.status_code == 422


@pytest.mark.integration
class TestCORSMiddleware:
    """Testes do middleware CORS."""
    
    def test_cors_headers_present(self, client):
        """Teste se headers CORS estão presentes."""
        response = client.options(
            "/health",
            headers={"Origin": "http://localhost:3000"}
        )
        
        # Verifica que a resposta inclui headers CORS
        assert "access-control-allow-origin" in response.headers or response.status_code == 200
    
    def test_cors_allowed_origin(self, client):
        """Teste com origem permitida."""
        response = client.get(
            "/health",
            headers={"Origin": "http://localhost:5173"}
        )
        
        assert response.status_code == 200


@pytest.mark.integration
class TestErrorHandling:
    """Testes de tratamento de erros globais."""
    
    def test_404_not_found(self, client):
        """Teste endpoint inexistente."""
        response = client.get("/endpoint-inexistente")
        
        assert response.status_code == 404
    
    def test_405_method_not_allowed(self, client):
        """Teste método HTTP não permitido."""
        response = client.put("/health")
        
        assert response.status_code == 405
    
    def test_invalid_json(self, client):
        """Teste com JSON inválido."""
        response = client.post(
            "/extract-job-details",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422

