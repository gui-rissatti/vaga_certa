"""
Configuração do LangSmith para observabilidade.
Deve ser importado antes de qualquer uso dos agentes.
"""
import os
from config import settings

# Configura LangSmith se API key estiver disponível
if settings.langchain_api_key:
    os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
    os.environ["LANGCHAIN_TRACING_V2"] = str(settings.langchain_tracing_v2).lower()
    os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project
    os.environ["LANGCHAIN_ENDPOINT"] = settings.langchain_endpoint
    
    print(f"✅ LangSmith configurado - Projeto: {settings.langchain_project}")
else:
    print("⚠️ LangSmith não configurado - LANGCHAIN_API_KEY não encontrada")

