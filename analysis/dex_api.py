import aiohttp
from typing import Dict, Optional
from logger import get_logger
from config import settings
from functools import lru_cache
from error_handling import (
    handle_errors,
    APIConnectionError,
    DataValidationError
)

logger = get_logger()

class DexAPI:
    """
    Cliente para APIs descentralizadas (DexScreener, Solana Blockchain).
    Integrado com sistema de tratamento de erros personalizado.
    """
    def __init__(self):
        self.dexscreener_url = settings.API_URLS["dexscreener"]
        self.solana_api_url = settings.API_URLS["solana"]
        self.cache = {}
        self._session = None

    @property
    async def session(self):
        """Gerencia conexões HTTP de forma eficiente"""
        if not self._session or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    @handle_errors(re_raise=True, log_level="error")  # Alterado para re-levantar exceções
    async def fetch_market_data(self, symbol: str) -> Optional[Dict]:
        """Busca dados de mercado de uma memecoin específica."""
        url = f"{self.dexscreener_url}/tokens/{symbol}"
        
        session = await self.session
        response = await session.get(url)
        
        if response.status != 200:
            raise APIConnectionError(
                message="Falha na conexão com DexScreener",
                url=url,
                status_code=response.status
            )

        data = await response.json()
        
        if not self._validate_market_data(data):
            raise DataValidationError(
                message="Dados de mercado inválidos",
                field="response",
                value=data
            )

        self.cache[symbol] = data
        logger.debug(f"Dados de mercado obtidos para {symbol}")
        return data

    @handle_errors(re_raise=True, log_level="warning")  # Alterado para re-levantar exceções
    async def get_onchain_metrics(self, contract_address: str) -> Optional[Dict]:
        """Obtém métricas on-chain (holders, transações de whales)."""
        url = f"{self.solana_api_url}/token/{contract_address}/metrics"
        
        session = await self.session
        response = await session.get(url)
        
        if response.status != 200:
            raise APIConnectionError(
                message="Falha na conexão com Solana API",
                url=url,
                status_code=response.status
            )

        return await response.json()

    def _validate_market_data(self, data: Dict) -> bool:
        """Valida estrutura básica dos dados de mercado"""
        required_fields = ["price", "liquidity", "volume"]
        return all(field in data for field in required_fields)

    @lru_cache(maxsize=100)
    def get_cached_data(self, symbol: str) -> Optional[Dict]:
        """Retorna dados em cache para evitar requisições repetitivas."""
        return self.cache.get(symbol)

    async def close(self):
        """Fecha conexões HTTP"""
        if self._session and not self._session.closed:
            await self._session.close()