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
        "name": f"{symbol} Token",
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
        {"text": "Ótimo projeto!", "timestamp": "2023-01-01T00:00:00Z"},
        {"text": "Não gostei", "timestamp": "2023-01-01T01:00:00Z"}
    ]
    
    # Mock do método de análise de sentimento
    async def mock_analyze_sentiment(social_data):
        return {
            "vader_score": {"compound": 0.8},  # Certifique-se de que o valor é maior que 0.7
            "huggingface_label": "POSITIVE",
            "huggingface_score": 0.99
        }
    
    mock.analyze_sentiment = AsyncMock(side_effect=mock_analyze_sentiment)
    
    return mock

@pytest.fixture
def memecoin_manager_mock():
    """Mock do MemecoinManager para simular a adição de memecoins."""
    mock = Mock(spec=MemecoinManager)
    mock.memecoins = []
    
    def add_memecoin(memecoin):
        mock.memecoins.append(memecoin)
    
    mock.add_memecoin = Mock(side_effect=add_memecoin)
    return mock

@pytest.fixture
def historical_data():
    """Gera dados históricos válidos para análise técnica."""
    return pd.DataFrame({
        'close': np.linspace(100, 200, num=20)
    })

@pytest.fixture
def market_analyzer(mocker, memecoin_manager_mock):
    """Cria uma instância do MarketAnalyzer com mocks injetados corretamente para métodos assíncronos."""
    # Cria o mock do DEX API com métodos assíncronos
    dex_api_mock = create_autospec(DexAPI, instance=True)
    
    # Configura o método fetch_market_data para retornar uma coroutine
    async def mock_fetch_market_data(symbol):
        return {
            'name': f"{symbol} Token",
            'symbol': symbol,
            'price': 150.0,
            'volume': 2_000_000.0,
            'liquidity': 1_000_000.0,
            'holders': 10000
        }
    
    dex_api_mock.fetch_market_data = AsyncMock(side_effect=mock_fetch_market_data)
    
    # Cria o mock da SocialAPI com métodos assíncronos
    social_api_mock = create_autospec(SocialAPI, instance=True)
    
    # Configura o método fetch_twitter_mentions para retornar uma coroutine
    async def mock_fetch_twitter_mentions(symbol):
        return [
            {"text": "Ótimo projeto!", "timestamp": "2023-01-01T00:00:00Z"},
            {"text": "Não gostei", "timestamp": "2023-01-01T01:00:00Z"}
        ]
    
    social_api_mock.fetch_twitter_mentions = AsyncMock(side_effect=mock_fetch_twitter_mentions)
    
    # Configura o mock para análise de sentimento - este é o ponto crítico
    async def mock_analyze_sentiment(text):
        return {"vader_score": {"compound": 0.8}}
    
    social_api_mock.analyze_sentiment = AsyncMock(side_effect=mock_analyze_sentiment)
    
    return MarketAnalyzer(
        dex_api=dex_api_mock,
        social_api=social_api_mock,
        manager=memecoin_manager_mock
    )

# Testes Unitários #############################################################

class TestMarketAnalyzer:
    """Testes para a classe MarketAnalyzer com diferentes configurações de mock."""

    from unittest.mock import AsyncMock

class TestMarketAnalyzer:
    # ... outros métodos de teste ...

    @pytest.mark.asyncio
    async def test_processamento_simultaneo(self, market_analyzer):
        """Verifica o processamento bem-sucedido de múltiplos símbolos."""
        # Cria mock objects para representar instâncias de Memecoin
        mock_memecoin_sol = AsyncMock(spec=Memecoin)
        mock_memecoin_eth = AsyncMock(spec=Memecoin)
        mock_memecoin_btc = AsyncMock(spec=Memecoin)

        # Configura o método _create_memecoin_instance para retornar os mock objects
        market_analyzer._create_memecoin_instance = AsyncMock(side_effect=[
            mock_memecoin_sol, mock_memecoin_eth, mock_memecoin_btc
        ])

        # Executa o método que está sendo testado
        await market_analyzer.realtime_monitoring(["SOL", "ETH", "BTC"])

        # Verifica se add_memecoin foi chamado 3 vezes
        assert market_analyzer.memecoin_manager.add_memecoin.call_count == 3

        # Verifica se add_memecoin foi chamado com as instâncias corretas de Memecoin
        market_analyzer.memecoin_manager.add_memecoin.assert_has_calls([
            call(mock_memecoin_sol),
            call(mock_memecoin_eth),
            call(mock_memecoin_btc)
        ], any_order=True)

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
        assert len(market_analyzer.memecoin_manager.memecoins) > 0  # Verifica se a lista não está vazia
        memecoin = market_analyzer.memecoin_manager.memecoins[0]

        assert memecoin.symbol == "SOL"
        assert memecoin.price == 150.0  # Verifique se o preço corresponde ao que foi mockado

        # Aplicação de análise técnica
        indicadores = market_analyzer.apply_technical_analysis(historical_data)
        sinal = market_analyzer.detect_opportunities(memecoin)

        assert isinstance(indicadores, dict)
        assert sinal == "buy"  # Verifique se o sinal é "buy"

    @pytest.mark.asyncio
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
    with pytest.raises(AnalysisError):
        Memecoin(
            symbol="SOL",
            name="Solana",
            price="100.0",  # String inválida
            volume_24h=500_000.0,
            liquidity=1_000_000.0,
            holders=1000,
            social_mentions=50,
            sentiment_score=0.75
        )

def test_tipos_dados_validos(market_analyzer):
    """Testa criação de Memecoin com tipos de dados válidos."""
    memecoin_valida = Memecoin(
        symbol="SOL",
        name="Solana",
        price=100.0,  # Float válido
        volume_24h=500_000.0,
        liquidity=1_000_000.0,
        holders=1000,
        social_mentions=50,
        sentiment_score=0.75
    )
    assert isinstance(memecoin_valida, Memecoin)

# Configuração de Testes #######################################################

if __name__ == "__main__":
    pytest.main([
        "-v",
        "--cov=analysis",
        "--cov-report=term-missing",
        "--durations=5"
    ])