"""
Módulo de análise de mercado para Memecoins.

Combina dados de APIs DEX e redes sociais para gerar sinais de compra/venda
baseados em análise técnica e sentimento do mercado.

Implementa:
- Validação de dados hierárquica
- Análise técnica com TA-Lib
- Análise de sentimento em tempo real
- Detecção de oportunidades com critérios combinados
- Tratamento de erros resiliente
"""

import asyncio
import json
from unittest.mock import AsyncMock, Mock
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union
from logger import get_logger
from memecoins import Memecoin, MemecoinManager
from analysis import DexAPI, SocialAPI
from ta.momentum import RSIIndicator
from ta.trend import MACD
from ta.volatility import BollingerBands
from error_handling import (
    handle_errors,
    DataValidationError,
    ProcessingError,
    AnalysisError
)

logger = get_logger()

class MarketAnalyzer:
    """
    Coordenador principal de análise de mercado para Memecoins.
    
    Atributos:
        dex_api (DexAPI): Conexão com API de dados de mercado.
        social_api (SocialAPI): Conexão com API de dados sociais.
        memecoin_manager (MemecoinManager): Gerenciador de instâncias Memecoin.

    Métodos principais:
        realtime_monitoring: Monitoramento assíncrono de múltiplos símbolos.
        apply_technical_analysis: Análise técnica com indicadores TA-Lib.
        detect_opportunities: Detecção de sinais de compra/venda.
    """

    def __init__(self, dex_api: DexAPI, social_api: SocialAPI, manager: MemecoinManager = None) -> None:
        """
        Inicializa o analisador com dependências validadas.

        Args:
            dex_api: Instância configurada da API DEX.
            social_api: Instância configurada da API Social.
            manager: Instância do gerenciador de memecoins (opcional).

        Raises:
            DataValidationError: Se as dependências forem inválidas.
        """
        self.dex_api = dex_api
        self.social_api = social_api
        self.memecoin_manager = manager or MemecoinManager()

        self._validate_dependencies()

    def _validate_dependencies(self) -> None:
        """Valida integridade das dependências injetadas."""
        if not isinstance(self.dex_api, (DexAPI, Mock, AsyncMock)):
            raise DataValidationError(
                message="Instância DexAPI inválida",
                field="dex_api",
                value=type(self.dex_api).__name__
            )
        if not isinstance(self.social_api, (SocialAPI, Mock, AsyncMock)):
            raise DataValidationError(
                message="Instância SocialAPI inválida",
                field="social_api",
                value=type(self.social_api).__name__
            )

    @handle_errors(re_raise=False, log_level="warning")
    async def realtime_monitoring(self, symbols: List[str]) -> None:
        """
        Monitora múltiplas memecoins em tempo real com processamento paralelo.

        Args:
            symbols: Lista de símbolos para monitoramento.

        Raises:
            DataValidationError: Para lista de símbolos inválida.
            ProcessingError: Para falhas na coleta de dados.
        """
        if not symbols or not isinstance(symbols, list):
            raise DataValidationError(
                message="Lista de símbolos inválida",
                field="symbols",
                value=symbols
            )

        # Remove duplicados e cria tarefas para processamento paralelo
        tasks = [self.process_memecoin(symbol) for symbol in set(symbols)]
        
        # Tenta coletar dados e levanta ProcessingError em caso de falha
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            raise ProcessingError(
                message="Falha na coleta de dados de mercado ou sociais",
                component="realtime_monitoring",
                details=str(e)
            )

    @handle_errors(re_raise=False, log_level="error")
    async def process_memecoin(self, symbol: str) -> None:
        """
        Processa pipeline completo para uma memecoin.

        1. Coleta dados de mercado e sociais.
        2. Valida dados brutos.
        3. Calcula métricas derivadas.
        4. Armazena instância Memecoin.

        Args:
            symbol: Símbolo da memecoin para processamento.
        """
        
        # Coleta dados de mercado e sociais
        market_data, social_data = await asyncio.gather(
            self.dex_api.fetch_market_data(symbol),
            self.social_api.fetch_twitter_mentions(symbol)
        )

        # Adicione um log para verificar os dados sociais
        print(f"Dados sociais coletados para {symbol}: {social_data}")

        # Valida os dados coletados
        self._validate_market_data(market_data, symbol)
        self._validate_social_data(social_data, symbol)

        # Cria e adiciona a instância de Memecoin ao gerenciador
        memecoin = await self._create_memecoin_instance(symbol, market_data, social_data)  # Adicione 'await' aqui
        self.memecoin_manager.add_memecoin(memecoin)

        logger.info(f"Memecoin processada: {symbol}", extra={"data": str(memecoin)})

    def _validate_market_data(self, data: Dict, symbol: str) -> None:
        """Valida estrutura básica dos dados de mercado."""
        required_fields = {
            "name": str,
            "price": (float, int),
            "volume": (int, float),
            "liquidity": (int, float),
            "holders": int
        }

        for field, expected_type in required_fields.items():
            if field not in data:
                raise DataValidationError(
                    message=f"Campo obrigatório ausente: {field}",
                    field=f"market_data.{field}",
                    value=data
                )
            if not isinstance(data[field], expected_type):
                raise DataValidationError(
                    message=f"Tipo inválido para {field}",
                    field=f"market_data.{field}",
                    value=type(data[field]).__name__
                )

    def _validate_social_data(self, data: Union[Dict, List[Dict]], symbol: str) -> None:
        """
        Valida estrutura básica dos dados sociais.
        
        Args:
            data: Dados sociais em formato de dicionário ou lista de dicionários
            symbol: Símbolo da criptomoeda
        """
        # Caso 1: dados é um dicionário único
        if isinstance(data, dict):
            # Verificar se o dicionário contém as chaves necessárias
            if "mentions" in data and "sentiment" in data:
                return  # Os dados são válidos
            else:
                missing_keys = []
                if "mentions" not in data:
                    missing_keys.append("mentions")
                if "sentiment" not in data:
                    missing_keys.append("sentiment")
                    
                raise DataValidationError(
                    message=f"Dados sociais para {symbol} incompletos. Faltam campos: {', '.join(missing_keys)}",
                    field="social_data",
                    value=list(data.keys())
                )
        
        # Caso 2: dados é uma lista de dicionários
        elif isinstance(data, list):
            if not data:  # Lista vazia
                raise DataValidationError(
                    message=f"Lista de dados sociais para {symbol} está vazia",
                    field="social_data",
                    value="empty list"
                )
            
            # Validar cada item da lista conforme a lógica original
            for i, post in enumerate(data):
                if "text" not in post:
                    raise DataValidationError(
                        message=f"Post {i} sem texto para {symbol}",
                        field=f"social_data[{i}].text",
                        value=post
                    )
        
        # Caso 3: dados não é nem um dicionário nem uma lista
        else:
            raise DataValidationError(
                message="Dados sociais devem ser um dicionário ou uma lista de dicionários",
                field="social_data",
                value=type(data).__name__
            )

    async def _create_memecoin_instance(
        self,
        symbol: str,
        market_data: Dict,
        social_data: List[Dict]
    ) -> Memecoin:
        """
        Constrói instância Memecoin com dados validados.

        Args:
            symbol: Símbolo da memecoin (ex: "SOL").
            market_data: Dicionário contendo dados de mercado. Espera-se as chaves:
                - name: Nome da memecoin.
                - price: Preço atual (float ou int).
                - volume: Volume de negociação nas últimas 24h (float ou int).
                - liquidity: Liquidez do par de negociação (float ou int).
                - holders: Número de detentores (int).
            social_data: Lista de dicionários contendo menções sociais. Cada dicionário deve conter:
                - text: Texto da menção.
                - timestamp: Data e hora da menção.

        Returns:
            Instância de Memecoin.

        Raises:
            DataValidationError: Se os dados de mercado ou sociais forem inválidos.
        """
        # Validação dos dados de mercado
        required_market_fields = ["name", "price", "volume", "liquidity", "holders"]
        for field in required_market_fields:
            if field not in market_data:
                raise DataValidationError(
                    message=f"Dados de mercado inválidos: campo '{field}' ausente",
                    field=f"market_data.{field}",
                    value=None
                )

        # Validação dos dados sociais
        if not isinstance(social_data, list):
            raise DataValidationError(
                message="Dados sociais inválidos: deve ser uma lista de dicionários",
                field="social_data",
                value=social_data
            )

        # Cálculo do sentiment score com tratamento de exceções
        try:
            sentiment_score = await self._calculate_sentiment_score(social_data)
        except Exception as e:
            logger.error(f"Erro ao calcular sentiment score para {symbol}: {e}")
            sentiment_score = 0.0  # Valor padrão em caso de erro

        # Criação da instância de Memecoin
        return Memecoin(
            symbol=symbol,
            name=market_data["name"],
            price=float(market_data["price"]),
            volume_24h=float(market_data["volume"]),
            liquidity=float(market_data["liquidity"]),
            holders=int(market_data["holders"]),
            social_mentions=len(social_data),
            sentiment_score=sentiment_score
        )

    @handle_errors(re_raise=True, log_level="error")
    async def _calculate_sentiment_score(self, social_data: List[Dict]) -> float:
        """
        Calcula score de sentimento médio para posts sociais.

        Args:
            social_data: Lista de posts com texto.

        Returns:
            float: Score médio entre -1 (negativo) e 1 (positivo).

        Raises:
            ProcessingError: Para falhas na análise de sentimento.
        """
        if not social_data:
            logger.debug("Nenhum dado social para análise de sentimento")
            return 0.0

        scores = []
        for post in social_data:
            if "text" not in post:
                logger.warning("Post sem texto ignorado")
                continue  # Ignora posts sem texto

            logger.debug(f"Processando post: {post['text']}")  # Log do texto do post

            try:
                sentiment = await self.social_api.analyze_sentiment(post["text"])
                logger.debug(f"Sentiment retornado: {sentiment}")  # Log do resultado da análise
                scores.append(sentiment["vader_score"]["compound"])
            except KeyError as e:
                logger.warning(f"Post incompleto ignorado: {str(e)}")
            except Exception as e:
                raise ProcessingError(
                    message="Falha na análise de sentimento",
                    component="nlp_processor",
                    input_data=post,
                    details=str(e)
                )

        if scores:
            average_score = round(sum(scores) / len(scores), 4)
            logger.debug(f"Score médio calculado: {average_score}")
            return average_score
        else:
            logger.debug("Nenhum score de sentimento calculado, retornando 0.0")
            return 0.0

    @handle_errors(re_raise=True, log_level="warning")
    def apply_technical_analysis(self, historical_data: pd.DataFrame) -> Dict[str, float]:
        """
        Aplica análise técnica com múltiplos indicadores.

        Parâmetros:
            historical_data: DataFrame com dados históricos:
                - Deve conter coluna 'close'.
                - Mínimo de 14 períodos.

        Retorna:
            Dict com últimos valores dos indicadores:
            - rsi: Índice de Força Relativa (14 períodos).
            - macd: Converg ência/Divergência de Médias Móveis.
            - bollinger_upper: Banda superior de Bollinger (20 períodos).
            - bollinger_lower: Banda inferior de Bollinger (20 períodos).

        Raises:
            DataValidationError: Para dados insuficientes ou inválidos.
        """
        # Validação inicial
        if historical_data.empty or len(historical_data) < 14:
            raise DataValidationError(
                message=f"Dados insuficientes ({len(historical_data)} períodos), são necessários 14 períodos",
                field="historical_data.index",
                value=len(historical_data)
            )

        if "close" not in historical_data.columns:
            raise DataValidationError(
                message="Coluna 'close' ausente",
                field="historical_data.columns",
                value=list(historical_data.columns)
            )
        
        # Pré-processamento
        closes = historical_data["close"].ffill().bfill()
        if closes.isnull().any():
            raise DataValidationError(
                message="Série 'close' contém valores inválidos",
                field="historical_data.close",
                value=closes[closes.isnull()].index.tolist()
            )

        # Cálculo dos indicadores
        try:
            return {
                "rsi": RSIIndicator(closes, 14).rsi().iloc[-1],
                "macd": MACD(closes).macd().iloc[-1],
                "bollinger_upper": BollingerBands(closes).bollinger_hband().iloc[-1],
                "bollinger_lower": BollingerBands(closes).bollinger_lband().iloc[-1]
            }
        except Exception as e:
            raise AnalysisError(
                message="Falha no cálculo de indicadores",
                component="technical_analysis",
                input_stats=closes.describe().to_dict(),
                details=str(e)
            )
    
    @handle_errors(re_raise=True, log_level="warning")
    def detect_opportunities(self, memecoin: Memecoin) -> Optional[str]:
        """
        Avalia condições combinadas para detecção de oportunidades.

        Estratégia:
            Compra: Sentimento > 0.7 AND Volume 24h > 1M.
            Venda: Sentimento < 0.3 AND Volume 24h < 500K.

        Args:
            memecoin: Instância Memecoin com dados atualizados.

        Returns:
            "buy", "sell" ou None.

        Raises:
            DataValidationError: Para atributos ausentes.
            AnalysisError: Para tipos de dados inválidos.
        """
        # Validação de atributos
        required_attrs = ["sentiment_score", "volume_24h", "price"]  # Adicionado "price"
        missing = [attr for attr in required_attrs 
                if not hasattr(memecoin, attr) or getattr(memecoin, attr) is None]
        
        if missing:
            raise DataValidationError(
                message="Atributos obrigatórios ausentes ou nulos",
                field="memecoin",
                value=f"Atributos faltantes ou nulos: {', '.join(missing)}"
            )
        
        # Validação de tipos
        try:
            score = float(memecoin.sentiment_score)
            volume = float(memecoin.volume_24h)
            price = float(memecoin.price)  # Adicionado validação do tipo de preço
        except (TypeError, ValueError) as e:
            # Verifique a assinatura correta do construtor AnalysisError
            raise AnalysisError(
                message="Tipo de dado inválido para análise",
                metric="sentiment_and_volume",
                dataset=f"Memecoin: {memecoin.symbol}",
                algorithm="opportunity_detection",
                details=json.dumps({
                    "input_types": {
                        "sentiment_score": type(memecoin.sentiment_score).__name__,
                        "volume_24h": type(memecoin.volume_24h).__name__,
                        "price": type(memecoin.price).__name__  # Adicionado tipo do preço
                    },
                    "error": str(e)
                }),
                cause=e
            )

        # Lógica de decisão
        print(f"Sentiment Score: {score}, Volume: {volume}")  # Adicione esta linha para depuração
        if score > 0.7 and volume > 1_000_000:
            return "buy"
        if score < 0.3 and volume < 500_000:
            return "sell"
        else:
            return None