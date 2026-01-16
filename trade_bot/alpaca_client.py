"""Alpaca API client wrapper"""

import alpaca_trade_api as tradeapi
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from .config import Config

class AlpacaClient:
    """Wrapper for Alpaca Trade API"""
    
    def __init__(self, config: Config):
        self.config = config
        self.api = tradeapi.REST(
            config.alpaca_api_key,
            config.alpaca_secret_key,
            config.base_url,
            api_version='v2'
        )
    
    async def verify_connection(self) -> bool:
        """Verify API connection"""
        try:
            account = self.api.get_account()
            return account.status == 'ACTIVE'
        except Exception:
            return False
    
    def get_account(self) -> Dict:
        """Get account information"""
        account = self.api.get_account()
        return {
            'id': account.id,
            'equity': float(account.equity),
            'cash': float(account.cash),
            'buying_power': float(account.buying_power),
            'day_trade_buying_power': float(account.day_trade_buying_power),
            'status': account.status
        }
    
    def get_positions(self) -> List[Dict]:
        """Get current positions"""
        positions = self.api.list_positions()
        return [
            {
                'symbol': pos.symbol,
                'qty': int(pos.qty),
                'market_value': float(pos.market_value),
                'cost_basis': float(pos.cost_basis),
                'unrealized_pl': float(pos.unrealized_pl),
                'unrealized_plpc': float(pos.unrealized_plpc),
                'side': pos.side
            }
            for pos in positions
        ]
    
    def submit_order(
        self,
        symbol: str,
        qty: int,
        side: str,
        type: str = 'market',
        time_in_force: str = 'day',
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None
    ) -> Dict:
        """Submit a trade order"""
        order = self.api.submit_order(
            symbol=symbol,
            qty=qty,
            side=side,
            type=type,
            time_in_force=time_in_force,
            limit_price=limit_price,
            stop_price=stop_price
        )
        return {
            'id': order.id,
            'symbol': order.symbol,
            'qty': int(order.qty),
            'side': order.side,
            'type': order.type,
            'status': order.status,
            'submitted_at': order.submitted_at
        }
    
    def get_bars(
        self,
        symbols: List[str],
        timeframe: str = '1Min',
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 1000
    ) -> Dict:
        """Get historical price data"""
        if start is None:
            start = datetime.now() - timedelta(days=7)
        
        bars = self.api.get_bars(
            symbols,
            timeframe,
            start=start.isoformat(),
            end=end.isoformat() if end else None,
            limit=limit
        )
        
        return bars.df.to_dict()
    
    def get_latest_trades(self, symbols: List[str]) -> Dict:
        """Get latest trade data for symbols"""
        trades = self.api.get_latest_trades(symbols)
        return {symbol: trade._raw for symbol, trade in trades.items()}