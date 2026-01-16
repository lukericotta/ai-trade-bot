#!/usr/bin/env python3
"""
AI Trading Bot - Main Entry Point

This is the main entry point for the AI trading bot that uses the Alpaca Trade API
to execute automated trading strategies for stocks and crypto.

Usage:
    python main.py --config config/default_config.json
    python main.py --help

The bot will run continuously in the background, analyzing market data and
executing trades based on the configured strategies.
"""

import argparse
import logging
import signal
import sys
import time
from pathlib import Path
import asyncio
from typing import Optional

# Import our trading bot components
try:
    from config_manager import ConfigManager, ConfigurationError
except ImportError as e:
    print(f"Error importing configuration manager: {e}")
    print("Please ensure all required modules are installed and available.")
    sys.exit(1)

# Set up logging
def setup_logging(log_level: str = 'INFO'):
    """Set up logging with proper directory creation."""
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / 'trading_bot.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()


class TradingBot:
    """
    Main trading bot class that orchestrates all trading activities.
    """
    
    def __init__(self, config_path: str):
        self.config_manager = ConfigManager(config_path)
        self.running = False
        self.account_manager = None
        self.data_manager = None
        self.strategy_manager = None
        self.risk_manager = None
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.stop()
    
    async def initialize(self):
        """
        Initialize all bot components.
        """
        try:
            logger.info("Initializing trading bot components...")
            
            # TODO: Initialize components as they are developed
            # self.account_manager = AccountManager(self.config_manager)
            # self.data_manager = DataManager(self.config_manager)
            # self.strategy_manager = StrategyManager(self.config_manager)
            # self.risk_manager = RiskManager(self.config_manager)
            
            # Validate configuration
            self.config_manager.validate_config()
            
            # Check if API keys are configured
            config = self.config_manager.current_config
            if not config.get('alpaca', {}).get('api_key'):
                raise ConfigurationError("Alpaca API key not configured")
            
            logger.info("Trading bot initialized successfully")
            
        except ConfigurationError as e:
            logger.error(f"Configuration error during initialization: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during initialization: {e}")
            raise
    
    async def run(self):
        """
        Main bot execution loop.
        """
        try:
            await self.initialize()
            self.running = True
            
            logger.info("Starting trading bot main loop...")
            
            while self.running:
                try:
                    # Main trading logic will go here
                    # For now, just log that we're running
                    logger.info("Bot is running... (main trading logic to be implemented)")
                    
                    # TODO: Implement main trading loop
                    # - Fetch market data
                    # - Analyze signals
                    # - Execute risk management
                    # - Place trades if conditions are met
                    # - Update portfolio state
                    
                    # Sleep for a short interval before next iteration
                    await asyncio.sleep(10)  # 10 seconds between iterations
                    
                except Exception as e:
                    logger.error(f"Error in main trading loop: {e}")
                    # Continue running unless it's a critical error
                    await asyncio.sleep(30)  # Wait longer on errors
            
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received, shutting down...")
        except Exception as e:
            logger.error(f"Critical error in main run loop: {e}")
            raise
        finally:
            await self.cleanup()
    
    def stop(self):
        """
        Stop the trading bot gracefully.
        """
        logger.info("Stopping trading bot...")
        self.running = False
    
    async def cleanup(self):
        """
        Clean up resources before shutdown.
        """
        logger.info("Cleaning up trading bot resources...")
        # TODO: Implement cleanup logic
        # - Close any open positions if configured to do so
        # - Save state snapshots
        # - Close database connections
        # - Clean up async tasks
        logger.info("Trading bot shutdown complete")


def parse_arguments():
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser(
        description="AI Trading Bot - Automated trading with Alpaca API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python main.py --config config/aggressive_config.json
    python main.py --config config/conservative_config.json --log-level DEBUG
        """
    )
    
    parser.add_argument(
        '--config', '-c',
        default='config/default_config.json',
        help='Path to configuration file (default: config/default_config.json)'
    )
    
    parser.add_argument(
        '--log-level', '-l',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='INFO',
        help='Set the logging level (default: INFO)'
    )
    
    parser.add_argument(
        '--dry-run', '-d',
        action='store_true',
        help='Run in dry-run mode (no actual trades will be executed)'
    )
    
    return parser.parse_args()


async def main():
    """
    Main entry point for the trading bot.
    """
    # Ensure we're in the correct working directory
    script_dir = Path(__file__).parent.absolute()
    if script_dir != Path.cwd():
        logger.info(f"Changing working directory to: {script_dir}")
        import os
        os.chdir(script_dir)
    
    args = parse_arguments()
    
    # Set up logging with the specified level
    global logger
    logger = setup_logging(args.log_level)
    
    # Create necessary directories
    for directory in ['logs', 'config', 'data']:
        Path(directory).mkdir(exist_ok=True)
        logger.debug(f"Ensured directory exists: {directory}")
    
    # Check if config file exists
    config_path = Path(args.config)
    if not config_path.exists():
        logger.error(f"Configuration file not found: {args.config}")
        logger.info("Please create a configuration file or use --config to specify a different path.")
        logger.info("See config/example_config.json for a template.")
        
        # Create a basic config template if config directory exists but file doesn't
        if config_path.parent.exists():
            logger.info(f"Creating basic configuration template at: {args.config}")
            basic_config = {
                "alpaca": {
                    "api_key": "YOUR_ALPACA_API_KEY_HERE",
                    "secret_key": "YOUR_ALPACA_SECRET_KEY_HERE",
                    "base_url": "https://paper-api.alpaca.markets"
                },
                "trading": {
                    "max_positions": 5,
                    "risk_per_trade": 0.02,
                    "stop_loss_percent": 0.05
                },
                "logging": {
                    "level": "INFO"
                }
            }
            try:
                import json
                with open(config_path, 'w') as f:
                    json.dump(basic_config, f, indent=4)
                logger.info(f"Created basic config template. Please edit {args.config} with your actual API keys.")
            except Exception as e:
                logger.error(f"Failed to create config template: {e}")
        
        return 1
    
    if args.dry_run:
        logger.info("Running in DRY-RUN mode - no actual trades will be executed")
    
    try:
        # Create and run the trading bot
        bot = TradingBot(args.config)
        await bot.run()
        return 0
        
    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        return 0
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    # Run the async main function
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nBot stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"Critical startup error: {e}")
        sys.exit(1)