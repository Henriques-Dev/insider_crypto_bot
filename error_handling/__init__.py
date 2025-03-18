"""
Pacote error_handling do Insider Crypto Bot.

Este pacote centraliza o tratamento de erros, incluindo exceções personalizadas
e utilitários para capturar e registrar erros de forma consistente.
"""

from .exceptions import (
    InsiderCryptoError,
    APIConnectionError,
    DataValidationError,
    TradingStrategyError,
    ConfigurationError,
    ProcessingError,
    AnalysisError,
    handle_errors
)

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