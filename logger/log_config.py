"""
Módulo de configuração de logging para o Insider Crypto Bot.

Implementa um sistema de logging personalizado com níveis específicos, formatação colorida,
roteamento para múltiplos handlers e tratamento de alertas especializados.

Características Principais:
- Níveis customizados (INFO, ALERT, WARNING, ERROR, CRITICAL)
- Saída colorida para console
- Rotação diária de arquivos de log
- Arquivo separado para alertas críticos
- Formatação consistente para análise automatizada
- Integração com exceções personalizadas do módulo exceptions.py
"""

import logging
import sys
import os
from pathlib import Path
from logging.handlers import TimedRotatingFileHandler
from config import settings
from typing import Optional, Dict, Any
from error_handling.exceptions import InsiderCryptoError

# Definindo nível customizado para ALERT
ALERT_LEVEL = 35
logging.addLevelName(ALERT_LEVEL, "ALERT")

class CustomLogger(logging.getLoggerClass()):
    """Logger customizado com método para alertas críticos e tratamento de exceções."""

    def alert(self, msg: str, *args, **kwargs) -> None:
        """
        Registra um alerta crítico na operação do sistema.

        Args:
            msg (str): Mensagem de alerta.
            *args: Argumentos adicionais para formatação da mensagem.
            **kwargs: Argumentos nomeados adicionais para formatação da mensagem.
        """
        if self.isEnabledFor(ALERT_LEVEL):
            self._log(ALERT_LEVEL, msg, args, **kwargs)

    def log_exception(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Registra uma exceção com detalhes contextuais.

        Args:
            error (Exception): A exceção a ser registrada.
            context (Optional[Dict[str, Any]]): Dicionário com informações contextuais adicionais.
        """
        if isinstance(error, InsiderCryptoError):
            self.error(
                f"[{error.error_type}] {str(error)}",
                extra={
                    "details": error.details,
                    "cause": str(error.cause) if error.cause else None,
                    "context": context
                }
            )
        else:
            self.critical(
                f"Erro não tratado: {str(error)}",
                exc_info=True,
                extra={"context": context}
            )

class ColorFormatter(logging.Formatter):
    """Formatador de log com saída colorida para console usando códigos ANSI."""

    COLORS = {
        logging.DEBUG: "\033[36m",      # Azul
        logging.INFO: "\033[32m",       # Verde
        logging.WARNING: "\033[33m",    # Amarelo
        logging.ERROR: "\033[31m",      # Vermelho
        logging.CRITICAL: "\033[31;1m", # Vermelho Intenso
        ALERT_LEVEL: "\033[35;1m",      # Magenta Intenso
    }
    RESET = "\033[0m"

    def __init__(self, fmt: Optional[str] = None, datefmt: Optional[str] = None):
        super().__init__(fmt, datefmt)
        self._fmt = fmt  # Mantém compatibilidade com sistemas que não suportam cores

    def format(self, record: logging.LogRecord) -> str:
        """
        Formata o registro de log aplicando cores baseadas no nível.

        Args:
            record (logging.LogRecord): Registro de log a ser formatado.

        Returns:
            str: Mensagem formatada com códigos ANSI.
        """
        color = self.COLORS.get(record.levelno, self.RESET)
        formatted_fmt = f"{color}{self._fmt}{self.RESET}"
        formatter = logging.Formatter(formatted_fmt, self.datefmt)
        return formatter.format(record)

def setup_logger(
    name: str = "InsiderCrypto",
    log_level: Optional[str] = None,
    log_dir: Optional[str] = None,
    alert_log: Optional[str] = None
) -> logging.Logger:
    """
    Configura o sistema de logging com handlers para console e arquivos.

    Args:
        name (str): Nome do logger. Padrão: "InsiderCrypto".
        log_level (str, optional): Nível de log (ex: "DEBUG", "INFO"). Padrão: settings.
        log_dir (str, optional): Diretório para arquivos de log. Padrão: settings.
        alert_log (str, optional): Nome do arquivo de alertas. Padrão: settings.

    Returns:
        logging.Logger: Instância do logger configurado.

    Raises:
        OSError: Se não for possível criar o diretório de logs.
    """
    # Configurar diretório de logs
    log_dir = log_dir or settings.LOG_CONFIG["LOG_DIR"]
    try:
        Path(log_dir).mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise OSError(f"Falha ao criar diretório de logs: {log_dir}") from e

    # Registrar logger customizado
    logging.setLoggerClass(CustomLogger)
    logger = logging.getLogger(name)

    # Converter nível de log para inteiro
    resolved_log_level = log_level or settings.LOG_CONFIG["LOG_LEVEL"]
    level = getattr(logging, resolved_log_level.upper(), logging.INFO)
    logger.setLevel(level)

    # Evitar handlers duplicados
    if not logger.handlers:
        # Configurar formatação
        base_fmt = "%(asctime)s | %(name)s | %(levelname)s | %(module)s:%(lineno)d - %(message)s"
        date_fmt = "%Y-%m-%d %H:%M:%S"

        # Handler para console
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(ColorFormatter(base_fmt, date_fmt))
        console_handler.setLevel(level)

        # Handler para arquivo principal com rotação
        main_handler = TimedRotatingFileHandler(
            filename=os.path.join(log_dir, "main.log"),
            when="midnight",
            backupCount=7,
            encoding="utf-8"
        )
        main_handler.setFormatter(logging.Formatter(base_fmt, date_fmt))
        main_handler.setLevel(level)

        # Handler para alertas críticos
        alert_log_name = alert_log or settings.LOG_CONFIG["ALERT_LOG"]
        alert_handler = logging.FileHandler(
            filename=os.path.join(log_dir, alert_log_name),
            mode="a",
            encoding="utf-8"
        )
        alert_handler.setLevel(ALERT_LEVEL)
        alert_handler.setFormatter(logging.Formatter(base_fmt, date_fmt))

        # Adicionar handlers
        logger.addHandler(console_handler)
        logger.addHandler(main_handler)
        logger.addHandler(alert_handler)

    return logger

def get_logger(name: Optional[str] = None) -> logging .Logger:
    """
    Obtém uma instância do logger configurado.

    Args:
        name (str, optional): Nome do logger. Padrão: "InsiderCrypto".

    Returns:
        logging.Logger: Instância do logger.
    """
    return logging.getLogger(name or "InsiderCrypto")

# Exemplo de uso
if __name__ == "__main__":
    logger = setup_logger()
    logger.info("Sistema de logging inicializado com sucesso!")
    logger.alert("ALERTA: Teste de alerta crítico")
    logger.warning("Aviso: Teste de mensagem de aviso")

    # Exemplo de tratamento de exceção
    try:
        raise InsiderCryptoError(
            "Erro de teste",
            details="Detalhes do erro",
            cause=ValueError("Causa raiz")
        )
    except InsiderCryptoError as e:
        logger.log_exception(e, context={"user_id": 123, "action": "test"})