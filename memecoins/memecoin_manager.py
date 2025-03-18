from analysis.dex_api import DexAPI
from analysis.social_api import SocialAPI
from memecoins import Memecoin

# Cria uma instância do gerenciador de memecoins
class MemecoinManager:
    """
    Gerenciador de instâncias de Memecoin.

    Atributos:
        memecoins (list): Lista de instâncias de Memecoin gerenciadas.
    """
    def __init__(self):
        """Inicializa o gerenciador com uma lista vazia de memecoins."""
        self.memecoins = []

    def add_memecoin(self, memecoin: Memecoin) -> None:
        """
        Adiciona uma nova instância de Memecoin à lista.

        Args:
            memecoin (Memecoin): A instância de Memecoin a ser adicionada.
        """
        self.memecoins.append(memecoin)

async def fetch_memecoins() -> MemecoinManager:
    """
    Busca dados de mercado e sociais para criar instâncias de Memecoin.

    Retorna:
        MemecoinManager: Instância do gerenciador com memecoins adicionadas.

    Raises:
        Exception: Para falhas na busca de dados de mercado ou sociais.
    """
    # Cria instâncias das APIs
    dex_api = DexAPI()
    social_api = SocialAPI()
    manager = MemecoinManager()

    try:
        # Obtém dados de mercado
        market_data = await dex_api.get_market_data()  # Supondo que seja assíncrono
        for data in market_data:
            # Cria uma instância de Memecoin com os dados obtidos
            memecoin = Memecoin(
                symbol=data["symbol"],
                name=data["name"],
                price=data["price"],
                volume_24h=data["volume_24h"],
                liquidity=data["liquidity"],
                holders=data["holders"],
                social_mentions=await social_api.get_mentions(data["symbol"]),  # Supondo que seja assíncrono
                sentiment_score=await social_api.get_sentiment(data["symbol"]),  # Supondo que seja assíncrono
            )
            manager.add_memecoin(memecoin)
    except Exception as e:
        print(f"Erro ao buscar dados: {e}")

    return manager

# Para chamar a função assíncrona, você pode usar um loop de eventos
if __name__ == "__main__":
    import asyncio
    memecoin_manager = asyncio.run(fetch_memecoins())
    print(f"Memecoins adicionadas: {len(memecoin_manager.memecoins)}")