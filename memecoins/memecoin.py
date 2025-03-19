from dataclasses import dataclass
from typing import Optional
from error_handling import AnalysisError

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

    def __post_init__(self):
        """Valida os tipos dos atributos após a inicialização."""
        if not isinstance(self.price, (float, int)):
            raise AnalysisError(
                message="Tipo de dado inválido para análise",
                metric="price",
                dataset=f"Memecoin: {self.symbol}",
                algorithm="type_validation",
                details=f"O atributo 'price' deve ser um número (float ou int). Recebido: {type(self.price)}",
                cause=TypeError(f"Expected float or int, got {type(self.price)}")
            )
        if not isinstance(self.volume_24h, (float, int)):
            raise AnalysisError(
                message="Tipo de dado inválido para análise",
                metric="volume_24h",
                dataset=f"Memecoin: {self.symbol}",
                algorithm="type_validation",
                details=f"O atributo 'volume_24h' deve ser um número (float ou int). Recebido: {type(self.volume_24h)}",
                cause=TypeError(f"Expected float or int, got {type(self.volume_24h)}")
            )
        if not isinstance(self.liquidity, (float, int)):
            raise AnalysisError(
                message="Tipo de dado inválido para análise",
                metric="liquidity",
                dataset=f"Memecoin: {self.symbol}",
                algorithm="type_validation",
                details=f"O atributo 'liquidity' deve ser um número (float ou int). Recebido: {type(self.liquidity)}",
                cause=TypeError(f"Expected float or int, got {type(self.liquidity)}")
            )
        if not isinstance(self.holders, int):
            raise AnalysisError(
                message="Tipo de dado inválido para análise",
                metric="holders",
                dataset=f"Memecoin: {self.symbol}",
                algorithm="type_validation",
                details=f"O atributo 'holders' deve ser um inteiro. Recebido: {type(self.holders)}",
                cause=TypeError(f"Expected int, got {type(self.holders)}")
            )
        if not isinstance(self.social_mentions, int):
            raise AnalysisError(
                message="Tipo de dado inválido para análise",
                metric="social_mentions",
                dataset=f"Memecoin: {self.symbol}",
                algorithm="type_validation",
                details=f"O atributo 'social_mentions' deve ser um inteiro. Recebido: {type(self.social_mentions)}",
                cause=TypeError(f"Expected int, got {type(self.social_mentions)}")
            )
        if self.sentiment_score is not None and not isinstance(self.sentiment_score, (float, int)):
            raise AnalysisError(
                message="Tipo de dado inválido para análise",
                metric="sentiment_score",
                dataset=f"Memecoin: {self.symbol}",
                algorithm="type_validation",
                details=f"O atributo 'sentiment_score' deve ser um número (float ou int) ou None. Recebido: {type(self.sentiment_score)}",
                cause=TypeError(f"Expected float, int or None, got {type(self.sentiment_score)}")
            )

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