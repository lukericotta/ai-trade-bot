"""Main AI Trading Bot implementation"""

import asyncio
import logging
from typing import Dict, List
from datetime import datetime

from .config import Config
from .alpaca_client import AlpacaClient
from .account_manager import AccountManager
from .data_analyzer import DataAnalyzer
from .trading_engine import TradingEngine
from .risk_manager import RiskManager
from .logger import setup_logger

class AITradingBot:
    """Main AI Trading Bot class"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = setup_logger(config.log_level, config.log_file)
        
        # Initialize components
        self.alpaca_client = AlpacaClient(config)
        self.account_manager = AccountManager(self.alpaca_client)
        self.data_analyzer = DataAnalyzer(self.alpaca_client)
        self.trading_engine = TradingEngine(self.alpaca_client, config)
        self.risk_manager = RiskManager(config)
        
        self.is_running = False
        self._tasks: List[asyncio.Task] = []
    
    async def initialize(self) -> bool:
        """Initialize the trading bot"""
        try:
            self.logger.info("Initializing AI Trading Bot...")
            
            # Verify API connection
            if not await self.alpaca_client.verify_connection():
                self.logger.error("Failed to connect to Alpaca API")
                return False
            
            # Load account information
            account_info = await self.account_manager.get_account_info()
            self.logger.info(f"Account loaded: {account_info['id']}")
            
            # Initialize data analyzer
            await self.data_analyzer.initialize()
            
            self.logger.info("AI Trading Bot initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize bot: {e}")
            return False
    
    async def start(self):
        """Start the trading bot"""
        if not await self.initialize():
            return
        
        self.is_running = True
        self.logger.info("Starting AI Trading Bot...")
        
        # Start background tasks
        self._tasks = [
            asyncio.create_task(self._data_collection_loop()),
            asyncio.create_task(self._analysis_loop()),
            asyncio.create_task(self._trading_loop()),
            asyncio.create_task(self._monitoring_loop())
        ]
        
        # Wait for all tasks
        await asyncio.gather(*self._tasks, return_exceptions=True)
    
    async def stop(self):
        """Stop the trading bot gracefully"""
        self.logger.info("Stopping AI Trading Bot...")
        self.is_running = False
        
        # Cancel all tasks
        for task in self._tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self._tasks, return_exceptions=True)
        
        self.logger.info("AI Trading Bot stopped")
    
    async def _data_collection_loop(self):
        """Continuous data collection loop"""
        while self.is_running:
            try:
                await self.data_analyzer.collect_market_data()
                await asyncio.sleep(self.config.data_refresh_interval)
            except Exception as e:
                self.logger.error(f"Data collection error: {e}")
                await asyncio.sleep(10)
    
    async def _analysis_loop(self):
        """Market analysis loop"""
        while self.is_running:
            try:
                signals = await self.data_analyzer.analyze_market()
                await self.trading_engine.process_signals(signals)
                await asyncio.sleep(self.config.analysis_interval)
            except Exception as e:
                self.logger.error(f"Analysis error: {e}")
                await asyncio.sleep(30)
    
    async def _trading_loop(self):
        """Trading execution loop"""
        while self.is_running:
            try:
                # Check for trading opportunities
                trades = await self.trading_engine.get_pending_trades()
                
                for trade in trades:
                    # Risk management check
                    if await self.risk_manager.validate_trade(trade):
                        await self.trading_engine.execute_trade(trade)
                    else:
                        self.logger.warning(f"Trade rejected by risk manager: {trade}")
                
                await asyncio.sleep(5)  # Check every 5 seconds
            except Exception as e:
                self.logger.error(f"Trading error: {e}")
                await asyncio.sleep(10)
    
    async def _monitoring_loop(self):
        """Portfolio monitoring and position management"""
        while self.is_running:
            try:
                # Monitor existing positions
                positions = await self.account_manager.get_positions()
                
                for position in positions:
                    # Check stop loss and take profit
                    await self.risk_manager.check_position_limits(position)
                
                # Update account metrics
                await self.account_manager.update_metrics()
                
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                self.logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(30)