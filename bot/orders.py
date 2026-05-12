"""
High-level order placement logic.

This layer sits between the CLI and the raw BinanceClient, combining
validation, logging, and response formatting into clean, reusable helpers.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any, Dict, Optional

from .client import BinanceAPIError, BinanceClient
from .validators import (
    validate_order_type,
    validate_price,
    validate_quantity,
    validate_side,
    validate_stop_price,
    validate_symbol,
)

logger = logging.getLogger("trading_bot.orders")


# ---------------------------------------------------------------------------
# Response formatting
# ---------------------------------------------------------------------------

def format_order_response(response: Dict[str, Any]) -> str:
    """Return a human-readable summary of an order response dict."""
    lines = [
        "┌─ Order Confirmation ───────────────────────────────",
        f"│  Order ID   : {response.get('orderId', 'N/A')}",
        f"│  Symbol     : {response.get('symbol', 'N/A')}",
        f"│  Side       : {response.get('side', 'N/A')}",
        f"│  Type       : {response.get('type', 'N/A')}",
        f"│  Status     : {response.get('status', 'N/A')}",
        f"│  Orig Qty   : {response.get('origQty', 'N/A')}",
        f"│  Executed   : {response.get('executedQty', 'N/A')}",
        f"│  Avg Price  : {response.get('avgPrice', 'N/A')}",
        f"│  Price      : {response.get('price', 'N/A')}",
        f"│  Stop Price : {response.get('stopPrice', 'N/A')}",
        f"│  Time InFrc : {response.get('timeInForce', 'N/A')}",
        f"│  Client OID : {response.get('clientOrderId', 'N/A')}",
        f"│  Created At : {response.get('updateTime', 'N/A')} (ms epoch)",
        "└────────────────────────────────────────────────────",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Core order function
# ---------------------------------------------------------------------------

def place_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    order_type: str,
    quantity: str | float,
    price: Optional[str | float] = None,
    stop_price: Optional[str | float] = None,
    time_in_force: str = "GTC",
    reduce_only: bool = False,
) -> Dict[str, Any]:
    """
    Validate inputs and place an order via the BinanceClient.

    Returns the raw API response dict on success.
    Raises ValueError for invalid inputs or BinanceAPIError for API failures.
    """

    # --- Validate ---
    symbol = validate_symbol(symbol)
    side = validate_side(side)
    order_type = validate_order_type(order_type)
    qty = validate_quantity(quantity)
    lmt_price = validate_price(price, order_type)
    stp_price = validate_stop_price(stop_price, order_type)

    # --- Print request summary ---
    _print_request_summary(symbol, side, order_type, qty, lmt_price, stp_price, time_in_force)

    # --- Log request ---
    logger.info(
        "Order request | symbol=%s side=%s type=%s qty=%s price=%s stopPrice=%s tif=%s",
        symbol, side, order_type, qty, lmt_price, stp_price, time_in_force,
    )

    try:
        response = client.place_order(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=qty,
            price=lmt_price,
            stop_price=stp_price,
            time_in_force=time_in_force,
            reduce_only=reduce_only,
        )
    except BinanceAPIError as exc:
        logger.error("Order failed: %s", exc)
        raise
    except Exception as exc:
        logger.error("Unexpected error placing order: %s", exc, exc_info=True)
        raise

    # --- Log and pretty-print response ---
    logger.info("Order response | %s", response)
    print("\n" + format_order_response(response))
    print("\n✅  Order placed successfully!\n")

    return response


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _print_request_summary(
    symbol: str,
    side: str,
    order_type: str,
    quantity: Decimal,
    price: Optional[Decimal],
    stop_price: Optional[Decimal],
    time_in_force: str,
) -> None:
    side_arrow = "▲ BUY " if side == "BUY" else "▼ SELL"
    lines = [
        "\n┌─ Order Request ────────────────────────────────────",
        f"│  Symbol     : {symbol}",
        f"│  Side       : {side_arrow}",
        f"│  Type       : {order_type}",
        f"│  Quantity   : {quantity}",
    ]
    if price is not None:
        lines.append(f"│  Price      : {price}")
    if stop_price is not None:
        lines.append(f"│  Stop Price : {stop_price}")
    if order_type != "MARKET":
        lines.append(f"│  TIF        : {time_in_force}")
    lines.append("└────────────────────────────────────────────────────")
    print("\n".join(lines))
