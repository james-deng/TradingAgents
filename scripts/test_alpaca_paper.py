"""
Minimal Alpaca paper-trading smoke test (no LLMs involved).

Exports a $1 market buy for AAPL to confirm credentials and connectivity.
Requires env vars: ALPACA_API_KEY_ID, ALPACA_API_SECRET_KEY (and optionally ALPACA_PAPER_BASE_URL).

This script prepends the project root to sys.path so it works even if Python
isn't picking up the editable install.
"""

import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Load env before importing DEFAULT_CONFIG so keys are picked up
load_dotenv()

from tradingagents.execution import AlpacaPaperClient  # noqa: E402
from tradingagents.default_config import DEFAULT_CONFIG  # noqa: E402
import os


def main():
    cfg = DEFAULT_CONFIG["alpaca_paper_trading"].copy()
    cfg["enabled"] = True
    cfg["order_notional"] = 1000  # $1000 test order (for market orders)
    cfg["extended_hours"] = True  # allow outside RTH when supported
    # Refresh auth fields from env in case defaults were None
    cfg["api_key"] = os.getenv("ALPACA_API_KEY_ID") or cfg.get("api_key")
    cfg["api_secret"] = os.getenv("ALPACA_API_SECRET_KEY") or cfg.get("api_secret")
    cfg["base_url"] = os.getenv("ALPACA_PAPER_BASE_URL") or cfg.get("base_url")

    client = AlpacaPaperClient(cfg)
    print("Client ready:", client.is_ready())
    # Helpful visibility
    print("Key present:", bool(cfg.get("api_key")), "Secret present:", bool(cfg.get("api_secret")))
    print("Base URL:", client.base_url)
    # Place a limit order: 1 share at a limit price (default $500 if not provided)
    limit_price = float(os.getenv("ALPACA_TEST_LIMIT_PRICE", "500"))
    qty = float(os.getenv("ALPACA_TEST_LIMIT_QTY", "1"))
    result = client.submit_order(
        "AAPL",
        "buy",
        order_type="limit",
        qty=qty,
        limit_price=limit_price,
    )
    print("Order result:", result)


if __name__ == "__main__":
    main()
