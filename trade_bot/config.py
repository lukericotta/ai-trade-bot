"""Configuration management for the trading bot"""

import os
from typing import Optional
from dataclasses import dataclass

@dataclass
class Config:
    """Trading bot configuration"""
    # Alpaca API credentials
    alpaca_api_key: Optional[str] = None
    alpaca_secret_key: Optional[str] = None
    base_url: str = 'https://paper-api.alpaca.markets'  # Paper trading by default
    
    # Trading parameters
    paper_trading: bool = True
    risk_tolerance: float = 0.02  # 2% risk per trade
    max_position_size: float = 0.1  # 10% of portfolio per position
    stop_loss_percentage: float = 0.05  # 5% stop loss
    take_profit_percentage: float = 0.15  # 15% take profit
    
    # Data and analysis
    data_refresh_interval: int = 60  # seconds
    analysis_interval: int = 300  # 5 minutes
    
    # Logging
    log_level: str = 'INFO'
    log_file: str = 'trading_bot.log'
    
    @classmethod
    def from_env(cls) -> 'Config':
        """Load configuration from environment variables"""
        return cls(
            alpaca_api_key=os.getenv('ALPACA_API_KEY'),
            alpaca_secret_key=os.getenv('ALPACA_SECRET_KEY'),
            base_url=os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets'),
            paper_trading=os.getenv('PAPER_TRADING', 'true').lower() == 'true'
        )