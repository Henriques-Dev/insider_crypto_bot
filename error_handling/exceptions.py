"""
Módulo de tratamento de erros personalizados para o Meme Coin Monitor.

Contém exceções hierárquicas e utilitários para captura e registro consistente de erros,
com suporte a encadeamento de exceções e enriquecimento de informações de contexto.
"""

from typing import Callable, Any, Optional, Type
from functools import wraps
import logging  # Importando o módulo de logging para uso posterior

class InsiderCryptoError(Exception):
    """
    Classe base para todas as exceções personalizadas do projeto.
    
    Atributos:
        message (str): Mensagem descritiva do erro.
        details (Optional[str]): Detalhes técnicos adicionais.
        cause (Optional[Exception]): Exceção original que causou o erro.
    """
    def __init__(
        self,
        message: str,
        details: Optional[str] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(message)
        self.details = details
        self.cause = cause
        self.error_type = self.__class__.__name__
        if cause:
            self.__cause__ = cause  # Suporte oficial ao encadeamento de exceções

    def __str__(self) -> str:
        base = f"[{self.error_type}] {super().__str__()}"
        details = f" | Detalhes: {self.details}" if self.details else ""
        cause = f" | Causa: {self.cause}" if self.cause else ""
        return f"{base}{details}{cause}"

# ----------------------------------------------------------
# Exceções Específicas do Domínio
# ----------------------------------------------------------

class APIConnectionError(InsiderCryptoError):
    """
    Erro de conexão com APIs externas.
    
    Atributos:
        url (Optional[str]): Endpoint da API que causou o erro.
        status_code (Optional[int]): Código HTTP retornado.
    """
    def __init__(
        self,
        message: str,
        url: Optional[str] = None,
        status_code: Optional[int] = None,
        details: Optional[str] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(
            message=f"{message} (URL: {url})" if url else message,
            details=details,
            cause=cause
        )
        self.url = url
        self.status_code = status_code

class DataValidationError(InsiderCryptoError):
    """
    Erro de validação de dados recebidos.
    
    Atributos:
        field (Optional[str]): Campo que falhou na validação.
        value (Optional[Any]): Valor inválido recebido.
    """
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        context: Optional[dict] = None,
        details: Optional[str] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(
            message=f"{message} (Campo: {field})" if field else message,
            details=details,
            cause=cause
        )
        self.field = field
        self.value = value
        self.context = context 

class TradingStrategyError(InsiderCryptoError):
    """
    Erro em estratégias de trading.
    
    Atributos:
        strategy (str): Nome da estratégia que falhou.
        parameters (dict): Parâmetros usados na estratégia.
    """
    def __init__(
        self,
        message: str,
        strategy: str,
        parameters: Optional[dict] = None,
        details: Optional[str] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(
            message=f"{message} (Estratégia: {strategy})",
            details=details,
            cause=cause
        )
        self.strategy = strategy
        self.parameters = parameters or {}

class ConfigurationError(InsiderCryptoError):
    """
    Erro de configuração do sistema.
    
    Atributos:
        config_key (str): Chave de configuração problemática.
        expected_type (Type): Tipo esperado para o valor.
        actual_value (Any): Valor recebido.
    """
    def __init__(
        self,
        message: str,
        config_key: str,
        expected_type: Optional[Type] = None,
        actual_value: Optional[Any] = None,
        details: Optional[str] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(
            message=f"{message} (Config: {config_key})",
            details=details,
            cause=cause
        )
        self.config_key = config_key
        self.expected_type = expected_type
        self.actual_value = actual_value

class ProcessingError(InsiderCryptoError):
    """
    Erro durante processamento de dados ou análises.
    
    Atributos:
        component (Optional[str]): Módulo ou componente onde ocorreu o erro.
        input_data (Optional[Any]): Dados que estavam sendo processados.
        operation (Optional[str]): Tipo de operação sendo executada.
    """
    def __init__(
        self,
        message: str,
        component: Optional[str] = None,
        input_data: Optional[Any] = None,
        operation: Optional[str] = None,
        details: Optional[str] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(
            message=f"{message} (Componente: {component}, Dados: {input_data})" if component else message,
            details=details,
            cause=cause
        )
        self.component = component
        self.input_data = input_data
        self.operation = operation

    def __str__(self) -> str:
        base = super().__str__()
        operation = f" | Operação: {self.operation}" if self.operation else ""
        return f"{base}{operation}"

class AnalysisError(InsiderCryptoError):
    """
    Erro durante análises de dados ou processamento de métricas complexas.
    
    Atributos:
        metric (str): Nome da métrica analisada.
        dataset (Optional[Any]): Conjunto de dados utilizado.
        algorithm (Optional[str]): Algoritmo/método de análise utilizado.
    """
    def __init__(
        self,
        message: str,
        metric: Optional[str] = None,
        dataset: Optional[Any] = None,
        algorithm: Optional[str] = None,
        details: Optional[str] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(
            message=f"{message} (Métrica: {metric}, Dataset: {dataset}, Algoritmo: {algorithm})" if metric else message,
            details=details,
            cause=cause
        )
        self.metric = metric
        self.dataset = dataset
        self.algorithm = algorithm

    def __str__(self) -> str:
        base = super().__str__()
        algorithm = f" | Algoritmo: {self.algorithm}" if self.algorithm else ""
        return f"{base}{algorithm}"
    
# ----------------------------------------------------------
# Utilitário de Tratamento de Erros
# ----------------------------------------------------------

def handle_errors(re_raise: bool = True, log_level: str = "error") -> Callable:
    """
    Decorador para tratamento centralizado de erros com opções configuráveis.
    
    Args:
        re_raise (bool): Se True, relança a exceção após o log.
        log_level (str): Nível de log para erros conhecidos (debug, info, warning, error, critical).
    
    Exemplo:
        @handle_errors(re_raise=False, log_level="warning")
        def funcao_arriscada():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            from logger import get_logger  # Importação tardia
            logger = get_logger()
             
            # Converte o log_level de string para o nível de log correspondente
            log_level_int = getattr(logging, log_level.upper(), logging.ERROR)
            
            try:
                return func(*args, **kwargs)
            except InsiderCryptoError as e:
                logger.log(
                    log_level_int,
                    f"Erro de negócio detectado: {e.error_type}",
                    extra={
                        "details": e.details,
                        "error_type": e.error_type,
                        "cause": str(e.cause) if e.cause else None
                    }
                )
                if re_raise:
                    raise
                return None
            except Exception as e:
                logger.critical(
                    "Erro crítico não tratado",
                    exc_info=True,
                    extra={
                        "error_type": e.__class__.__name__,
                        "exception": str(e)
                    }
                )
                if re_raise:
                    raise InsiderCryptoError(
                        "Erro não tratado detectado",
                        cause=e
                    ) from e
                return None
        return wrapper
    return decorator

# ----------------------------------------------------------
# Interface Pública do Módulo
# ----------------------------------------------------------
__all__ = [
    "InsiderCryptoError",
    "APIConnectionError",
    "DataValidationError",
    "TradingStrategyError",
    "ConfigurationError",
    "ProcessingError",
    "AnalysisError",
    "handle_errors"
]