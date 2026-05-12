#!/usr/bin/env python3
"""
cli.py — Command-line interface for the Binance Futures Testnet trading bot.

Usage examples:

  # Market buy
  python cli.py place --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001

  # Limit sell
  python cli.py place --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 70000

  # Stop-limit buy
  python cli.py place --symbol BTCUSDT --side BUY --type STOP_LIMIT \\
      --quantity 0.001 --price 68000 --stop-price 67500

  # Check connectivity
  python cli.py ping

  # Show open orders
  python cli.py open-orders --symbol BTCUSDT
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Optional

from bot.client import BinanceAPIError, BinanceClient
from bot.logging_config import setup_logging
from bot.orders import place_order

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_client(args: argparse.Namespace) -> BinanceClient:
    """Build a BinanceClient from CLI args or environment variables."""
    api_key = getattr(args, "api_key", None) or os.environ.get("BINANCE_TESTNET_API_KEY", "")
    api_secret = getattr(args, "api_secret", None) or os.environ.get("BINANCE_TESTNET_API_SECRET", "")

    if not api_key or not api_secret:
        print(
            "❌  API credentials are required.\n"
            "    Set --api-key / --api-secret flags, or export:\n"
            "      BINANCE_TESTNET_API_KEY=<key>\n"
            "      BINANCE_TESTNET_API_SECRET=<secret>",
            file=sys.stderr,
        )
        sys.exit(1)

    return BinanceClient(api_key=api_key, api_secret=api_secret)


# ---------------------------------------------------------------------------
# Sub-command handlers
# ---------------------------------------------------------------------------


def cmd_ping(args: argparse.Namespace) -> None:
    """Test connectivity to Binance Futures Testnet."""
    import requests

    # /fapi/v1/ping returns {} on success; /fapi/v1/time returns server time
    url = "https://testnet.binancefuture.com/fapi/v1/time"
    try:
        resp = requests.get(url, timeout=10)
        if resp.ok:
            server_time = resp.json().get("serverTime", "N/A")
            print(f"✅  Binance Futures Testnet is reachable. Server time: {server_time} ms")
        else:
            print(f"⚠️   Got HTTP {resp.status_code} from testnet — check your network/VPN.",
                  file=sys.stderr)
            sys.exit(1)
    except requests.exceptions.ConnectionError as exc:
        print(f"❌  Connection error: {exc}", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.Timeout:
        print("❌  Request timed out.", file=sys.stderr)
        sys.exit(1)


def cmd_place(args: argparse.Namespace) -> None:
    """Place a new futures order."""
    client = _get_client(args)

    try:
        place_order(
            client=client,
            symbol=args.symbol,
            side=args.side,
            order_type=args.type,
            quantity=args.quantity,
            price=args.price,
            stop_price=args.stop_price,
            time_in_force=args.time_in_force,
            reduce_only=args.reduce_only,
        )
    except ValueError as exc:
        print(f"\n❌  Validation error: {exc}\n", file=sys.stderr)
        sys.exit(2)
    except BinanceAPIError as exc:
        print(f"\n❌  Binance API error [{exc.code}]: {exc.message}\n", file=sys.stderr)
        sys.exit(3)
    except Exception as exc:
        print(f"\n❌  Unexpected error: {exc}\n", file=sys.stderr)
        sys.exit(4)


def cmd_open_orders(args: argparse.Namespace) -> None:
    """List open orders for a symbol."""
    client = _get_client(args)
    try:
        orders = client.get_open_orders(symbol=args.symbol or None)
        if not orders:
            print("ℹ️   No open orders found.")
            return
        print(json.dumps(orders, indent=2))
    except BinanceAPIError as exc:
        print(f"❌  API error [{exc.code}]: {exc.message}", file=sys.stderr)
        sys.exit(3)


def cmd_account(args: argparse.Namespace) -> None:
    """Print account balances."""
    client = _get_client(args)
    try:
        account = client.get_account()
        assets = [a for a in account.get("assets", []) if float(a.get("walletBalance", 0)) > 0]
        if not assets:
            print("ℹ️   No non-zero balances found.")
        for asset in assets:
            print(
                f"  {asset['asset']:<8} wallet={asset['walletBalance']:<18} "
                f"unrealised PnL={asset.get('unrealizedProfit', '0')}"
            )
    except BinanceAPIError as exc:
        print(f"❌  API error [{exc.code}]: {exc.message}", file=sys.stderr)
        sys.exit(3)


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trading_bot",
        description="Binance Futures Testnet trading bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Global options
    parser.add_argument(
        "--api-key",
        metavar="KEY",
        help="Binance Testnet API key (or set BINANCE_TESTNET_API_KEY env var)",
    )
    parser.add_argument(
        "--api-secret",
        metavar="SECRET",
        help="Binance Testnet API secret (or set BINANCE_TESTNET_API_SECRET env var)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity (default: INFO)",
    )

    sub = parser.add_subparsers(dest="command", metavar="<command>", required=True)

    # --- ping ---
    sub.add_parser("ping", help="Test connectivity to Binance Futures Testnet")

    # --- place ---
    place_p = sub.add_parser("place", help="Place a new futures order")
    place_p.add_argument(
        "--symbol", required=True, metavar="SYMBOL",
        help="Trading pair, e.g. BTCUSDT"
    )
    place_p.add_argument(
        "--side", required=True, choices=["BUY", "SELL"],
        help="Order side"
    )
    place_p.add_argument(
        "--type", required=True, dest="type",
        choices=["MARKET", "LIMIT", "STOP_LIMIT"],
        help="Order type"
    )
    place_p.add_argument(
        "--quantity", required=True, type=float, metavar="QTY",
        help="Order quantity in base asset"
    )
    place_p.add_argument(
        "--price", type=float, metavar="PRICE", default=None,
        help="Limit price (required for LIMIT and STOP_LIMIT)"
    )
    place_p.add_argument(
        "--stop-price", type=float, metavar="STOP_PRICE", default=None,
        dest="stop_price",
        help="Trigger price (required for STOP_LIMIT)"
    )
    place_p.add_argument(
        "--tif", dest="time_in_force", default="GTC",
        choices=["GTC", "IOC", "FOK"],
        help="Time-in-force for LIMIT orders (default: GTC)"
    )
    place_p.add_argument(
        "--reduce-only", action="store_true", default=False,
        help="Reduce-only flag"
    )

    # --- open-orders ---
    oo_p = sub.add_parser("open-orders", help="List open orders")
    oo_p.add_argument("--symbol", metavar="SYMBOL", default=None, help="Filter by symbol")

    # --- account ---
    sub.add_parser("account", help="Show account balances")

    return parser


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    # Initialise logging before anything else
    setup_logging(log_level=args.log_level)

    dispatch = {
        "ping": cmd_ping,
        "place": cmd_place,
        "open-orders": cmd_open_orders,
        "account": cmd_account,
    }

    handler = dispatch.get(args.command)
    if handler is None:
        parser.print_help()
        sys.exit(1)

    handler(args)


if __name__ == "__main__":
    main()
