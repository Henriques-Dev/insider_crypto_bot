import aiohttp
from typing import Dict, List
from transformers import pipeline
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from logger import get_logger
from config import settings
from error_handling import (
    handle_errors,
    APIConnectionError,
    DataValidationError,
    ProcessingError
)

logger = get_logger()

class SocialAPI:
    """
    Cliente para APIs sociais e análise de sentimento NLP com tratamento de erros avançado.
    """
    def __init__(self):
        self.twitter_url = settings.API_URLS["twitter"]
        self.reddit_url = settings.API_URLS["reddit"]
        self._session = None
        self.nlp_model = self._load_nlp_model()
        self.vader = SentimentIntensityAnalyzer()

    @property
    async def session(self):
        """Gerencia conexões HTTP de forma eficiente"""
        if not self._session or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    def _load_nlp_model(self):
        """Carrega modelo NLP com tratamento de erros de inicialização"""
        try:
            return pipeline(
                "sentiment-analysis", 
                model="distilbert-base-uncased-finetuned-sst-2-english"
            )
        except Exception as e:
            logger.critical(f"Falha ao carregar modelo NLP: {e}")
            raise ProcessingError(
                message="Falha na inicialização do modelo NLP",
                component="transformers",
                details=str(e)
            )

    @handle_errors(re_raise=True, log_level="warning")  # Alterado para re-levantar exceções
    async def fetch_twitter_mentions(self, symbol: str) -> List[Dict]:
        """Busca menções no Twitter para uma memecoin."""
        url = f"{self.twitter_url}/tweets/search/recent?query={symbol}"
        headers = {"Authorization": f"Bearer {settings.API_KEYS['twitter']}"}
        
        session = await self.session
        response = await session.get(url, headers=headers)
        
        if response.status != 200:
            raise APIConnectionError(
                message="Falha na conexão com Twitter API",
                url=url,
                status_code=response.status
            )

        data = await response.json()
        
        if not self._validate_social_data(data, platform="twitter"):
            raise DataValidationError(
                message="Resposta inválida do Twitter",
                field="response",
                value=data
            )
            
        return data

    @handle_errors(re_raise=True, log_level="warning")  # Alterado para re-levantar exceções
    async def fetch_reddit_posts(self, symbol: str) -> List[Dict]:
        """Busca posts no Reddit para uma memecoin."""
        url = f"{self.reddit_url}/search?q={symbol}"
        headers = {"User -Agent": "InsiderCryptoBot/0.1"}
        
        session = await self.session
        response = await session.get(url, headers=headers)
        
        if response.status != 200:
            raise APIConnectionError(
                message="Falha na conexão com Reddit API",
                url=url,
                status_code=response.status
            )

        data = await response.json()
        
        if not self._validate_social_data(data, platform="reddit"):
            raise DataValidationError(
                message="Resposta inválida do Reddit",
                field="response",
                value=data
            )
            
        return data

    @handle_errors(re_raise=True, log_level="error")  # Alterado para re-levantar exceções
    def analyze_sentiment(self, text: str) -> Dict:
        """Analisa o sentimento de um texto usando NLP."""
        if not text or len(text.strip()) < 3:
            raise DataValidationError(
                message="Texto inválido para análise",
                field="text",
                value=text
            )
        
        try:
            vader_score = self.vader.polarity_scores(text)
            hf_result = self.nlp_model(text[:512])[0]  # Truncar para limite do modelo
            
            return {
                "vader_score": vader_score,
                "huggingface_label": hf_result["label"],
                "huggingface_score": hf_result["score"]
            }
        except Exception as e:
            raise ProcessingError(
                message="Falha na análise de sentimento",
                component="nlp_model",
                input_data=text,
                details=str(e)
            )

    def _validate_social_data(self, data, symbol: str) -> None:
        """
        Valida estrutura básica dos dados sociais.
        
        Args:
            data: Dados sociais em formato de dicionário ou lista de dicionários
            symbol: Símbolo da criptomoeda
            
        Raises:
            DataValidationError: Se os dados não estiverem no formato esperado
        """
        # Caso 1: dados é um dicionário único
        if isinstance(data, dict):
            # Verificar se o dicionário contém as chaves necessárias
            required_keys = ["mentions", "sentiment"]
            missing_keys = [key for key in required_keys if key not in data]
            
            if missing_keys:
                raise DataValidationError(
                    message=f"Dados sociais para {symbol} incompletos. Faltam campos: {', '.join(missing_keys)}",
                    field="social_data",
                    value=list(data.keys())
                )
            return  # Os dados são válidos se chegamos aqui
        
        # Caso 2: dados é uma lista de dicionários
        elif isinstance(data, list):
            if not data:  # Lista vazia
                raise DataValidationError(
                    message=f"Lista de dados sociais para {symbol} está vazia",
                    field="social_data",
                    value="empty list"
                )
            
            # Aqui você pode adicionar validação para cada item da lista se necessário
            for i, item in enumerate(data):
                if not isinstance(item, dict):
                    raise DataValidationError(
                        message=f"Item {i} dos dados sociais para {symbol} não é um dicionário",
                        field="social_data",
                        value=type(item).__name__
                    )
                
                # Verificar se cada dicionário contém as chaves necessárias
                required_keys = ["mentions", "sentiment"]
                missing_keys = [key for key in required_keys if key not in item]
                
                if missing_keys:
                    raise DataValidationError(
                        message=f"Dados sociais para {symbol} no item {i} incompletos. Faltam campos: {', '.join(missing_keys)}",
                        field="social_data",
                        value=list(item.keys())
                    )
        
        # Caso 3: dados não é nem um dicionário nem uma lista
        else:
            raise DataValidationError(
                message="Dados sociais devem ser um dicionário ou uma lista de dicionários",
                field="social_data",
                value=type(data).__name__
            )