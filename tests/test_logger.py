import logging
from pathlib import Path
from logger import setup_logger, get_logger, CustomLogger
from config import settings
from error_handling import InsiderCryptoError, APIConnectionError  # Importa exceções personalizadas

import logging
from pathlib import Path
from logger import setup_logger, get_logger, CustomLogger
from config import settings
from error_handling import InsiderCryptoError, APIConnectionError  # Importa exceções personalizadas

def test_logger():
    """
    Testa o sistema de logging, verificando se os logs são gerados corretamente,
    se os arquivos de log são criados e se o tratamento de exceções funciona.
    """
    # Limpar o cache de loggers
    logging.Logger.manager.loggerDict.clear()

    # Garantindo que a classe CustomLogger seja registrada
    logging.setLoggerClass(CustomLogger)
    
    # Agora configuramos o logger
    logger = setup_logger(log_level=settings.LOG_CONFIG["LOG_LEVEL"], log_dir=settings.LOG_CONFIG["LOG_DIR"])
    
    # Verificar se o logger é da classe correta
    assert isinstance(logger, CustomLogger), "Logger não é uma instância de CustomLogger"
    
    # Testa os diferentes níveis de log
    logger.debug("Esta é uma mensagem de DEBUG")
    logger.info("Esta é uma mensagem de INFO")
    logger.warning("Esta é uma mensagem de WARNING")
    logger.alert("Esta é uma mensagem de ALERT")
    logger.error("Esta é uma mensagem de ERROR")
    logger.critical("Esta é uma mensagem de CRITICAL")

    # Teste com exceções genéricas
    try:
        1 / 0  # Gera uma exceção
    except ZeroDivisionError as e:
        logger.error(f"Erro ao dividir por zero: {e}", exc_info=True)

    # Teste com exceções personalizadas
    try:
        raise APIConnectionError(
            message="Falha na conexão com a API",
            url="https://api.example.com",
            status_code=500,
            details="Timeout ao tentar conectar",
            cause=Exception("Erro de rede")
        )
    except APIConnectionError as e:
        logger.log_exception(e, context={"user_id": 123, "action": "fetch_data"})

    # Verifica se os arquivos de log foram criados
    log_dir = Path(settings.LOG_CONFIG["LOG_DIR"])  # Usa o diretório de logs do settings
    main_log = log_dir / "main.log"
    alert_log = log_dir / "alerts.log"

    assert main_log.exists(), "Arquivo main.log não foi criado!"
    assert alert_log.exists(), "Arquivo alerts.log não foi criado!"

    # Verifica o conteúdo dos arquivos de log
    with open(main_log, "r", encoding="utf-8") as f:
        main_log_content = f.read()
        assert "DEBUG" in main_log_content, "Mensagem de DEBUG não foi registrada!"
        assert "INFO" in main_log_content, "Mensagem de INFO não foi registrada!"
        assert "WARNING" in main_log_content, "Mensagem de WARNING não foi registrada!"
        assert "ALERT" in main_log_content, "Mensagem de ALERT não foi registrada!"
        assert "ERROR" in main_log_content, "Mensagem de ERROR não foi registrada!"
        assert "CRITICAL" in main_log_content, "Mensagem de CRITICAL não foi registrada!"
        assert "APIConnectionError" in main_log_content, "Exceção personalizada não foi registrada!"
        assert "Falha na conexão com a API" in main_log_content, "Mensagem de erro personalizada não foi registrada!"

    with open(alert_log, "r", encoding="utf-8") as f:
        alert_log_content = f.read()
        assert "ALERT" in alert_log_content, "Mensagem de ALERT não foi registrada no alerts.log!"

    # Testa o logger retornado por get_logger
    another_logger = get_logger()
    another_logger.info("Testando o logger retornado por get_logger")
    with open(main_log, "r", encoding="utf-8") as f:
        main_log_content = f.read()
        assert "Testando o logger retornado por get_logger" in main_log_content, "Logger retornado por get_logger não funcionou!"

    print("Todos os testes passaram com sucesso!")

if __name__ == "__main__":
    test_logger()