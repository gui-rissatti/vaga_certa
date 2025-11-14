"""
Classe base para todos os agentes, fornecendo funcionalidades comuns
como logging, retry, e integração com LangSmith.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import structlog
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    RetryError
)
from langchain_core.runnables import Runnable
from langchain_core.callbacks import CallbackManager
from langsmith import traceable

logger = structlog.get_logger()


class BaseAgent(ABC):
    """
    Classe base abstrata para todos os agentes de IA.
    Fornece funcionalidades comuns de logging, retry e observabilidade.
    """
    
    def __init__(
        self,
        model_name: str = "gemini-2.5-flash",
        max_retries: int = 3,
        timeout_seconds: int = 300
    ):
        """
        Inicializa o agente base.
        
        Args:
            model_name: Nome do modelo LLM a ser usado
            max_retries: Número máximo de tentativas em caso de falha
            timeout_seconds: Timeout em segundos para operações
        """
        self.model_name = model_name
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds
        self.logger = logger.bind(agent=self.__class__.__name__)
    
    @abstractmethod
    def _create_chain(self) -> Runnable:
        """Cria a cadeia LangChain específica do agente."""
        pass
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        reraise=True
    )
    @traceable(name="agent_execution")
    async def execute(
        self,
        input_data: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Executa o agente com retry automático e observabilidade.
        
        Args:
            input_data: Dados de entrada para o agente
            **kwargs: Argumentos adicionais específicos do agente
            
        Returns:
            Resultado da execução do agente
            
        Raises:
            RetryError: Se todas as tentativas falharem
        """
        self.logger.info(
            "Executando agente",
            model=self.model_name,
            input_keys=list(input_data.keys())
        )
        
        try:
            chain = self._create_chain()
            result = await chain.ainvoke(input_data)
            
            self.logger.info(
                "Agente executado com sucesso",
                model=self.model_name
            )
            
            return result
            
        except Exception as e:
            self.logger.error(
                "Erro na execução do agente",
                error=str(e),
                error_type=type(e).__name__
            )
            raise
    
    def _log_operation(
        self,
        operation: str,
        success: bool,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Registra uma operação para observabilidade."""
        log_data = {
            "operation": operation,
            "success": success,
            "agent": self.__class__.__name__,
            "model": self.model_name
        }
        
        if metadata:
            log_data.update(metadata)
        
        if success:
            self.logger.info("Operação concluída", **log_data)
        else:
            self.logger.warning("Operação falhou", **log_data)

