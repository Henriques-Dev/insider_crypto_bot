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
from unittest.mock import AsyncMock, Mock
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
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

        # Valida os dados coletados
        self._validate_market_data(market_data, symbol)
        self._validate_social_data(social_data, symbol)

        # Cria e adiciona a instância de Memecoin ao gerenciador
        memecoin = self._create_memecoin_instance(symbol, market_data, social_data)
        self.memecoin_manager.add_memecoin(memecoin)

        logger.info(f"Memecoin processada: {symbol}", extra={"data": memecoin.summary()})

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

    def _validate_social_data(self, data: List[Dict], symbol: str) -> None:
        """Valida estrutura básica dos dados sociais."""
        if not isinstance(data, list):
            raise DataValidationError(
                message="Dados sociais devem ser uma lista",
                field="social_data",
                value=type(data).__name__
            )
        
        for i, post in enumerate(data):
            if "text" not in post:
                raise DataValidationError(
                    message=f"Post {i} sem texto para {symbol}",
                    field=f"social_data[{i}].text",
                    value=post
                )

    def _create_memecoin_instance(
        self,
        symbol: str,
        market_data: Dict,
        social_data: List[Dict]
    ) -> Memecoin:
        """Constrói instância Memecoin com dados validados."""
        sentiment_score = asyncio.run(self._calculate_sentiment_score(social_data))  # Chamada assíncrona
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
            try:
                sentiment = await self.social_api.analyze_sentiment(post["text"])
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

        return round(sum(scores) / len(scores), 4) if scores else 0.0

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
                message=f"Dados insuficientes ({len(historical_data)} períodos)",
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
        required_attrs = ["sentiment_score", "volume_24h"]
        missing = [attr for attr in required_attrs if not hasattr(memecoin, attr)]
        if missing:
            raise DataValidationError(
                message="Atributos obrigatórios ausentes",
                field="memecoin",
                value=f"Atributos faltantes: {', '.join(missing)}"
            )
        
        # Validação de tipos
        try:
            score = float(memecoin.sentiment_score)
            volume = float(memecoin.volume_24h)
        except (TypeError, ValueError) as e:
            raise AnalysisError(
                message="Tipo de dado inválido para análise",
                component="opportunity_detection",
                details={
                    "input_types": {
                        "sentiment_score": type(memecoin.sentiment_score).__name__,
                        "volume_24h": type(memecoin.volume_24h).__name__
                    },
                    "error": str(e)
                }
            )

        # Lógica de decisão
        if score > 0.7 and volume > 1_000_000:
            return "buy"
        if score < 0.3 and volume < 500_000:
            return "sell"
        
        return None