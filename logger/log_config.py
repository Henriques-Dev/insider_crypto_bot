"""
Módulo de configuração de loggin para o Insider Crypto Bot

Implementa um sistema de loggin personalizado ocm níveis especificos, formatação colorida, 
roteamento para múltiplos handlers e tratamentos de alertas especializados.

Caracteriscitas Principais:
- Níveis customizados (INFO, ALERT, WARNING, ERROR, CRITICAL)
- Saída colorida para console
- Rotação diária de arquivos de log
- Arquivo separado para alertas críticos
- Formação consistente para análise automatizada
"""

import logging
import sys
import os
from pathlib import Path
from logging.handlers import TimedRotatingFileHandler
from config.settings import LOG_CONFIG
from typing import Optional

# Definindo nível customizado para ALERT
ALERT_LEVEL = 35
logging.addLevelName(ALERT_LEVEL, "ALERT")

class CustomLogger(logging.getLoggerClass()):
    """Logger customizado com método para alertas críticos"""

    def alert(self, msg: str, *args, **kwargs) -> None:
        """Registra um alerta crítico na operação do sistema"""
        if self.isEnabledFor(ALERT_LEVEL):
            self._log(ALERT_LEVEL, msg, args, **kwargs)

class ColorFormatter(logging.Formatter):
    """Formatador de log com saída colorida para console"""

    COLORS = {
        logging.DEBUG: "\033[36m",              # Azul
        logging.INFO: "\033[32m",               # Verde
        logging.WARNING: "\033[33m",            # Amarelo
        logging.ERROR: "\033[31m",              # Vermelho
        logging.CRITICAL: "\033[31;1m",         # Vermelho Intensivo
        ALERT_LEVEL: "\033[35;1m",              # Magenta Intensivo
    }
    RESET = "\033[0m"

    def format(self, record) -> str:
        """Aplica formatação colorida baseada no nivel do log"""
        color = self.COLORS.get(record.levelno, self.RESET)
        fmt = f"{color}{self._fmt}{self.RESET}"
        return logging.Formatter(fmt, self.datefmt).format(record)
    
def setup_logger(
    name: str = "InsiderCrypto",
    log_level: Optional[str] = None,
    log_dir: Optional[str] = None,
    alert_log: Optional[str] = None
) -> logging.Logger:
    """
    Configura o sistema de logging com handlers para console e arquivos.
    """
    # Configurar diretório de logs
    log_dir = log_dir or LOG_CONFIG["LOG_DIR"]
    Path(log_dir).mkdir(exist_ok=True)

    # Registrar logger customizado
    logging.setLoggerClass(CustomLogger)
    logger = logging.getLogger(name)

    # Define o nível de log
    log_level = log_level or LOG_CONFIG["LOG_LEVEL"]
    level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(level)

    # Log de depuração para verificar o nível de log
    logger.debug(f"Nível de log configurado: {log_level} ({level})")

    # Evitar registros duplicados
    if logger.handlers:
        return logger
    
    # Formatação padrão
    base_fmt = "%(asctime)s | %(name)s | %(levelname)s | %(module)s:%(lineno)d - %(message)s"
    date_fmt = "%Y-%m-%d %H:%M:%S"

    ## Handler para console com cores
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(ColorFormatter(base_fmt, date_fmt))
    console_handler.setLevel(level)  # Define o mesmo nível do logger

    # Handler para arquivo principal com rotação diária
    main_handler = TimedRotatingFileHandler(
        filename=os.path.join(log_dir, "main.log"),
        when="midnight",
        backupCount=7,
        encoding="utf-8"
    )
    main_handler.setFormatter(logging.Formatter(base_fmt, date_fmt))
    main_handler.setLevel(level)  # Define o mesmo nível do logger

    # Handler especial para alertas
    alert_log = alert_log or LOG_CONFIG["ALERT_LOG"]
    alert_handler = logging.FileHandler(
        filename=os.path.join(log_dir, alert_log),
        mode="a",
        encoding="utf-8"
    )
    alert_handler.setLevel(ALERT_LEVEL)  # Mantém o nível ALERT para este handler
    alert_handler.setFormatter(logging.Formatter(base_fmt, date_fmt))

    # Adicionar handlers ao logger
    logger.addHandler(console_handler)
    logger.addHandler(main_handler)
    logger.addHandler(alert_handler)

    return logger

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Retorna um logger configurado apropriadamente"""
    return logging.getLogger(name or "InsiderCrypto")

# Exemplo de uso
if __name__ == "__main__":
    logger = setup_logger()
    logger.info("Sistema de logging inicializado com sucesso!")
    logger.error("ALERTA: Teste de alerta crítico")
    logger.warning("Aviso: Teste de mensagem de aviso")