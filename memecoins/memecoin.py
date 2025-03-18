from dataclasses import dataclass
from typing import Optional

@dataclass
class Memecoin:
    """
    Classe que representa uma memecoin com métricas essenciais para análise.

    Atributos:
        symbol (str): Símbolo da memecoin (ex: SOL, DOGE).
        name (str): Nome completo da memecoin.
        price (float): Preço atual em dólares.
        volume_24h (float): Volume de negociação nas últimas 24 horas.
        liquidity (float): Liquidez total disponível.
        holders (int): Número de holders únicos.
        social_mentions (int): Quantidade de menções sociais (Twitter, Reddit, etc.).
        sentiment_score (Optional[float]): Pontuação de sentimento calculada por NLP (0.0 a 1.0).
    """
    symbol: str
    name: str
    price: float
    volume_24h: float
    liquidity: float
    holders: int
    social_mentions: int
    sentiment_score: Optional[float] = None

    def __str__(self) -> str:
        """Representação amigável dos dados da memecoin."""
        return (
            f"{self.symbol} ({self.name}) - "
            f"Price: ${self.price:.4f} | "
            f"24h Volume: ${self.volume_24h:,.2f} | "
            f"Liquidity: ${self.liquidity:,.2f} | "
            f"Holders: {self.holders:,} | "
            f"Mentions: {self.social_mentions:,}"
        )

    def is_high_volume(self, min_volume: float) -> bool:
        """
        Verifica se o volume de negociação está acima do limite especificado.
        
        Args:
            min_volume (float): Limite mínimo em dólares.
            
        Returns:
            bool: True se o volume for igual ou maior que o mínimo, False caso contrário.
        """
        return self.volume_24h >= min_volume

    def is_high_liquidity(self, min_liquidity: float) -> bool:
        """
        Verifica se a liquidez está acima do limite especificado.
        
        Args:
            min_liquidity (float): Limite mínimo em dólares.
            
        Returns:
            bool: True se a liquidez for igual ou maior que o mínimo, False caso contrário.
        """
        return self.liquidity >= min_liquidity

    def is_high_sentiment(self, min_sentiment: float = 0.7) -> bool:
        """
        Verifica se a pontuação de sentimento está acima do limite.
        
        Args:
            min_sentiment (float): Limite mínimo (0.0 a 1.0).
            
        Returns:
            bool: True se a pontuação for igual ou maior que o mínimo,
                  False se não houver pontuação disponível.
        """
        if self.sentiment_score is None:
            return False
        return self.sentiment_score >= min_sentiment