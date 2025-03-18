"""
Testes unitários e de integração para o módulo de análise de mercado.
"""

import pytest
from unittest.mock import AsyncMock, Mock, call, create_autospec
import pandas as pd
import numpy as np
import logging
from analysis import MarketAnalyzer, DexAPI, SocialAPI
from memecoins import Memecoin, MemecoinManager
from error_handling import (
    DataValidationError,
    ProcessingError,
    AnalysisError
)

# Fixtures #####################################################################

@pytest.fixture
def dex_api_mock():
    """Mock da DexAPI para simular dados de mercado."""
    mock = create_autospec(DexAPI, instance=True)
    mock.fetch_market_data.side_effect = lambda symbol: {
        "symbol": symbol,
        "price": 150.0,
        "volume": 2_000_000.0,
        "liquidity": 1_000_000.0,
        "holders": 10_000
    }
    return mock

@pytest.fixture
def social_api_mock():
    """Mock da SocialAPI com análise de sentimento controlada."""
    mock = create_autospec(SocialAPI, instance=True)
    mock.fetch_twitter_mentions.return_value = [
        {"text": "Ótimo projeto!"},
        {"text": "Não gostei"}
    ]
    mock.analyze_sentiment.return_value = {
        "vader_score": {"compound": 0.8},
        "huggingface_label": "POSITIVE",
        "huggingface_score": 0.99
    }
    return mock

@pytest.fixture
def memecoin_manager_mock():
    """Mock do MemecoinManager para simular a adição de memecoins."""
    mock = Mock(spec=MemecoinManager)
    mock.memecoins = []
    mock.add_memecoin = Mock()
    return mock

@pytest.fixture
def historical_data():
    """Gera dados históricos válidos para análise técnica."""
    return pd.DataFrame({
        'close': np.linspace(100, 200, num=20)
    })

@pytest.fixture
def market_analyzer(dex_api_mock, memecoin_manager_mock):
    """Cria uma instância do MarketAnalyzer com mocks injetados."""
    return MarketAnalyzer(
        dex_api=dex_api_mock,
        social_api=create_autospec(SocialAPI, instance=True),
        manager=memecoin_manager_mock
    )

# Testes Unitários #############################################################

class TestMarketAnalyzer:
    """Testes para a classe MarketAnalyzer com diferentes configurações de mock."""

    @pytest.mark.asyncio
    async def test_processamento_simultaneo(self, market_analyzer):
        """Verifica o processamento bem-sucedido de múltiplos símbolos."""
        await market_analyzer.realtime_monitoring(["SOL", "ETH", "BTC"])
        assert market_analyzer.memecoin_manager.add_memecoin.call_count == 3  # Verifica se 3 chamadas foram feitas
        market_analyzer.memecoin_manager.add_memecoin.assert_has_calls([
            call("SOL"), call("ETH"), call("BTC")
        ], any_order=True)
        
    def test_analise_tecnica_dados_insuficientes(self, market_analyzer):
        """Verifica o tratamento de dados históricos incompletos."""
        with pytest.raises(DataValidationError) as exc_info:
            market_analyzer.apply_technical_analysis(pd.DataFrame({'close': [100]*13}))
        
        assert exc_info.value.field == "historical_data"
        assert "14 períodos" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_dependencias_invalidas(self):
        """Testa a validação de dependências inválidas no construtor."""
        with pytest.raises(DataValidationError):
            MarketAnalyzer("api_inválida", None)

    def test_deteccao_oportunidades_atributos_faltantes(self, market_analyzer):
        """Testa a detecção de oportunidades com atributos obrigatórios ausentes."""
        memecoin_invalida = Memecoin(
            symbol="SOL",
            name="Solana",
            price=100.0,
            volume_24h=500_000.0,
            liquidity=1_000_000.0,
            holders=1000,
            social_mentions=50
            # sentiment_score ausente
        )
        
        with pytest.raises(DataValidationError):
            market_analyzer.detect_opportunities(memecoin_invalida)

# Testes de Integração #########################################################

class TestCenariosCompletos:
    """Testes de cenários completos com combinações complexas de mocks."""

    @pytest.mark.asyncio
    async def test_fluxo_positivo(self, market_analyzer, historical_data):
        """Teste completo do fluxo de análise com dados válidos."""
        await market_analyzer.realtime_monitoring(["SOL"])
        
        # Verifica se a memecoin foi criada com dados corretos
        memecoin = market_analyzer.memecoin_manager.memecoins[0]
        assert memecoin.symbol == "SOL"
        assert memecoin.price == 150.0
        
        # Simula a memecoin adicionada
        memecoin = Memecoin(
            symbol="SOL",
            name="Solana",
            price=150.0,
            volume_24h=2_000_000.0,
            liquidity=1_000_000.0,
            holders=10_000,
            social_mentions=2,
            sentiment_score=0.8
        )
        market_analyzer.memecoin_manager.memecoins = [memecoin]
        
        indicadores = market_analyzer.apply_technical_analysis(historical_data)
        sinal = market_analyzer.detect_opportunities(memecoin)
        
        assert isinstance(indicadores, dict)
        assert sinal == "buy"

    @ pytest.mark.asyncio
    async def test_fluxo_com_falhas(self, dex_api_mock, social_api_mock):
        """Teste completo do fluxo de tratamento de erros."""
        dex_api_mock.fetch_market_data.side_effect = Exception("Erro API")
        social_api_mock.fetch_twitter_mentions.return_value = []
        
        analyzer = MarketAnalyzer(dex_api_mock, social_api_mock)
        
        with pytest.raises(ProcessingError) as exc_info:
            await analyzer.realtime_monitoring(["SOL"])
        
        assert "Erro API" in str(exc_info.value)  # Verifica se a mensagem de erro está correta

# Testes de Estratégia #########################################################

def test_limiares_decisao(market_analyzer):
    """Teste paramétrico dos critérios de compra/venda."""
    test_cases = [
        (0.75, 1_500_000, "buy"),
        (0.25, 400_000, "sell"),
        (0.5, 750_000, None),
        (0.8, 900_000, None),
        (0.4, 1_100_000, None)
    ]
    
    for score, volume, esperado in test_cases:
        memecoin = Memecoin(
            symbol="TEST",
            name="Test Coin",
            price=100.0,
            volume_24h=volume,
            liquidity=1_000_000.0,
            holders=1000,
            social_mentions=50,
            sentiment_score=score
        )
        
        assert market_analyzer.detect_opportunities(memecoin) == esperado

def test_tipos_dados_invalidos(market_analyzer):
    """Testa detecção de tipos de dados inválidos."""
    memecoin_invalida = Memecoin(
        symbol="SOL",
        name="Solana",
        price="100.0",  # String inválida
        volume_24h=500_000.0,
        liquidity=1_000_000.0,
        holders=1000,
        social_mentions=50,
        sentiment_score=0.75
    )
    
    with pytest.raises(AnalysisError):
        market_analyzer.detect_opportunities(memecoin_invalida)

# Configuração de Testes #######################################################

if __name__ == "__main__":
    pytest.main([
        "-v",
        "--cov=analysis",
        "--cov-report=term-missing",
        "--durations=5"
    ])