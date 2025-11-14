"""
Configuração centralizada da aplicação usando Pydantic Settings.
Garante type safety e validação de variáveis de ambiente.
"""
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Optional
import os
import warnings


class Settings(BaseSettings):
    """Configurações da aplicação carregadas de variáveis de ambiente."""
    
    # Google Gemini API - Opcional na inicialização para não crashar no Vercel
    # mas será validada no startup da aplicação
    google_api_key: Optional[str] = None
    
    @field_validator('google_api_key')
    @classmethod
    def validate_google_api_key(cls, v: Optional[str]) -> Optional[str]:
        """Valida que a API key do Google está presente e não é placeholder."""
        if v and ("your_" in v.lower() or "example" in v.lower()):
            warnings.warn(
                "⚠️ GOOGLE_API_KEY parece ser um placeholder. "
                "Configure a chave real em https://aistudio.google.com/app/apikey"
            )
        return v
    
    def is_configured(self) -> bool:
        """Verifica se a aplicação está completamente configurada."""
        return bool(self.google_api_key and 
                   self.google_api_key.strip() and 
                   "your_" not in self.google_api_key.lower())
    
    # LangSmith Configuration (opcional no Vercel)
    langchain_api_key: Optional[str] = None
    langchain_tracing_v2: bool = False  # Desabilitado por padrão no Vercel
    langchain_project: str = "vaga_certa_production"
    langchain_endpoint: str = "https://api.smith.langchain.com"
    
    # Application Settings
    environment: str = "production"
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Rate Limiting
    max_requests_per_minute: int = 60
    max_requests_per_hour: int = 1000
    
    # Timeouts
    request_timeout_seconds: int = 300
    scraping_timeout_seconds: int = 30
    
    # CORS
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:5174"
    ]
    
    @field_validator('cors_origins', mode='before')
    @classmethod
    def parse_cors_origins(cls, v) -> list[str]:
        """Converte string separada por vírgulas em lista."""
        if isinstance(v, str):
            # Remove espaços e divide por vírgula
            return [origin.strip() for origin in v.split(',') if origin.strip()]
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Instância global de configurações
settings = Settings()

