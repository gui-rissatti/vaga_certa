"""
API REST principal usando FastAPI.
Implementa endpoints para extração e geração de materiais de carreira.
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog
from contextlib import asynccontextmanager
import os

import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Importa configuração do LangSmith primeiro
import setup_langsmith

# Tenta carregar configurações e fornece mensagem clara se falhar
try:
    from config import settings
except Exception as e:
    logger_error = structlog.get_logger()
    logger_error.critical(
        "Falha ao carregar configurações - verifique variáveis de ambiente",
        error=str(e)
    )
    # Re-raise para Vercel capturar no log
    raise

from agents import ExtractionAgent, GenerationAgent
from api.models import (
    JobExtractionRequest,
    UserInputRequest,
    JobDetailsResponse,
    GenerateMaterialsRequest,
    GeneratedContentResponse,
    ErrorResponse
)

# Configuração de logging estruturado
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer()
    ]
)
logger = structlog.get_logger()


# Instâncias globais dos agentes (singleton)
extraction_agent: ExtractionAgent = None
generation_agent: GenerationAgent = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia ciclo de vida da aplicação."""
    global extraction_agent, generation_agent
    
    # Startup
    logger.info("Inicializando aplicação Vaga Certa")
    
    # Verifica se GOOGLE_API_KEY está configurada
    if not settings.is_configured():
        logger.critical(
            "❌ GOOGLE_API_KEY não configurada!",
            google_api_key_present=bool(settings.google_api_key),
            environment=settings.environment
        )
        logger.error(
            "Para configurar:\n"
            "1. Render: Dashboard → Environment → Add GOOGLE_API_KEY\n"
            "2. Vercel: Execute 'vercel env add GOOGLE_API_KEY'\n"
            "3. Obtenha sua chave em: https://aistudio.google.com/app/apikey\n"
            "4. Redeploy: git push origin main"
        )
        # Não falha para permitir health check, mas agentes não serão inicializados
        extraction_agent = None
        generation_agent = None
    else:
        logger.info("Inicializando agentes de IA")
        extraction_agent = ExtractionAgent()
        generation_agent = GenerationAgent()
        logger.info("Agentes inicializados com sucesso")
    
    yield
    
    # Shutdown
    logger.info("Encerrando aplicação")
    if extraction_agent and extraction_agent.web_scraper:
        await extraction_agent.web_scraper.close()


# Cria aplicação FastAPI
app = FastAPI(
    title="Portfolio Agent API",
    description="API para geração de materiais de carreira personalizados usando LangChain e LangSmith",
    version="2.0.0",
    lifespan=lifespan
)

# Configuração CORS - permitir Render, Vercel e localhost
cors_origins = settings.cors_origins.copy()

# Adicionar origens de produção baseadas no ambiente
if os.getenv("RENDER"):
    # Rodando no Render.com
    cors_origins.extend([
        "https://*.onrender.com",
        "https://vaga-certa-frontend.onrender.com",
    ])
    logger.info("CORS configurado para Render.com")
