"""
Low-level Binance Futures Testnet client.

Wraps raw HMAC-signed REST requests so the rest of the application
never needs to deal with authentication boilerplate.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import time
import urllib.parse
from decimal import Decimal
from typing import Any, Dict, Optional

import requests

from .logging_config import setup_logging

TESTNET_BASE_URL = "https://testnet.binancefuture.com"
FUTURES_API_V1 = "/fapi/v1"

logger = logging.getLogger("trading_bot.client")


class BinanceAPIError(Exception):
    """Raised when the Binance API returns an error payload."""

    def __init__(self, code: int, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"Binance API error {code}: {message}")


class BinanceClient:
    """
    Thin, stateless wrapper around the Binance Futures Testnet REST API.

    Parameters
    ----------
    api_key:    Testnet API key.
    api_secret: Testnet API secret.
    base_url:   Override the default testnet base URL (useful for testing).
    timeout:    HTTP request timeout in seconds.
    """

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        base_url: str = TESTNET_BASE_URL,
        timeout: int = 10,
    ) -> None:
        if not api_key or not api_secret:
            raise ValueError("api_key and api_secret must not be empty.")
        self._api_key = api_key
        self._api_secret = api_secret
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._session = requests.Session()
        self._session.headers.update(
            {
                "X-MBX-APIKEY": self._api_key,
                "Content-Type": "application/x-www-form-urlencoded",
            }
        )
        logger.debug("BinanceClient initialised (base_url=%s)", self._base_url)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _sign(self, params: Dict[str, Any]) -> str:
        """Return HMAC-SHA256 signature for the given query-string params."""
        query_string = urllib.parse.urlencode(params)
        return hmac.new(
            self._api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def _signed_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute a signed HTTP request against the Binance Futures API.

        Automatically appends `timestamp` and `signature` fields.
        """
        params = params or {}
        params["timestamp"] = int(time.time() * 1000)
        params["signature"] = self._sign(params)

        url = f"{self._base_url}{FUTURES_API_V1}{endpoint}"

        logger.debug(
            "→ %s %s | params=%s",
            method.upper(),
            endpoint,
            {k: v for k, v in params.items() if k != "signature"},
        )

        try:
            if method.upper() == "GET":
                response = self._session.get(
                    url, params=params, timeout=self._timeout
                )
            elif method.upper() == "POST":
                response = self._session.post(
                    url, data=params, timeout=self._timeout
                )
            elif method.upper() == "DELETE":
                response = self._session.delete(
                    url, params=params, timeout=self._timeout
                )
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
        except requests.exceptions.Timeout as exc:
            logger.error("Request timed out (%s %s): %s", method, endpoint, exc)
            raise
        except requests.exceptions.ConnectionError as exc:
            logger.error("Network error (%s %s): %s", method, endpoint, exc)
            raise

        logger.debug(
            "← %s %s | status=%s body=%s",
            method.upper(),
            endpoint,
            response.status_code,
            response.text[:500],
        )

        data: Dict[str, Any] = response.json()

        # Binance returns error payloads with HTTP 4xx/5xx AND a `code` field < 0
        if not response.ok or (isinstance(data, dict) and data.get("code", 0) < 0):
            code = data.get("code", response.status_code)
            msg = data.get("msg", response.text)
            logger.error("API error code=%s msg=%s", code, msg)
            raise BinanceAPIError(code=code, message=msg)

        return data

    # ------------------------------------------------------------------
    # Public API methods
    # ------------------------------------------------------------------

    def get_server_time(self) -> int:
        """Return Binance server time (epoch ms) — also used as connectivity check."""
        url = f"{self._base_url}{FUTURES_API_V1}/time"
        resp = self._session.get(url, timeout=self._timeout)
        resp.raise_for_status()
        return resp.json()["serverTime"]

    def get_exchange_info(self) -> Dict[str, Any]:
        """Return full exchange info (symbol filters, etc.)."""
        url = f"{self._base_url}{FUTURES_API_V1}/exchangeInfo"
        resp = self._session.get(url, timeout=self._timeout)
        resp.raise_for_status()
        return resp.json()

    def get_account(self) -> Dict[str, Any]:
        """Return account information (balances, positions)."""
        return self._signed_request("GET", "/account")

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: Decimal,
        price: Optional[Decimal] = None,
        stop_price: Optional[Decimal] = None,
        time_in_force: str = "GTC",
        reduce_only: bool = False,
    ) -> Dict[str, Any]:
        """
        Place a new order on Binance Futures Testnet.

        Parameters
        ----------
        symbol:        Trading pair (e.g. BTCUSDT).
        side:          BUY or SELL.
        order_type:    MARKET, LIMIT, or STOP (stop-limit).
        quantity:      Order quantity in base asset.
        price:         Limit price (required for LIMIT and STOP).
        stop_price:    Trigger price (required for STOP).
        time_in_force: GTC | IOC | FOK (ignored for MARKET).
        reduce_only:   If True, order can only reduce an existing position.
        """
        params: Dict[str, Any] = {
            "symbol": symbol,
            "side": side,
            "type": order_type if order_type != "STOP_LIMIT" else "STOP",
            "quantity": str(quantity),
            "reduceOnly": str(reduce_only).lower(),
        }

        if order_type in ("LIMIT", "STOP_LIMIT"):
            params["timeInForce"] = time_in_force
            params["price"] = str(price)

        if order_type == "STOP_LIMIT":
            params["stopPrice"] = str(stop_price)

        logger.info(
            "Placing order: symbol=%s side=%s type=%s qty=%s price=%s stopPrice=%s",
            symbol,
            side,
            order_type,
            quantity,
            price,
            stop_price,
        )

        result = self._signed_request("POST", "/order", params)
        logger.info("Order placed successfully: orderId=%s", result.get("orderId"))
        return result

    def cancel_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """Cancel an open order by orderId."""
        return self._signed_request(
            "DELETE", "/order", {"symbol": symbol, "orderId": order_id}
        )

    def get_open_orders(self, symbol: Optional[str] = None) -> list:
        """Return a list of open orders, optionally filtered by symbol."""
        params: Dict[str, Any] = {}
        if symbol:
            params["symbol"] = symbol
        return self._signed_request("GET", "/openOrders", params)  # type: ignore[return-value]
