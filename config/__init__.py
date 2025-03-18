"""
Pacote config do Insider Crypto Bot.

Este pacote centraliza todas as configurações do projeto, incluindo chaves de API,
configurações de logging, parâmetros de mercado e URLs de APIs.
"""

from .settings import settings

# Expõe a instância de configurações
__all__ = ["settings"]