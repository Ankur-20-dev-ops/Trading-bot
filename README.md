# 🤖 Binance Futures Testnet Trading Bot

A clean, lightweight Python CLI application for placing futures orders on the **Binance Futures Testnet (USDT-M)**. Built with a structured three-layer architecture, proper logging, and full input validation — no heavy frameworks, just Python and `requests`.

---

## Features

- ✅ Place **Market**, **Limit**, and **Stop-Limit** orders
- ✅ Supports **BUY** and **SELL** sides
- ✅ Full **input validation** with descriptive error messages
- ✅ **Rotating log file** with complete request/response trail
- ✅ Clean **CLI** with multiple sub-commands
- ✅ Credentials via **environment variables** (no secrets in code)
- ✅ Structured **three-layer architecture** (client → orders → CLI)

---

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py          # Package exports
│   ├── client.py            # Binance REST API wrapper (HMAC signing, HTTP)
│   ├── orders.py            # Order placement logic + response formatting
│   ├── validators.py        # Input validation (symbol, side, qty, price …)
│   └── logging_config.py    # Rotating file + console log setup
├── cli.py                   # CLI entry point (argparse sub-commands)
├── logs/
│   └── trading_bot.log      # Auto-created on first run
├── requirements.txt
└── README.md
```

---

## Setup

### Prerequisites

- Python **3.9+**
- A [Binance Futures Testnet](https://testnet.binancefuture.com) account

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/trading-bot.git
cd trading-bot
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

> Only one runtime dependency: **`requests`**

### 3. Get Testnet API credentials

1. Go to [https://testnet.binancefuture.com](https://testnet.binancefuture.com)
2. Log in with your GitHub account
3. Navigate to **API Key** → generate a new key pair
4. Save your **API Key** and **Secret Key**

### 4. Set credentials as environment variables

**Linux / macOS:**
```bash
export BINANCE_TESTNET_API_KEY="your_api_key_here"
export BINANCE_TESTNET_API_SECRET="your_api_secret_here"
```

**Windows (Command Prompt):**
```cmd
set BINANCE_TESTNET_API_KEY=your_api_key_here
set BINANCE_TESTNET_API_SECRET=your_api_secret_here
```

> Alternatively, pass `--api-key` and `--api-secret` flags directly to any command.

---

## Usage

### Check connectivity

```bash
python cli.py ping
```
```
✅  Binance Futures Testnet is reachable. Server time: 1720616531482 ms
```

---

### Place a Market Order

```bash
# BUY
python cli.py place --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001

# SELL
python cli.py place --symbol ETHUSDT --side SELL --type MARKET --quantity 0.01
```

---

### Place a Limit Order

```bash
python cli.py place \
  --symbol BTCUSDT \
  --side SELL \
  --type LIMIT \
  --quantity 0.001 \
  --price 70000
```

---

### Place a Stop-Limit Order

```bash
python cli.py place \
  --symbol BTCUSDT \
  --side BUY \
  --type STOP_LIMIT \
  --quantity 0.001 \
  --price 68000 \
  --stop-price 67500
```

---

### List Open Orders

```bash
python cli.py open-orders --symbol BTCUSDT
```

---

### View Account Balances

```bash
python cli.py account
```

---

### All CLI Options

```
usage: trading_bot [-h] [--api-key KEY] [--api-secret SECRET]
                   [--log-level {DEBUG,INFO,WARNING,ERROR}]
                   <command> ...

commands:
  ping          Test connectivity to Binance Futures Testnet
  place         Place a new futures order
  open-orders   List open orders (optionally filter by symbol)
  account       Show non-zero account balances
```

**`place` flags:**

| Flag | Required | Description |
|---|---|---|
| `--symbol` | ✅ | Trading pair, e.g. `BTCUSDT` |
| `--side` | ✅ | `BUY` or `SELL` |
| `--type` | ✅ | `MARKET`, `LIMIT`, or `STOP_LIMIT` |
| `--quantity` | ✅ | Order quantity in base asset |
| `--price` | For LIMIT / STOP_LIMIT | Limit price |
| `--stop-price` | For STOP_LIMIT | Trigger price |
| `--tif` | No (default: `GTC`) | Time-in-force: `GTC`, `IOC`, `FOK` |
| `--reduce-only` | No | Reduce-only flag |

---

## Sample Output

```
┌─ Order Request ────────────────────────────────────
│  Symbol     : BTCUSDT
│  Side       : ▲ BUY
│  Type       : MARKET
│  Quantity   : 0.001
└────────────────────────────────────────────────────

┌─ Order Confirmation ───────────────────────────────
│  Order ID   : 4611686018427387959
│  Symbol     : BTCUSDT
│  Side       : BUY
│  Type       : MARKET
│  Status     : FILLED
│  Orig Qty   : 0.001
│  Executed   : 0.001
│  Avg Price  : 57432.10
│  Price      : 0
│  Stop Price : 0
│  Time InFrc : GTC
│  Client OID : x-xcKtGiEu20250710
│  Created At : 1720616531925 (ms epoch)
└────────────────────────────────────────────────────

✅  Order placed successfully!
```

---

## Logging

Logs are written to `logs/trading_bot.log` automatically on first run.

- **File:** `DEBUG` level and above — full API request/response trail
- **Console:** `WARNING` level and above — keeps the terminal clean
- **Rotation:** Max 5 MB per file, 3 backups kept

To enable verbose console output:
```bash
python cli.py --log-level DEBUG place --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
```

---

## Error Handling

| Scenario | Behaviour |
|---|---|
| Invalid symbol / side / type | Descriptive error message, exit code `2` |
| Missing price for LIMIT order | Descriptive error message, exit code `2` |
| Binance API error (e.g. insufficient margin) | API error code + message shown, exit code `3` |
| Network timeout / connection failure | Exception caught and logged, exit code `4` |
| Missing API credentials | Early exit with setup instructions, exit code `1` |

---

## Assumptions

- **Testnet only** — the base URL `https://testnet.binancefuture.com` is the default. Override via `BinanceClient(base_url=...)` for production.
- **USDT-M perpetual futures** — all orders use the `/fapi/v1/order` endpoint.
- **Quantity precision** must match the symbol's `LOT_SIZE` filter. If Binance returns error `-1111`, reduce decimal places (e.g. use `0.001` not `0.0012345`).
- Credentials are read from environment variables or CLI flags — never hardcoded.

---

## Tech Stack

| | |
|---|---|
| Language | Python 3.9+ |
| HTTP | `requests` |
| CLI | `argparse` (stdlib) |
| Auth | HMAC-SHA256 signed REST |
| Logging | `logging.handlers.RotatingFileHandler` |

---

## License

MIT
