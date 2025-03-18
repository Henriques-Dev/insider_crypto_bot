"""
Pacote analysis do Insider Crypto Bot.

Integra dados de APIs descentralizadas e sociais para análise combinada.
"""

from .dex_api import DexAPI
from .social_api import SocialAPI
from .analysis_logic import MarketAnalyzer

__all__ = ["DexAPI", "SocialAPI", "MarketAnalyzer"]