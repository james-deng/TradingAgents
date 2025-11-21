import json
import logging
from typing import Any, Dict, Optional

import requests


class AlpacaPaperClient:
    """Lightweight Alpaca paper-trading client for submitting market orders."""

    def __init__(self, config: Dict[str, Any]):
        self.enabled = config.get("enabled", False)
        self.api_key = config.get("api_key")
        self.api_secret = config.get("api_secret")
        self.base_url = self._normalize_base_url(
            config.get("base_url", "https://paper-api.alpaca.markets")
        )
        self.order_notional = config.get("order_notional", 1000)
        self.time_in_force = config.get("time_in_force", "day")

    def is_ready(self) -> bool:
        """Return True only when enabled and keys are present."""
        return bool(self.enabled and self.api_key and self.api_secret)

    @staticmethod
    def _normalize_base_url(raw: str) -> str:
        """Strip whitespace, trailing slashes, and accidental /v2 suffixes."""
        if not raw:
            return "https://paper-api.alpaca.markets"
        url = raw.strip()
        url = url.rstrip("/")
        if url.endswith("/v2"):
            url = url[:-3]
        return url

    def submit_order(
        self, symbol: str, side: str, notional: Optional[float] = None
    ) -> Dict[str, Any]:
        """Submit a simple market order by notional."""
        order_notional = notional or self.order_notional
        payload = {
            "symbol": symbol.upper(),
            "side": side.lower(),
            "type": "market",
            "time_in_force": self.time_in_force,
            "notional": order_notional,
        }

        url = f"{self.base_url}/v2/orders"
        headers = {
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.api_secret,
            "Content-Type": "application/json",
        }

        try:
            resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=10)
            resp.raise_for_status()
            return {"status": "submitted", "order": resp.json()}
        except Exception as exc:  # pragma: no cover - simple logging path
            logging.error("Failed to place Alpaca order: %s", exc)
            return {"status": "error", "error": str(exc)}
