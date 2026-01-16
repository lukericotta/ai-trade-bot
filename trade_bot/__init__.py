"""AI Trading Bot Package"""

__version__ = '1.0.0'
__author__ = 'AI Trading Bot Team'

from .bot import AITradingBot
from .config import Config

__all__ = ['AITradingBot', 'Config']