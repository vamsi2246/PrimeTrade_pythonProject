from typing import Optional


class TradingBotError(Exception):
    """Base exception for all trading bot errors."""
    pass


class ConfigError(TradingBotError):
    """Raised when configuration is missing or invalid."""
    pass


class ValidationError(TradingBotError):
    """Raised when validation of input parameters (e.g. symbol, side, qty) fails."""
    pass


class NetworkError(TradingBotError):
    """Raised when network requests fail or timeout."""
    pass


class BinanceAPIError(TradingBotError):
    """Raised when Binance API returns an error status code or failure response."""

    def __init__(self, message: str, status_code: Optional[int] = None, error_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code

    def __str__(self):
        code_str = f" [Code: {self.error_code}]" if self.error_code else ""
        status_str = f" (HTTP {self.status_code})" if self.status_code else ""
        return f"{super().__str__()}{code_str}{status_str}"


class OrderPlacementError(TradingBotError):
    """Raised when an order fails to place or fill."""
    pass
