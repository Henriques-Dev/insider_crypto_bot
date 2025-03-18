"""
Pacote logger do Insider Crypto Bot.

Este pacote fornece um sistema de logging personalizado com suporte a níveis customizados,
formatação colorida, rotação de arquivos de log e tratamento de alertas especializados.

Funcionalidades principais:
- setup_logger: Configura o logger com handlers para console e arquivos.
- get_logger: Retorna um logger configurado apropriadamente.
- Níveis customizados: INFO, ALERT, WARNING, ERROR, CRITICAL.
"""

# Expõe as funções e classes principais do módulo log_config
from .log_config import (
    setup_logger,
    get_logger,
    CustomLogger,
    ColorFormatter,
    ALERT_LEVEL,
)

# Define o que será importado quando alguém fizer `from logger import *`
__all__ = [
    "setup_logger",
    "get_logger",
    "CustomLogger",
    "ColorFormatter",
    "ALERT_LEVEL",
]

# Configuração inicial do logger (opcional)
# Aqui você pode configurar um logger padrão para o pacote, se necessário.
# Por exemplo:
# import logging
# logging.basicConfig(level=logging.INFO)