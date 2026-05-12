"""trading_bot.bot — Binance Futures Testnet trading bot package."""

from .client import BinanceAPIError, BinanceClient
from .logging_config import setup_logging
from .orders import place_order
from .validators import (
    validate_order_type,
    validate_price,
    validate_quantity,
    validate_side,
    validate_stop_price,
    validate_symbol,
)

__all__ = [
    "BinanceAPIError",
    "BinanceClient",
    "setup_logging",
    "place_order",
    "validate_order_type",
    "validate_price",
    "validate_quantity",
    "validate_side",
    "validate_stop_price",
    "validate_symbol",
]
