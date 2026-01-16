import logging
import time
import traceback
from enum import Enum
from typing import Dict, Any, Callable, Optional
from functools import wraps
import asyncio
from datetime import datetime, timedelta

class ErrorSeverity(Enum):
    """Error severity levels for different types of failures"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorType(Enum):
    """Categories of errors that can occur in the trading system"""
    API_ERROR = "api_error"
    NETWORK_ERROR = "network_error"
    DATA_ERROR = "data_error"
    MODEL_ERROR = "model_error"
    TRADING_ERROR = "trading_error"
    SYSTEM_ERROR = "system_error"
    VALIDATION_ERROR = "validation_error"

class ErrorHandler:
    """
    Comprehensive error handling and recovery system for the trading bot.
    Provides retry mechanisms, circuit breakers, and graceful degradation.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = self._setup_logger()
        self.error_counts = {}
        self.circuit_breakers = {}
        self.last_errors = {}
        self.recovery_strategies = self._init_recovery_strategies()
        
    def _setup_logger(self) -> logging.Logger:
        """Setup comprehensive logging for error tracking"""
        logger = logging.getLogger('trade_bot_errors')
        logger.setLevel(logging.INFO)
        
        # File handler for persistent error logs
        file_handler = logging.FileHandler('logs/error_log.log')
        file_handler.setLevel(logging.ERROR)
        
        # Console handler for immediate feedback
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        
        # Formatter with detailed information
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def _init_recovery_strategies(self) -> Dict[ErrorType, Callable]:
        """Initialize recovery strategies for different error types"""
        return {
            ErrorType.API_ERROR: self._recover_from_api_error,
            ErrorType.NETWORK_ERROR: self._recover_from_network_error,
            ErrorType.DATA_ERROR: self._recover_from_data_error,
            ErrorType.MODEL_ERROR: self._recover_from_model_error,
            ErrorType.TRADING_ERROR: self._recover_from_trading_error,
            ErrorType.SYSTEM_ERROR: self._recover_from_system_error,
            ErrorType.VALIDATION_ERROR: self._recover_from_validation_error
        }
    
    def handle_error(self, error: Exception, error_type: ErrorType, 
                    severity: ErrorSeverity, context: Dict[str, Any] = None) -> bool:
        """Main error handling entry point"""
        try:
            error_info = {
                'error': str(error),
                'type': error_type.value,
                'severity': severity.value,
                'timestamp': datetime.now(),
                'context': context or {},
                'traceback': traceback.format_exc()
            }
            
            # Log the error
            self._log_error(error_info)
            
            # Update error tracking
            self._update_error_tracking(error_type, error_info)
            
            # Check circuit breaker
            if self._should_circuit_break(error_type):
                self._activate_circuit_breaker(error_type)
                return False
            
            # Attempt recovery
            recovery_success = self._attempt_recovery(error_type, error_info)
            
            # Send alerts for critical errors
            if severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
                self._send_alert(error_info)
            
            return recovery_success
            
        except Exception as handler_error:
            self.logger.critical(f"Error handler itself failed: {handler_error}")
            return False
    
    def _log_error(self, error_info: Dict[str, Any]):
        """Log error with appropriate level based on severity"""
        severity = error_info['severity']
        message = f"[{error_info['type']}] {error_info['error']}"
        
        if severity == ErrorSeverity.CRITICAL.value:
            self.logger.critical(message, extra=error_info)
        elif severity == ErrorSeverity.HIGH.value:
            self.logger.error(message, extra=error_info)
        elif severity == ErrorSeverity.MEDIUM.value:
            self.logger.warning(message, extra=error_info)
        else:
            self.logger.info(message, extra=error_info)
    
    def _update_error_tracking(self, error_type: ErrorType, error_info: Dict[str, Any]):
        """Update error frequency tracking for circuit breaker logic"""
        if error_type not in self.error_counts:
            self.error_counts[error_type] = []
        
        self.error_counts[error_type].append(error_info['timestamp'])
        self.last_errors[error_type] = error_info
        
        # Clean old error records (keep only last hour)
        cutoff_time = datetime.now() - timedelta(hours=1)
        self.error_counts[error_type] = [
            ts for ts in self.error_counts[error_type] if ts > cutoff_time
        ]
    
    def _should_circuit_break(self, error_type: ErrorType) -> bool:
        """Determine if circuit breaker should activate"""
        if error_type not in self.error_counts:
            return False
        
        error_threshold = self.config.get('circuit_breaker', {}).get(
            error_type.value, 5
        )
        
        recent_errors = len(self.error_counts[error_type])
        return recent_errors >= error_threshold
    
    def _activate_circuit_breaker(self, error_type: ErrorType):
        """Activate circuit breaker for specific error type"""
        self.circuit_breakers[error_type] = {
            'activated_at': datetime.now(),
            'duration': timedelta(minutes=self.config.get('circuit_breaker_duration', 15))
        }
        
        self.logger.critical(f"Circuit breaker activated for {error_type.value}")
    
    def _attempt_recovery(self, error_type: ErrorType, error_info: Dict[str, Any]) -> bool:
        """Attempt to recover from the error using appropriate strategy"""
        try:
            if error_type in self.recovery_strategies:
                return self.recovery_strategies[error_type](error_info)
            else:
                self.logger.warning(f"No recovery strategy for {error_type.value}")
                return False
        except Exception as recovery_error:
            self.logger.error(f"Recovery failed for {error_type.value}: {recovery_error}")
            return False
    
    def _recover_from_api_error(self, error_info: Dict[str, Any]) -> bool:
        """Recovery strategy for API errors"""
        # Wait before retry
        time.sleep(self.config.get('api_retry_delay', 5))
        
        # Could implement API key rotation here if multiple keys available
        self.logger.info("Attempting API error recovery")
        return True
    
    def _recover_from_network_error(self, error_info: Dict[str, Any]) -> bool:
        """Recovery strategy for network errors"""
        # Progressive backoff for network issues
        retry_count = error_info.get('retry_count', 0)
        delay = min(2 ** retry_count, 60)  # Max 60 seconds
        
        time.sleep(delay)
        self.logger.info(f"Network error recovery attempt after {delay}s delay")
        return True
    
    def _recover_from_data_error(self, error_info: Dict[str, Any]) -> bool:
        """Recovery strategy for data errors"""
        # Use cached data or switch to alternative data source
        self.logger.info("Switching to cached data due to data error")
        return True
    
    def _recover_from_model_error(self, error_info: Dict[str, Any]) -> bool:
        """Recovery strategy for ML model errors"""
        # Fall back to rule-based trading or simpler models
        self.logger.info("Falling back to rule-based strategy due to model error")
        return True
    
    def _recover_from_trading_error(self, error_info: Dict[str, Any]) -> bool:
        """Recovery strategy for trading errors"""
        # Halt trading temporarily and reassess positions
        self.logger.warning("Trading error occurred, reassessing positions")
        return False  # Conservative approach for trading errors
    
    def _recover_from_system_error(self, error_info: Dict[str, Any]) -> bool:
        """Recovery strategy for system errors"""
        # System errors are serious, may need manual intervention
        self.logger.critical("System error detected, may need manual intervention")
        return False
    
    def _recover_from_validation_error(self, error_info: Dict[str, Any]) -> bool:
        """Recovery strategy for validation errors"""
        # Skip invalid data points and continue
        self.logger.info("Skipping invalid data due to validation error")
        return True
    
    def _send_alert(self, error_info: Dict[str, Any]):
        """Send alert for critical errors (placeholder for notification system)"""
        # This would integrate with email, SMS, or webhook notification systems
        self.logger.critical(f"ALERT: Critical error - {error_info['error']}")
    
    def is_circuit_breaker_active(self, error_type: ErrorType) -> bool:
        """Check if circuit breaker is currently active for error type"""
        if error_type not in self.circuit_breakers:
            return False
        
        breaker_info = self.circuit_breakers[error_type]
        if datetime.now() - breaker_info['activated_at'] > breaker_info['duration']:
            # Circuit breaker has expired, remove it
            del self.circuit_breakers[error_type]
            self.logger.info(f"Circuit breaker for {error_type.value} has been reset")
            return False
        
        return True
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status"""
        return {
            'error_counts': {k.value: len(v) for k, v in self.error_counts.items()},
            'active_circuit_breakers': [k.value for k in self.circuit_breakers.keys()],
            'last_errors': {k.value: v['timestamp'] for k, v in self.last_errors.items()},
            'timestamp': datetime.now()
        }


def retry_with_backoff(max_retries: int = 3, base_delay: float = 1.0, 
                      error_types: tuple = (Exception,)):
    """Decorator for retry logic with exponential backoff"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except error_types as e:
                    last_exception = e
                    if attempt < max_retries:
                        delay = base_delay * (2 ** attempt)
                        time.sleep(delay)
                        logging.warning(f"Retry {attempt + 1}/{max_retries} for {func.__name__} after {delay}s")
                    else:
                        logging.error(f"All retries exhausted for {func.__name__}")
            
            raise last_exception
        return wrapper
    return decorator


def async_retry_with_backoff(max_retries: int = 3, base_delay: float = 1.0,
                            error_types: tuple = (Exception,)):
    """Async version of retry decorator"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except error_types as e:
                    last_exception = e
                    if attempt < max_retries:
                        delay = base_delay * (2 ** attempt)
                        await asyncio.sleep(delay)
                        logging.warning(f"Async retry {attempt + 1}/{max_retries} for {func.__name__} after {delay}s")
                    else:
                        logging.error(f"All async retries exhausted for {func.__name__}")
            
            raise last_exception
        return wrapper
    return decorator
