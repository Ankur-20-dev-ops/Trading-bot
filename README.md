# 🤖 Binance Futures Testnet Trading Bot

A clean, production-style Python CLI application that places **Market**, **Limit**, and **Stop-Limit** orders on the **Binance Futures Testnet (USDT-M)**.

---

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py          # Package exports
│   ├── client.py            # Binance REST API wrapper (auth, signing, HTTP)
│   ├── orders.py            # Order placement logic + response formatting
│   ├── validators.py        # Input validation (symbol, side, qty, price …)
│   └── logging_config.py    # Rotating file + console log setup
├── cli.py                   # CLI entry point (argparse, sub-commands)
├── logs/
│   └── trading_bot.log      # Rotating log file (auto-created on first run)
├── requirements.txt
└── README.md
```

**Layer separation:**
- `bot/client.py` — knows nothing about the CLI; only speaks HTTP.
- `bot/orders.py` — orchestrates validation → API call → formatted output.
- `cli.py` — parses args, wires everything together, handles exit codes.

---

## Setup

### 1. Python

Requires **Python 3.9+**.

```bash
python --version
```

### 2. Clone / unzip

```bash
unzip trading_bot.zip   # or: git clone <repo>
cd trading_bot
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

Only one runtime dependency: **`requests`**.

### 4. Get Testnet credentials

1. Visit [https://testnet.binancefuture.com](https://testnet.binancefuture.com).
2. Log in with your GitHub account.
3. Go to **API Key** → generate a new key pair.
4. Copy the **API Key** and **Secret Key** somewhere safe.

### 5. Set credentials

**Option A — environment variables (recommended):**

```bash
export BINANCE_TESTNET_API_KEY="your_api_key_here"
export BINANCE_TESTNET_API_SECRET="your_api_secret_here"
```

**Option B — CLI flags** (pass on every command):

```bash
python cli.py --api-key YOUR_KEY --api-secret YOUR_SECRET place ...
```

---

## Running Examples

### Check connectivity

```bash
python cli.py ping
# ✅  Binance Futures Testnet is reachable.
```

### Place a Market Order — BUY

```bash
python cli.py place \
  --symbol BTCUSDT \
  --side BUY \
  --type MARKET \
  --quantity 0.001
```

### Place a Market Order — SELL

```bash
python cli.py place \
  --symbol ETHUSDT \
  --side SELL \
  --type MARKET \
  --quantity 0.01
```

### Place a Limit Order

```bash
python cli.py place \
  --symbol BTCUSDT \
  --side SELL \
  --type LIMIT \
  --quantity 0.001 \
  --price 60000
```

### Place a Stop-Limit Order (bonus order type)

```bash
python cli.py place \
  --symbol BTCUSDT \
  --side BUY \
  --type STOP_LIMIT \
  --quantity 0.001 \
  --price 68000 \
  --stop-price 67500
```

### List Open Orders

```bash
python cli.py open-orders --symbol BTCUSDT
```

### Show Account Balances

```bash
python cli.py account
```

### Change log verbosity

```bash
python cli.py --log-level DEBUG place --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
```

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

- Log file: `logs/trading_bot.log`
- Rotating: max 5 MB per file, 3 backups kept.
- Console: `WARNING` and above only (keeps terminal clean).
- File: `DEBUG` and above (full API request/response trail).

The `logs/` directory is created automatically on first run.

---

## Error Handling

| Scenario | Behaviour |
|---|---|
| Invalid symbol / side / type | `ValueError` → printed with ❌ message, exit code 2 |
| Missing price for LIMIT | `ValueError` → printed with ❌ message, exit code 2 |
| Binance API error (e.g. insufficient margin) | `BinanceAPIError` with code & message, exit code 3 |
| Network timeout / connection refused | `requests` exception, logged + printed, exit code 4 |
| Missing API credentials | Early exit with instructions, exit code 1 |

---

## Assumptions

- **Testnet only.** The base URL `https://testnet.binancefuture.com` is hard-coded as the default. Production use would require overriding `BinanceClient(base_url=...)`.
- **USDT-M perpetual futures.** All orders go to `/fapi/v1/order` (linear futures endpoint).
- **No order-book price lookup.** For MARKET orders the user does not supply a price — Binance fills at best available price.
- **Quantity precision** must match the symbol's `LOT_SIZE` filter. If Binance returns `-1111`, reduce decimal places (e.g. use `0.001` not `0.0012345`).
- The `--reduce-only` flag is exposed but defaults to `False`; useful when closing an existing position.

---

## Bonus Feature — Stop-Limit Orders

In addition to `MARKET` and `LIMIT`, the bot supports `STOP_LIMIT` orders.

```bash
python cli.py place \
  --symbol BTCUSDT --side BUY --type STOP_LIMIT \
  --quantity 0.001 --price 68000 --stop-price 67500
```

This maps to Binance's `STOP` futures order type with both `price` (limit) and `stopPrice` (trigger).
