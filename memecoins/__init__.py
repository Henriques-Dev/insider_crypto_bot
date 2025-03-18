"""
Pacote memecoins do Insider Crypto Bot.

Este pacote gerencia a lista de memecoins, aplica filtros e análises,
e identifica oportunidades de compra e venda.
"""

from .memecoin import Memecoin
from .memecoin_manager import MemecoinManager

# Expõe as classes principais
__all__ = ["Memecoin", "MemecoinManager"]