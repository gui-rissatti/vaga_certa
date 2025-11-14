"""
Agente de extração usando LangChain para extrair informações de vagas.
Implementa validação multi-camada e confidence scoring.
"""
from typing import Dict, Any, Optional
import json
import structlog
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langsmith import traceable

import sys
from pathlib import Path

# Adiciona o diretório raiz ao path para imports absolutos
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.base_agent import BaseAgent
from agents.prompts import PromptTemplates
from config import settings
from services.web_scraper import WebScraper
from utils.validation import ValidationResult, validate_and_score_job_content, validate_and_score_job_details

logger = structlog.get_logger()


class ExtractionAgent(BaseAgent):
    """
    Agente especializado em extração de informações de vagas de emprego.
    Combina web scraping com LLM para validação e refinamento.
    """
    
    def __init__(
        self,
        model_name: str = "gemini-2.5-flash",
        use_web_scraping: bool = True
    ):
        """
        Inicializa o agente de extração.
        
        Args:
            model_name: Modelo LLM a ser usado
            use_web_scraping: Se deve usar web scraping antes do LLM
        """
        super().__init__(model_name=model_name)
        self.use_web_scraping = use_web_scraping
        self.web_scraper = WebScraper() if use_web_scraping else None
        self._chain = None
    
    def _create_chain(self):
        """Cria a cadeia LangChain para extração."""
        if self._chain is None:
            llm = ChatGoogleGenerativeAI(
                model=self.model_name,
                google_api_key=settings.google_api_key,
                temperature=0.1,  # Baixa temperatura para extração precisa
            )
            
            prompt = PromptTemplates.get_job_content_extraction_prompt()
            parser = StrOutputParser()
            
            self._chain = prompt | llm | parser
        
        return self._chain
    
    @traceable(name="extract_job_content")
    async def extract_job_content_from_url(
        self,
        job_url: str
    ) -> Dict[str, Any]:
        """
        Extrai conteúdo de uma vaga a partir de uma URL.
        
        Args:
            job_url: URL da vaga de emprego
            
        Returns:
            Dicionário com conteúdo extraído e metadados de validação
            
        Raises:
            ValueError: Se a URL for inválida ou extração falhar
        """
        self.logger.info("Iniciando extração de conteúdo", url=job_url)
        
        # Validação básica da URL
        try:
            from urllib.parse import urlparse
            parsed = urlparse(job_url)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError(f"URL inválida: {job_url}")
        except Exception as e:
            raise ValueError(f"URL inválida: {job_url}") from e
        
        # Tentativa 1: Web scraping direto (mais rápido e confiável)
        if self.use_web_scraping and self.web_scraper:
            try:
                scraped_data = await self.web_scraper.scrape_job_posting(job_url)
                
                # Validação com scoring
                validation = validate_and_score_job_content(scraped_data["fullText"])
                
                if validation.is_valid:
                    self.logger.info(
                        "Extração via web scraping bem-sucedida",
                        score=validation.score,
                        url=job_url
                    )
                    return {
                        "content": scraped_data["fullText"],
                        "title": scraped_data.get("title", ""),
                        "company": scraped_data.get("company", ""),
                        "validation": {
                            "is_valid": True,
                            "score": validation.score,
                            "reasons": validation.reasons
                        },
                        "source": "web_scraping"
                    }
                else:
                    self.logger.warning(
                        "Web scraping retornou conteúdo de baixa qualidade - acionando fallback de IA",
                        score=validation.score,
                        reasons=validation.reasons
                    )
                    # Continua para tentar com LLM como fallback
                    
            except Exception as e:
                self.logger.warning(
                    "Web scraping falhou - acionando fallback de IA para extração de conteúdo",
                    error=str(e),
                    error_type=type(e).__name__
                )
        
        # Tentativa 2 (Fallback): LLM tenta acessar e extrair conteúdo da URL
        try:
            self.logger.info(
                "Iniciando extração de conteúdo via IA (fallback)",
                url=job_url
            )
            
            llm = ChatGoogleGenerativeAI(
                model=self.model_name,
                google_api_key=settings.google_api_key,
                temperature=0.1,
            )
            
            # Prompt para o LLM extrair conteúdo da URL
            fallback_prompt = f"""Você precisa extrair o conteúdo completo de uma vaga de emprego da seguinte URL:

URL: {job_url}

IMPORTANTE: Esta URL pode estar protegida contra web scraping. Tente acessar e extrair:
1. Título da vaga
2. Nome da empresa
3. Descrição completa da vaga
4. Requisitos
5. Benefícios
6. Qualquer outra informação relevante

Se não conseguir acessar a URL diretamente, explique o que impede o acesso.

Retorne o conteúdo extraído em formato de texto estruturado."""

            response = await llm.ainvoke(fallback_prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Valida o conteúdo extraído pela IA
            validation = validate_and_score_job_content(content)
            
            if not validation.is_valid:
                error_msg = (
                    f"IA não conseguiu extrair conteúdo válido da URL: {job_url}\n"
                    f"Score: {validation.score}/100 (mínimo: 70)\n"
                    f"Motivos: {', '.join(validation.reasons)}\n\n"
                    f"A URL pode estar protegida ou o conteúdo pode não estar acessível.\n"
                    f"Sugestões:\n"
                    f"1. Abra a URL no navegador e copie o conteúdo manualmente\n"
                    f"2. Tente uma URL diferente da mesma vaga\n"
                    f"3. Verifique se a vaga ainda está disponível"
                )
                self.logger.error(
                    "Fallback de IA falhou - conteúdo inválido",
                    score=validation.score,
                    reasons=validation.reasons
                )
                raise ValueError(error_msg)
            
            self.logger.info(
                "Conteúdo extraído via IA com sucesso (fallback)",
                score=validation.score,
                source="llm_fallback"
            )
            
            return {
                "content": content,
                "title": "",  # Será extraído em outra etapa
                "company": "",  # Será extraído em outra etapa
                "validation": {
                    "is_valid": True,
                    "score": validation.score,
                    "reasons": validation.reasons
                },
                "source": "llm_fallback"
            }
            
        except Exception as e:
            error_msg = (
                f"Falha completa ao extrair conteúdo da URL: {job_url}\n\n"
                f"Tentativas realizadas:\n"
                f"1. ✗ Web scraping direto\n"
                f"2. ✗ Extração via IA\n\n"
                f"Erro: {str(e)}\n\n"
                f"Ações sugeridas:\n"
                f"• Cole o conteúdo da vaga manualmente\n"
                f"• Verifique se a URL está correta e acessível\n"
                f"• Tente novamente em alguns minutos"
            )
            self.logger.error(
                "Extração de conteúdo falhou completamente",
                error=error_msg,
                error_type=type(e).__name__
            )
            raise ValueError(error_msg) from e
    
    @traceable(name="extract_job_details")
    async def extract_job_title_and_company(
        self,
        job_content: str,
        job_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extrai título e empresa da vaga a partir do conteúdo.
        
        Args:
            job_content: Conteúdo da vaga já extraído
            job_url: URL da vaga (opcional, usado para web scraping)
            
        Returns:
            Dicionário com título, empresa e metadados de validação
            
        Raises:
            ValueError: Se extração ou validação falhar
        """
        self.logger.info("Extraindo título e empresa")
        
        if not job_content or len(job_content.strip()) < 100:
            raise ValueError("Conteúdo da vaga muito curto ou vazio")
        
        # Tentativa 1: Web scraping se URL disponível
        parsing_succeeded = False
        if job_url and self.use_web_scraping and self.web_scraper:
            try:
                scraped_data = await self.web_scraper.scrape_job_posting(job_url)
                
                if scraped_data.get("title") and scraped_data.get("company"):
                    title = scraped_data["title"].strip()
                    company = scraped_data["company"].strip()
                    
                    # Validação rigorosa
                    validation = validate_and_score_job_details(title, company)
                    
                    if validation.is_valid:
                        self.logger.info(
                            "Título e empresa extraídos via web scraping",
                            title=title,
                            company=company,
                            score=validation.score
                        )
                        # BUG FIX: Retorna snake_case para consistência Python
                        return {
                            "job_title": title,  # snake_case correto
                            "company": company,
                            "validation": {
                                "is_valid": True,
                                "score": validation.score,
                                "reasons": validation.reasons
                            },
                            "source": "web_scraping"
                        }
                    else:
                        # Parsing encontrou dados mas validação falhou
                        self.logger.warning(
                            "Web scraping extraiu dados inválidos - acionando fallback de IA",
                            title=title,
                            company=company,
                            score=validation.score,
                            reasons=validation.reasons
                        )
                else:
                    # Parsing não encontrou título ou empresa
                    self.logger.warning(
                        "Web scraping não localizou título/empresa - acionando fallback de IA",
                        has_title=bool(scraped_data.get("title")),
                        has_company=bool(scraped_data.get("company"))
                    )
            except Exception as e:
                self.logger.warning(
                    "Web scraping falhou - acionando fallback de IA",
                    error=str(e),
                    error_type=type(e).__name__
                )
        else:
            self.logger.info("Web scraping desabilitado ou URL não fornecida - usando IA diretamente")
        
        # Tentativa 2 (ou Fallback): LLM com parsing estruturado
        try:
            self.logger.info(
                "Iniciando extração via IA",
                fallback_mode=job_url is not None and self.use_web_scraping
            )
            
            llm = ChatGoogleGenerativeAI(
                model=self.model_name,
                google_api_key=settings.google_api_key,
                temperature=0.1,
            )
            
            prompt = PromptTemplates.get_job_details_extraction_prompt()
            parser = JsonOutputParser(pydantic_object=None)  # Aceita qualquer JSON válido
            
            chain = prompt | llm | parser
            
            result = await chain.ainvoke({"content": job_content})
            
            # Extrai valores do resultado (aceita camelCase e snake_case)
            if isinstance(result, dict):
                title = result.get("jobTitle", result.get("job_title", "")).strip()
                company = result.get("company", "").strip()
            else:
                # Tenta parsear se for string JSON
                parsed = json.loads(result) if isinstance(result, str) else {}
                title = parsed.get("jobTitle", parsed.get("job_title", "")).strip()
                company = parsed.get("company", "").strip()
            
            # Validação rigorosa
            validation = validate_and_score_job_details(title, company)
            
            if not validation.is_valid:
                error_msg = (
                    f"IA não conseguiu extrair dados válidos.\n"
                    f"Score: {validation.score}/100 (mínimo: 90)\n"
                    f"Motivos: {', '.join(validation.reasons)}\n"
                    f"Título extraído: '{title}'\n"
                    f"Empresa extraída: '{company}'"
                )
                self.logger.error("Validação da IA falhou", **{
                    "score": validation.score,
                    "title": title,
                    "company": company,
                    "reasons": validation.reasons
                })
                raise ValueError(error_msg)
            
            source = "llm_fallback" if job_url and self.use_web_scraping else "llm"
            
            self.logger.info(
                "Título e empresa extraídos via IA com sucesso",
                title=title,
                company=company,
                score=validation.score,
                source=source
            )
            
            # BUG FIX: Sempre retorna snake_case para consistência Python
            return {
                "job_title": title,  # snake_case correto
                "company": company,
                "validation": {
                    "is_valid": True,
                    "score": validation.score,
                    "reasons": validation.reasons
                },
                "source": source
            }
            
        except json.JSONDecodeError as e:
            error_msg = f"IA retornou JSON inválido: {str(e)}"
            self.logger.error("Erro de parsing JSON", error=error_msg)
            raise ValueError(error_msg) from e
        except Exception as e:
            error_msg = f"Falha crítica na extração de título/empresa: {str(e)}"
            self.logger.error("Extração falhou completamente", error=error_msg, error_type=type(e).__name__)
            raise ValueError(error_msg) from e