elif os.getenv("VERCEL"):
    # Rodando no Vercel (fallback)
    cors_origins.extend([
        "https://*.vercel.app",
        "https://vaga-certa.vercel.app",
    ])
    logger.info("CORS configurado para Vercel")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware de logging para debug de roteamento no Vercel
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Middleware para debug de roteamento no Vercel.
    
    Logs detalhados para diagnosticar problemas de roteamento:
    - Path recebido pelo FastAPI
    - Headers importantes
    - Status code da resposta
    """
    logger.info(
        "🔍 Request received",
        method=request.method,
        path=request.url.path,
        full_url=str(request.url),
        root_path=app.root_path if hasattr(app, 'root_path') else "N/A",
        headers={
            "host": request.headers.get("host", "N/A"),
            "x-forwarded-for": request.headers.get("x-forwarded-for", "N/A"),
            "x-vercel-id": request.headers.get("x-vercel-id", "N/A"),
        },
        client=request.client.host if request.client else "unknown"
    )
    
    try:
        response = await call_next(request)
        
        logger.info(
            "✅ Response sent",
            status_code=response.status_code,
            path=request.url.path
        )
        return response
    except Exception as e:
        logger.error(
            "❌ Error processing request",
            path=request.url.path,
            error=str(e),
            error_type=type(e).__name__
        )
        raise


# Handlers de erro global
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handler para erros de validação."""
    logger.warning("Erro de validação", error=str(exc))
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(
            error="Erro de validação",
            detail=str(exc),
            error_code="VALIDATION_ERROR"
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handler para erros gerais."""
    logger.error("Erro não tratado", error=str(exc), error_type=type(exc).__name__)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Erro interno do servidor",
            detail="Ocorreu um erro inesperado. Por favor, tente novamente.",
            error_code="INTERNAL_ERROR"
        ).dict()
    )


# Endpoints
@app.get("/")
async def root():
    """
    Rota raiz para validação básica do roteamento.
    
    Esta rota ajuda a diagnosticar se o FastAPI está recebendo requisições corretamente.
    Se esta rota funcionar no Vercel (/api/), sabemos que o roteamento básico está OK.
    """
    return {
        "message": "FastAPI rodando no Vercel! 🚀",
        "status": "ok",
        "version": "2.0.0",
        "documentation": "/docs",
        "endpoints": {
            "health": "/health",
            "extract_job": "/extract-job-details",
            "generate_materials": "/generate-materials",
            "generate_complete": "/generate-complete"
        }
    }


@app.get("/health")
async def health_check():
    """Endpoint de health check com validação de configuração."""
    is_configured = settings.is_configured()
    
    response = {
        "status": "healthy" if is_configured else "misconfigured",
        "environment": settings.environment,
        "version": "2.0.0",
        "config": {
            "google_api_configured": is_configured,
            "langsmith_enabled": settings.langchain_tracing_v2,
            "agents_initialized": extraction_agent is not None and generation_agent is not None
        }
    }
    
    if not is_configured:
        response["error"] = {
            "code": "MISSING_API_KEY",
            "message": "GOOGLE_API_KEY não configurada",
            "instructions": [
                "Execute: vercel env add GOOGLE_API_KEY",
                "Cole sua chave do Google Gemini",
                "Obtenha em: https://aistudio.google.com/app/apikey",
                "Redeploy: git push origin main"
            ]
        }
    
    return response


@app.get("/debug")
async def debug_info(request: Request):
    """
    Endpoint de debug para verificar configuração no Vercel.
    
    Retorna informações sobre:
    - root_path configurado
    - URL da requisição
    - Rotas registradas
    - Configurações do ambiente
    
    Útil para diagnosticar problemas de roteamento e configuração.
    """
    return {
        "app_root_path": app.root_path,
        "request_url": str(request.url),
        "request_path": request.url.path,
        "request_base_url": str(request.base_url),
        "routes": [
            {
                "path": route.path,
                "name": route.name,
                "methods": list(route.methods) if hasattr(route, 'methods') else []
            }
            for route in app.routes
            if hasattr(route, 'path')
        ],
        "environment": settings.environment,
        "google_api_configured": settings.is_configured(),
        "langsmith_enabled": settings.langchain_tracing_v2,
        "version": "2.0.0",
        "vercel": bool(os.getenv("VERCEL"))
    }


@app.post("/extract-job-details", response_model=JobDetailsResponse)
async def extract_job_details(request: JobExtractionRequest):
    """
    Extrai detalhes da vaga (título, empresa, descrição) a partir da URL.
    
    BUG FIX: Agora usa JobExtractionRequest que não requer CV, resolvendo HTTP 422.
    
    Args:
        request: Requisição com URL da vaga (apenas job_url necessário)
        
    Returns:
        Detalhes da vaga extraídos e validados
        
    Raises:
        HTTPException: Se extração ou validação falhar
    """
    # Verifica se a aplicação está configurada
    if not settings.is_configured() or extraction_agent is None:
        logger.error("Tentativa de usar API sem GOOGLE_API_KEY configurada")
        raise HTTPException(
            status_code=503,
            detail={
                "error": "Serviço não configurado",
                "message": "GOOGLE_API_KEY não está configurada no servidor",
                "instructions": [
                    "Administrador: Configure a variável de ambiente GOOGLE_API_KEY",
                    "Obtenha a chave em: https://aistudio.google.com/app/apikey",
                    "Execute: vercel env add GOOGLE_API_KEY"
                ]
            }
        )
    
    try:
        logger.info("Extraindo detalhes da vaga", url=request.job_url)
        
        # Extrai conteúdo da vaga
        content_result = await extraction_agent.extract_job_content_from_url(
            request.job_url
        )
        
        # Extrai título e empresa
        details_result = await extraction_agent.extract_job_title_and_company(
            content_result["content"],
            request.job_url
        )
        
        # BUG FIX: Os agentes retornam snake_case, não camelCase
        content_validation = content_result.get("validation", {})
        content_score = content_validation.get("score", 0) if isinstance(content_validation, dict) else 0
        
        return JobDetailsResponse(
            job_title=details_result["job_title"],  # snake_case correto
            company=details_result["company"],
            job_description=content_result["content"],
            validation={
                "content": content_result["validation"],
                "details": details_result["validation"]
            },
            source=f"{content_result['source']} + {details_result['source']}",
            content_score=content_score
        )
        
    except ValueError as e:
        logger.warning("Erro na extração", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Erro inesperado na extração", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao extrair detalhes da vaga: {str(e)}"
        )


@app.post("/generate-materials", response_model=GeneratedContentResponse)
async def generate_materials(request: GenerateMaterialsRequest):
    """
    Gera materiais de carreira personalizados.
    
    Args:
        request: Requisição com dados para geração
        
    Returns:
        Materiais gerados (CV otimizado, carta, networking, dicas)
        
    Raises:
        HTTPException: Se geração falhar
    """
    # Verifica se a aplicação está configurada
    if not settings.is_configured() or generation_agent is None:
        logger.error("Tentativa de usar API sem GOOGLE_API_KEY configurada")
        raise HTTPException(
            status_code=503,
            detail={
                "error": "Serviço não configurado",
                "message": "GOOGLE_API_KEY não está configurada no servidor",
                "instructions": [
                    "Administrador: Configure a variável de ambiente GOOGLE_API_KEY",
                    "Obtenha a chave em: https://aistudio.google.com/app/apikey",
                    "Execute: vercel env add GOOGLE_API_KEY"
                ]
            }
        )
    
    try:
        logger.info(
            "Gerando materiais",
            job_title=request.job_title,
            company=request.company,
            use_thinking_mode=request.use_thinking_mode
        )
        
        # Cria agente de geração com configuração apropriada
        agent = GenerationAgent(use_thinking_mode=request.use_thinking_mode)
        
        result = await agent.generate_career_materials(
            cv=request.cv,
            job_title=request.job_title,
            company=request.company,
            job_description=request.job_description,
            tone=request.tone,
            language=request.language,
            custom_context=request.custom_context
        )

        compatibility = result.get("compatibility") or {
            "score": 0,
            "label": "Compatibilidade indisponível",
            "strengths": [],
            "gaps": [],
            "coverage_ratio": 0.0,
        }
        
        return GeneratedContentResponse(
            optimized_cv=result["optimizedCv"],
            cover_letter=result["coverLetter"],
            networking_message=result["networkingMessage"],
            interview_tips=result["interviewTips"],
            sources=result.get("sources", []),
            compatibility=compatibility,
            metadata=result.get("metadata", {})
        )
        
    except ValueError as e:
        logger.warning("Erro na geração", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Erro inesperado na geração", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao gerar materiais: {str(e)}"
        )


@app.post("/generate-complete")
async def generate_complete(request: UserInputRequest):
    """
    Endpoint completo que extrai detalhes da vaga e gera materiais em uma única chamada.
    Útil para simplificar integração no frontend.
    
    Args:
        request: Requisição completa com URL da vaga e CV
        
    Returns:
        Dicionário com detalhes da vaga e materiais gerados
    """
    try:
        logger.info("Processamento completo iniciado", url=request.job_url)
        
        # Passo 1: Extrair detalhes da vaga
        content_result = await extraction_agent.extract_job_content_from_url(
            request.job_url
        )
        
        details_result = await extraction_agent.extract_job_title_and_company(
            content_result["content"],
            request.job_url
        )
        job_title = details_result.get("job_title") or details_result.get("jobTitle")
        company = details_result.get("company")

        if not job_title or not company:
            raise ValueError("Falha ao extrair título ou empresa da vaga")
        
        # Passo 2: Gerar materiais
        agent = GenerationAgent()
        materials_result = await agent.generate_career_materials(
            cv=request.cv,
            job_title=job_title,
            company=company,
            job_description=content_result["content"],
            tone=request.tone,
            language=request.language,
            custom_context=request.custom_context
        )

        compatibility = materials_result.get("compatibility") or {
            "score": 0,
            "label": "Compatibilidade indisponível",
            "strengths": [],
            "gaps": [],
            "coverage_ratio": 0.0,
        }
        
        return {
            "jobDetails": {
                "jobTitle": job_title,
                "company": company,
                "jobDescription": content_result["content"],
                "validation": {
                    "content": content_result["validation"],
                    "details": details_result["validation"]
                }
            },
            "materials": {
                "optimizedCv": materials_result["optimizedCv"],
                "coverLetter": materials_result["coverLetter"],
                "networkingMessage": materials_result["networkingMessage"],
                "interviewTips": materials_result["interviewTips"],
                "sources": materials_result.get("sources", []),
                "compatibility": compatibility,
                "metadata": materials_result.get("metadata", {})
            }
        }
        
    except ValueError as e:
        logger.warning("Erro no processamento completo", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Erro inesperado no processamento completo", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Erro no processamento: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.environment == "development"
    )

