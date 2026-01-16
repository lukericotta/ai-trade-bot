# AI Trading Bot

An automated AI trading bot that uses the Alpaca Trade API to trade stocks and cryptocurrency with the goal of maximizing profits through intelligent analysis and automated execution.

## Features

- **Fully Automated Trading**: Runs continuously in the background
- **Multi-Asset Support**: Trade both stocks and cryptocurrency
- **Risk Management**: Built-in risk controls and position sizing
- **Strategy Configuration**: Support for multiple trading strategies
- **Real-time Analysis**: Continuous market data analysis and signal generation
- **Robust Error Handling**: Graceful error recovery and system resilience

## Quick Start

### Prerequisites

- Python 3.8 or higher
- Alpaca Trading Account with API keys
- Required Python packages (see requirements.txt)

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd trade_bot
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create your configuration file:
   ```bash
   cp config/example_config.json config/my_config.json
   # Edit config/my_config.json with your API keys and strategy settings
   ```

### Running the Bot

#### Basic Usage

```bash
# Start the bot with default configuration
python main.py

# Use a specific configuration file
python main.py --config config/my_config.json

# Run in dry-run mode (no actual trades)
python main.py --dry-run

# Enable debug logging
python main.py --log-level DEBUG
```

#### Command Line Options

- `--config`, `-c`: Path to configuration file (default: `config/default_config.json`)
- `--log-level`, `-l`: Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `--dry-run`, `-d`: Run without executing actual trades
- `--help`, `-h`: Show help message

### Configuration

The bot uses JSON configuration files to manage trading strategies and settings. Create your configuration file based on the example:

```json
{
    "alpaca": {
        "api_key": "YOUR_API_KEY",
        "secret_key": "YOUR_SECRET_KEY",
        "base_url": "https://paper-api.alpaca.markets",
        "data_url": "https://data.alpaca.markets"
    },
    "strategies": {
        "momentum": {
            "enabled": true,
            "risk_per_trade": 0.02,
            "max_positions": 5
        }
    },
    "risk_management": {
        "max_portfolio_risk": 0.10,
        "stop_loss_percent": 0.05,
        "take_profit_percent": 0.15
    }
}
```

**Important Security Note**: Never commit your actual API keys to version control. Keep your configuration files secure and consider using environment variables for sensitive data.

## Project Structure

```
trade_bot/
├── main.py                 # Main entry point
├── config_manager.py       # Configuration management
├── config/                 # Configuration files
│   ├── example_config.json
│   └── default_config.json
├── logs/                   # Log files
├── data/                   # Market data and backtest results
├── tests/                  # Unit tests
└── requirements.txt        # Python dependencies
```

## Development Status

🚧 **This project is under active development**

Currently implemented:
- ✅ Configuration management system
- ✅ Main entry point with proper CLI
- ✅ Basic error handling and logging
- ✅ Graceful shutdown handling

In development:
- 🔄 Account management integration
- 🔄 Market data streaming
- 🔄 Trading strategy implementation
- 🔄 Risk management system
- 🔄 Backtesting framework

## Safety Features

- **Dry-run Mode**: Test strategies without risking real money
- **Position Limits**: Configurable limits on position sizes and counts
- **Stop Losses**: Automatic stop-loss orders to limit downside risk
- **Circuit Breakers**: Automatic trading halts on excessive losses
- **API Rate Limiting**: Respects Alpaca API rate limits

## Monitoring and Logs

The bot logs all activities to both console and log files:

- **Log Location**: `logs/trading_bot.log`
- **Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Rotation**: Logs are rotated to prevent excessive disk usage

## Support and Contributing

This is an actively developed project. Please refer to the documentation and configuration examples for guidance on setup and usage.

## Disclaimer

**Trading involves risk of loss. This software is provided for educational and research purposes. Past performance does not guarantee future results. Always test thoroughly in paper trading mode before risking real capital. The authors are not responsible for any financial losses incurred through the use of this software.**

## License

See LICENSE file for details.
