"""
Agente de geração usando LangChain para criar materiais de carreira personalizados.
Implementa geração estruturada com validação de qualidade.
"""
from typing import Dict, Any
import re
import structlog
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langsmith import traceable

import sys
from pathlib import Path

# Adiciona o diretório raiz ao path para imports absolutos
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.base_agent import BaseAgent
from agents.prompts import PromptTemplates, get_prompt_variables
from config import settings
from utils.compatibility import calculate_compatibility

logger = structlog.get_logger()


class GenerationAgent(BaseAgent):
    """
    Agente especializado em geração de materiais de carreira personalizados.
    Usa prompts profissionais e validação de qualidade.
    """
    
    def __init__(
        self,
        model_name: str = "gemini-2.5-flash",
        use_thinking_mode: bool = False
    ):
        """
        Inicializa o agente de geração.
        
        Args:
            model_name: Modelo LLM a ser usado (gemini-2.5-flash ou gemini-2.5-pro)
            use_thinking_mode: Se deve usar modo de raciocínio (mais lento, mais preciso)
        """
        # Ajusta modelo baseado no modo de raciocínio
        if use_thinking_mode:
            model_name = "gemini-2.5-pro"
        
        super().__init__(model_name=model_name)
        self.use_thinking_mode = use_thinking_mode
        self._chain = None
    
    def _create_chain(self):
        """Cria a cadeia LangChain para geração."""
        if self._chain is None:
            # Configuração do modelo com ferramentas
            config = {}
            
            if self.use_thinking_mode:
                # Modo de raciocínio para maior precisão
                config["thinking_config"] = {"thinking_budget": 32768}
            
            # Habilita Google Search para contexto adicional
            config["tools"] = [{"googleSearch": {}}]
            
            llm = ChatGoogleGenerativeAI(
                model=self.model_name,
                google_api_key=settings.google_api_key,
                temperature=0.7,  # Temperatura média para criatividade controlada
                **config
            )
            
            prompt = PromptTemplates.get_career_materials_generation_prompt()
            parser = StrOutputParser()
            
            self._chain = prompt | llm | parser
        
        return self._chain
    
    @traceable(name="generate_career_materials")
    async def generate_career_materials(
        self,
        cv: str,
        job_title: str,
        company: str,
        job_description: str,
        tone: str = "Profissional mas entusiasmado",
        language: str = "Português Brasileiro",
        custom_context: str = ""
    ) -> Dict[str, Any]:
        """
        Gera materiais de carreira personalizados.
        
        Args:
            cv: Currículo do usuário
            job_title: Título da vaga
            company: Nome da empresa
            job_description: Descrição da vaga
            tone: Tom desejado
            language: Idioma alvo
            custom_context: Contexto adicional do usuário
            
        Returns:
            Dicionário com materiais gerados e metadados
        """
        self.logger.info(
            "Gerando materiais de carreira",
            job_title=job_title,
            company=company,
            model=self.model_name
        )
        
        # Validação de entrada
        if not cv or len(cv.strip()) < 50:
            raise ValueError("CV muito curto ou vazio")
        
        if not job_title or not company:
            raise ValueError("Título da vaga e empresa são obrigatórios")
        
        if not job_description or len(job_description.strip()) < 100:
            raise ValueError("Descrição da vaga muito curta ou vazia")
        
        # Prepara variáveis do prompt
        prompt_vars = get_prompt_variables(
            cv=cv,
            job_title=job_title,
            company=company,
            job_description=job_description,
            tone=tone,
            language=language,
            custom_context=custom_context
        )
        
        compatibility = calculate_compatibility(cv, job_description)

        try:
            # Executa a cadeia
            chain = self._create_chain()
            raw_response = await chain.ainvoke(prompt_vars)
            
            # Parseia a resposta estruturada
            parsed_content = self._parse_generated_content(raw_response)
            
            # Extrai fontes (grounding metadata) se disponível
            sources = self._extract_sources(raw_response)
            
            self.logger.info(
                "Materiais gerados com sucesso",
                sections=list(parsed_content.keys())
            )
            
            return {
                **parsed_content,
                "sources": sources,
                "compatibility": {
                    "score": compatibility.score,
                    "label": compatibility.label,
                    "strengths": compatibility.strengths,
                    "gaps": compatibility.gaps,
                    "coverage_ratio": compatibility.coverage_ratio,
                },
                "metadata": {
                    "model": self.model_name,
                    "use_thinking_mode": self.use_thinking_mode,
                    "tone": tone,
                    "language": language
                }
            }
            
        except Exception as e:
            self.logger.error("Erro na geração de materiais", error=str(e))
            raise ValueError(f"Falha ao gerar materiais: {e}") from e
    
    def _parse_generated_content(self, response_text: str) -> Dict[str, str]:
        """
        Parseia a resposta estruturada do LLM em seções.
        
        Args:
            response_text: Texto completo da resposta
            
        Returns:
            Dicionário com seções parseadas
        """
        sections = {
            "optimizedCv": "### OPTIMIZED CV ###",
            "coverLetter": "### COVER LETTER ###",
            "networkingMessage": "### NETWORKING MESSAGE ###",
            "interviewTips": "### INTERVIEW TIPS ###",
        }
        
        parsed_content = {}
        remaining_text = response_text
        
        keys = list(sections.keys())
        for i, key in enumerate(keys):
            start_marker = sections[key]
            next_key = keys[i + 1] if i + 1 < len(keys) else None
            end_marker = sections[next_key] if next_key else None
            
            start_index = remaining_text.find(start_marker)
            if start_index == -1:
                parsed_content[key] = f"Erro: Seção {start_marker} não encontrada"
                continue
            
            end_index = (
                remaining_text.find(end_marker, start_index)
                if end_marker
                else len(remaining_text)
            )
            
            if end_index == -1:
                end_index = len(remaining_text)
            
            section_text = remaining_text[
                start_index + len(start_marker):end_index
            ].strip()
            
            parsed_content[key] = section_text
        
        return parsed_content
    
    def _extract_sources(self, response_text: str) -> list:
        """
        Extrai fontes (grounding metadata) da resposta.
        Por enquanto retorna lista vazia, mas pode ser expandido
        para extrair URLs de fontes pesquisadas.
        
        Args:
            response_text: Texto da resposta
            
        Returns:
            Lista de fontes (dicionários com uri e title)
        """
        # TODO: Implementar extração de fontes do grounding metadata
        # quando disponível na resposta do LangChain
        return []

