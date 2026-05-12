"""
Input validation helpers for the trading bot.
All public functions raise ValueError with descriptive messages on bad input.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Optional

VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP_LIMIT"}


# ---------------------------------------------------------------------------
# Public validators
# ---------------------------------------------------------------------------


def validate_symbol(symbol: str) -> str:
    """Return uppercased symbol or raise ValueError."""
    symbol = symbol.strip().upper()
    if not symbol or not symbol.isalnum():
        raise ValueError(
            f"Invalid symbol '{symbol}'. Must be alphanumeric (e.g. BTCUSDT)."
        )
    return symbol


def validate_side(side: str) -> str:
    """Return normalised side (BUY|SELL) or raise ValueError."""
    side = side.strip().upper()
    if side not in VALID_SIDES:
        raise ValueError(
            f"Invalid side '{side}'. Allowed values: {', '.join(sorted(VALID_SIDES))}."
        )
    return side


def validate_order_type(order_type: str) -> str:
    """Return normalised order type or raise ValueError."""
    order_type = order_type.strip().upper()
    if order_type not in VALID_ORDER_TYPES:
        raise ValueError(
            f"Invalid order type '{order_type}'. "
            f"Allowed values: {', '.join(sorted(VALID_ORDER_TYPES))}."
        )
    return order_type


def validate_quantity(quantity: str | float) -> Decimal:
    """Return quantity as Decimal or raise ValueError."""
    try:
        qty = Decimal(str(quantity))
    except InvalidOperation:
        raise ValueError(f"Invalid quantity '{quantity}'. Must be a positive number.")
    if qty <= 0:
        raise ValueError(f"Quantity must be greater than zero (got {qty}).")
    return qty


def validate_price(price: Optional[str | float], order_type: str) -> Optional[Decimal]:
    """
    Validate price based on order type.

    - MARKET orders: price must be None (ignored even if provided).
    - LIMIT / STOP_LIMIT orders: price is required and must be positive.
    """
    order_type = order_type.upper()

    if order_type == "MARKET":
        return None  # price is irrelevant for market orders

    if price is None or str(price).strip() == "":
        raise ValueError(f"Price is required for {order_type} orders.")

    try:
        p = Decimal(str(price))
    except InvalidOperation:
        raise ValueError(f"Invalid price '{price}'. Must be a positive number.")
    if p <= 0:
        raise ValueError(f"Price must be greater than zero (got {p}).")
    return p


def validate_stop_price(
    stop_price: Optional[str | float], order_type: str
) -> Optional[Decimal]:
    """Stop price is only required for STOP_LIMIT orders."""
    order_type = order_type.upper()

    if order_type != "STOP_LIMIT":
        return None

    if stop_price is None or str(stop_price).strip() == "":
        raise ValueError("Stop price is required for STOP_LIMIT orders.")

    try:
        sp = Decimal(str(stop_price))
    except InvalidOperation:
        raise ValueError(f"Invalid stop price '{stop_price}'. Must be a positive number.")
    if sp <= 0:
        raise ValueError(f"Stop price must be greater than zero (got {sp}).")
    return sp
