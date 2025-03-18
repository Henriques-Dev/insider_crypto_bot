import os
from dotenv import load_dotenv

# Carrega variáveis sensíveis do .env
load_dotenv()

# Configurações gerais do projeto
class Settings:
    # Variáveis de ambiente para APIs (sensíveis, vêm do .env)
    API_KEYS = {
        "dexscreener": os.getenv("DEXSCREENER_API_KEY"),
        "twitter": os.getenv("TWITTER_API_KEY"),
        "reddit": os.getenv("REDDIT_API_KEY"),
        "telegram": os.getenv("TELEGRAM_API_KEY"),
    }

    # Variáveis de ambiente para URLs
    API_URLS = {
        "dexscreener": "https://api.dexscreener.com/latest/dex",
        "solana": "https://api.solscan.io",
        "twitter": "https://api.twitter.com/2",
        "reddit": "https://www.reddit.com/api/v1",
    }

    # Configurações de log (não sensíveis, definidas diretamente no settings.py)
    LOG_CONFIG = {
        "LOG_LEVEL": "DEBUG",  # Nível de log padrão (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        "LOG_DIR": "logs",     # Diretório onde os logs serão armazenados
        "ALERT_LOG": "alerts.log",  # Nome do arquivo de alertas
    }

# Instância única das configurações
settings = Settings()