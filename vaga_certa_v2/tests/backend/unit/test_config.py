"""
Testes unitários para o módulo de configuração.
"""
import pytest
from config import Settings


@pytest.mark.unit
class TestSettings:
    """Testes da classe Settings."""
    
    def test_settings_default_values(self, mock_google_api_key, mock_langchain_disabled):
        """Teste valores padrão das configurações."""
        settings = Settings()
        
        assert settings.environment == "production"
        assert settings.log_level == "INFO"
        assert settings.api_host == "0.0.0.0"
        assert settings.api_port == 8000
        assert isinstance(settings.cors_origins, list)
        assert len(settings.cors_origins) > 0
    
    def test_settings_google_api_key_validation(self, monkeypatch):
        """Teste validação da API key do Google."""
        # Testa com placeholder
        monkeypatch.setenv("GOOGLE_API_KEY", "your_api_key_here")
        settings = Settings()
        
        # Deve aceitar mas gerar warning (não testamos o warning aqui)
        assert settings.google_api_key == "your_api_key_here"
    
    def test_settings_is_configured(self, monkeypatch):
        """Teste do método is_configured."""
        # Configurado corretamente
        monkeypatch.setenv("GOOGLE_API_KEY", "AIzaSyABC123xyz")
        settings = Settings()
        assert settings.is_configured()
        
        # Não configurado (None)
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        settings = Settings()
        assert not settings.is_configured()
        
        # Não configurado (placeholder)
        monkeypatch.setenv("GOOGLE_API_KEY", "your_api_key_here")
        settings = Settings()
        assert not settings.is_configured()
    
    def test_settings_cors_origins_from_string(self, monkeypatch):
        """Teste parsing de CORS_ORIGINS como string."""
        monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173")
        monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
        
        settings = Settings()
        
        assert isinstance(settings.cors_origins, list)
        assert len(settings.cors_origins) == 2
        assert "http://localhost:3000" in settings.cors_origins
        assert "http://localhost:5173" in settings.cors_origins
    
    def test_settings_cors_origins_with_spaces(self, monkeypatch):
        """Teste parsing de CORS_ORIGINS com espaços."""
        monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000, http://localhost:5173 , http://localhost:8080")
        monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
        
        settings = Settings()
        
        assert len(settings.cors_origins) == 3
        # Deve remover espaços extras
        assert all(origin.strip() == origin for origin in settings.cors_origins)
    
    def test_settings_timeouts(self, mock_google_api_key):
        """Teste configurações de timeout."""
        settings = Settings()
        
        assert settings.request_timeout_seconds > 0
        assert settings.scraping_timeout_seconds > 0
        assert settings.request_timeout_seconds >= settings.scraping_timeout_seconds
    
    def test_settings_rate_limiting(self, mock_google_api_key):
        """Teste configurações de rate limiting."""
        settings = Settings()
        
        assert settings.max_requests_per_minute > 0
        assert settings.max_requests_per_hour > 0
        assert settings.max_requests_per_hour >= settings.max_requests_per_minute

