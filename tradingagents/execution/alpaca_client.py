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
        self.order_qty = config.get("order_qty")
        self.extended_hours = bool(config.get("extended_hours", False))

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
        self,
        symbol: str,
        side: str,
        notional: Optional[float] = None,
        qty: Optional[float] = None,
        order_type: str = "market",
        limit_price: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Submit a simple order. Market supports notional; limit requires qty."""
        side = side.lower()
        order_type = order_type.lower()

        payload = {
            "symbol": symbol.upper(),
            "side": side,
            "type": order_type,
            "time_in_force": self.time_in_force,
        }

        if order_type == "market":
            # Prefer qty (avoids fractional short restrictions); fall back to notional.
            if qty is not None:
                payload["qty"] = qty
            elif notional is not None:
                payload["notional"] = notional
            else:
                payload["qty"] = self.order_qty if hasattr(self, "order_qty") else 1
        elif order_type == "limit":
            if qty is None or limit_price is None:
                return {
                    "status": "error",
                    "error": "Limit orders require qty and limit_price",
                }
            payload["qty"] = qty
            payload["limit_price"] = limit_price
        else:
            return {"status": "error", "error": f"Unsupported order type: {order_type}"}

        if self.extended_hours:
            payload["extended_hours"] = True

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
        except requests.HTTPError as exc:  # pragma: no cover - simple logging path
            body = None
            try:
                body = resp.text
            except Exception:
                pass
            logging.error("Failed to place Alpaca order: %s | body=%s", exc, body)
            return {
                "status": "error",
                "error": str(exc),
                "status_code": getattr(exc.response, "status_code", None),
                "body": body,
            }
        except Exception as exc:  # pragma: no cover - simple logging path
            logging.error("Failed to place Alpaca order: %s", exc)
            return {"status": "error", "error": str(exc)}
