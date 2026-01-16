import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import alpaca_trade_api as tradeapi
from alpaca_trade_api.rest import APIError
import logging

class AccountManager:
    """
    Manages portfolio and account information for the AI Trading Bot.
    Handles account balance, positions, buying power, and portfolio metrics.
    """
    
    def __init__(self, alpaca_client: tradeapi.REST, config):
        self.client = alpaca_client
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Cache for account data to minimize API calls
        self._account_cache = {}
        self._positions_cache = {}
        self._portfolio_history = []
        
        # Thread safety
        self._lock = threading.RLock()
        self._last_update = None
        self._cache_ttl = 30  # seconds
        
        # Account metrics
        self.initial_equity = None
        self.current_equity = None
        self.total_pl = 0.0
        self.day_pl = 0.0
        
    def initialize(self) -> bool:
        """
        Initialize the account manager and validate account access.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            # Test API connection and get initial account data
            account = self.client.get_account()
            
            with self._lock:
                self._account_cache = {
                    'equity': float(account.equity),
                    'buying_power': float(account.buying_power),
                    'cash': float(account.cash),
                    'portfolio_value': float(account.portfolio_value),
                    'day_trade_count': int(account.day_trade_count),
                    'pattern_day_trader': account.pattern_day_trader,
                    'account_blocked': account.account_blocked,
                    'trade_suspended': account.trade_suspended,
                    'last_updated': datetime.now()
                }
                
                # Set initial equity for P&L calculations
                if self.initial_equity is None:
                    self.initial_equity = float(account.equity)
                
                self.current_equity = float(account.equity)
                
            # Load positions
            self._update_positions_cache()
            
            self.logger.info(f"Account Manager initialized. Equity: ${self.current_equity:,.2f}")
            return True
            
        except APIError as e:
            self.logger.error(f"Failed to initialize Account Manager: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error during initialization: {e}")
            return False
    
    def get_account_info(self, force_refresh: bool = False) -> Dict:
        """
        Get current account information with caching.
        
        Args:
            force_refresh: Force refresh from API ignoring cache
            
        Returns:
            Dict: Account information dictionary
        """
        with self._lock:
            # Check if cache is still valid
            if (not force_refresh and 
                self._last_update and 
                (datetime.now() - self._last_update).seconds < self._cache_ttl):
                return self._account_cache.copy()
        
        try:
            account = self.client.get_account()
            
            with self._lock:
                self._account_cache.update({
                    'equity': float(account.equity),
                    'buying_power': float(account.buying_power),
                    'cash': float(account.cash),
                    'portfolio_value': float(account.portfolio_value),
                    'day_trade_count': int(account.day_trade_count),
                    'pattern_day_trader': account.pattern_day_trader,
                    'account_blocked': account.account_blocked,
                    'trade_suspended': account.trade_suspended,
                    'last_updated': datetime.now()
                })
                
                self.current_equity = float(account.equity)
                self._last_update = datetime.now()
                
            return self._account_cache.copy()
            
        except APIError as e:
            self.logger.error(f"Failed to get account info: {e}")
            return self._account_cache.copy() if self._account_cache else {}
    
    def get_buying_power(self) -> float:
        """
        Get available buying power.
        
        Returns:
            float: Available buying power
        """
        account_info = self.get_account_info()
        return account_info.get('buying_power', 0.0)
    
    def get_portfolio_value(self) -> float:
        """
        Get current portfolio value.
        
        Returns:
            float: Total portfolio value
        """
        account_info = self.get_account_info()
        return account_info.get('portfolio_value', 0.0)
    
    def get_cash_balance(self) -> float:
        """
        Get available cash balance.
        
        Returns:
            float: Available cash
        """
        account_info = self.get_account_info()
        return account_info.get('cash', 0.0)
    
    def get_positions(self, force_refresh: bool = False) -> Dict[str, Dict]:
        """
        Get current positions with caching.
        
        Args:
            force_refresh: Force refresh from API
            
        Returns:
            Dict: Dictionary of positions keyed by symbol
        """
        if force_refresh or not self._positions_cache:
            self._update_positions_cache()
        
        with self._lock:
            return self._positions_cache.copy()
    
    def _update_positions_cache(self):
        """
        Update the positions cache from the API.
        """
        try:
            positions = self.client.list_positions()
            
            with self._lock:
                self._positions_cache.clear()
                
                for position in positions:
                    self._positions_cache[position.symbol] = {
                        'symbol': position.symbol,
                        'qty': float(position.qty),
                        'side': position.side,
                        'market_value': float(position.market_value),
                        'cost_basis': float(position.cost_basis),
                        'unrealized_pl': float(position.unrealized_pl),
                        'unrealized_plpc': float(position.unrealized_plpc),
                        'avg_entry_price': float(position.avg_entry_price),
                        'current_price': float(position.current_price)
                    }
                    
        except APIError as e:
            self.logger.error(f"Failed to update positions: {e}")
    
    def get_position(self, symbol: str) -> Optional[Dict]:
        """
        Get position for a specific symbol.
        
        Args:
            symbol: Stock/crypto symbol
            
        Returns:
            Dict or None: Position information or None if no position
        """
        positions = self.get_positions()
        return positions.get(symbol)
    
    def has_position(self, symbol: str) -> bool:
        """
        Check if we have a position in the given symbol.
        
        Args:
            symbol: Stock/crypto symbol
            
        Returns:
            bool: True if position exists
        """
        return symbol in self.get_positions()
    
    def calculate_position_size(self, symbol: str, price: float, 
                              risk_percent: Optional[float] = None) -> int:
        """
        Calculate appropriate position size based on risk management rules.
        
        Args:
            symbol: Stock/crypto symbol
            price: Current price per share
            risk_percent: Risk percentage (defaults to config)
            
        Returns:
            int: Number of shares to buy
        """
        if risk_percent is None:
            risk_percent = self.config.risk_tolerance
        
        buying_power = self.get_buying_power()
        portfolio_value = self.get_portfolio_value()
        
        # Calculate maximum position size based on risk tolerance
        max_position_value = portfolio_value * self.config.max_position_size
        risk_position_value = portfolio_value * risk_percent
        
        # Use the smaller of the two limits
        max_investment = min(max_position_value, risk_position_value, buying_power)
        
        if max_investment <= 0 or price <= 0:
            return 0
        
        # Calculate shares (rounded down)
        shares = int(max_investment / price)
        
        self.logger.debug(f"Position size calculation for {symbol}: "
                         f"Price: ${price}, Max Investment: ${max_investment}, "
                         f"Shares: {shares}")
        
        return shares
    
    def calculate_pl_metrics(self) -> Dict[str, float]:
        """
        Calculate profit/loss metrics.
        
        Returns:
            Dict: P&L metrics including total and daily P&L
        """
        account_info = self.get_account_info()
        current_equity = account_info.get('equity', 0.0)
        
        if self.initial_equity:
            total_pl = current_equity - self.initial_equity
            total_pl_percent = (total_pl / self.initial_equity) * 100
        else:
            total_pl = 0.0
            total_pl_percent = 0.0
        
        # Get day P&L from positions
        positions = self.get_positions()
        day_pl = sum(pos.get('unrealized_pl', 0.0) for pos in positions.values())
        
        return {
            'total_pl': total_pl,
            'total_pl_percent': total_pl_percent,
            'day_pl': day_pl,
            'current_equity': current_equity,
            'initial_equity': self.initial_equity or 0.0
        }
    
    def is_day_trading_restricted(self) -> bool:
        """
        Check if account is restricted from day trading.
        
        Returns:
            bool: True if day trading is restricted
        """
        account_info = self.get_account_info()
        
        # Check if account is blocked or trade suspended
        if (account_info.get('account_blocked', True) or 
            account_info.get('trade_suspended', True)):
            return True
        
        # Check PDT rule (Pattern Day Trader)
        equity = account_info.get('equity', 0.0)
        day_trade_count = account_info.get('day_trade_count', 0)
        
        # If equity < $25k and we've made 3+ day trades in 5 days
        if equity < 25000 and day_trade_count >= 3:
            return True
        
        return False
    
    def get_portfolio_summary(self) -> Dict:
        """
        Get comprehensive portfolio summary.
        
        Returns:
            Dict: Complete portfolio summary
        """
        account_info = self.get_account_info(force_refresh=True)
        positions = self.get_positions(force_refresh=True)
        pl_metrics = self.calculate_pl_metrics()
        
        return {
            'account_info': account_info,
            'positions': positions,
            'position_count': len(positions),
            'pl_metrics': pl_metrics,
            'trading_restricted': self.is_day_trading_restricted(),
            'timestamp': datetime.now().isoformat()
        }
    
    def log_portfolio_status(self):
        """
        Log current portfolio status for monitoring.
        """
        try:
            summary = self.get_portfolio_summary()
            account = summary['account_info']
            pl = summary['pl_metrics']
            
            self.logger.info(
                f"Portfolio Status - Equity: ${account.get('equity', 0):,.2f}, "
                f"Buying Power: ${account.get('buying_power', 0):,.2f}, "
                f"Positions: {summary['position_count']}, "
                f"Total P&L: ${pl['total_pl']:,.2f} ({pl['total_pl_percent']:.2f}%), "
                f"Day P&L: ${pl['day_pl']:,.2f}"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to log portfolio status: {e}")
    
    def cleanup(self):
        """
        Cleanup resources and connections.
        """
        with self._lock:
            self._account_cache.clear()
            self._positions_cache.clear()
            self._portfolio_history.clear()
        
        self.logger.info("Account Manager cleanup completed")