# tests/test_logger.py
import sys
import os

# Adiciona o diretório raiz ao Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importa o logger configurado
from logger.log_config import setup_logger, get_logger

# Configura o logger
logger = setup_logger(log_level="INFO")

# Testa os diferentes níveis de log
logger.debug("Esta é uma mensagem de DEBUG")  # Não deve aparecer (nível INFO)
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