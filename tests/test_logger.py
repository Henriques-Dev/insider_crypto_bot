import sys
import os
from logger import setup_logger

# Configura o logger com o nível definido no settings.py
logger = setup_logger()

# Testa os diferentes níveis de log
logger.debug("Esta é uma mensagem de DEBUG")
logger.info("Esta é uma mensagem de INFO")
logger.warning("Esta é uma mensagem de WARNING")
logger.alert("Esta é uma mensagem de ALERT")
logger.error("Esta é uma mensagem de ERROR")
logger.critical("Esta é uma mensagem de CRITICAL")

# Teste com exceções (opcional)
try:
    1 / 0  # Gera uma exceção
except ZeroDivisionError as e:
    logger.error(f"Erro ao dividir por zero: {e}", exc_info=True)