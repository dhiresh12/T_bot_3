"""Razorpay UPI payout service (RazorpayX Payouts API).

This module talks to Razorpay directly over HTTPS using ``requests`` so no
extra SDK dependency is required. It is intentionally defensive: if the
Razorpay credentials are not configured it reports itself as disabled and
withdrawals simply stay in the "pending" state for manual processing.

Environment variables:
    RAZORPAY_KEY_ID            - RazorpayX key id
    RAZORPAY_KEY_SECRET       - RazorpayX key secret
    RAZORPAY_ACCOUNT_NUMBER   - your RazorpayX current account number
    RAZORPAY_WEBHOOK_SECRET   - secret used to verify webhook signatures
"""
from __future__ import annotations

import hashlib
import hmac
import os
from typing import Any, Dict, Tuple

try:
    import requests
except ImportError:  # pragma: no cover - requests is a hard dependency of the app
    requests = None

BASE_URL = "https://api.razorpay.com/v1"


class PayoutService:
    def __init__(self) -> None:
        self.key_id = os.getenv("RAZORPAY_KEY_ID", "")
        self.key_secret = os.getenv("RAZORPAY_KEY_SECRET", "")
        self.account_number = os.getenv("RAZORPAY_ACCOUNT_NUMBER", "")
        self.webhook_secret = os.getenv("RAZORPAY_WEBHOOK_SECRET", "")
        self.enabled = bool(
            self.key_id and self.key_secret and self.account_number and requests is not None
        )

    def _auth(self) -> Tuple[str, str]:
        return (self.key_id, self.key_secret)

    def create_upi_payout(
        self, upi_id: str, name: str, amount_paise: int, reference_id: str
    ) -> Tuple[bool, str]:
        """Create a UPI payout to ``upi_id``. Returns (success, payout_id_or_error)."""
        if not self.enabled:
            return False, "Payout gateway not configured."
        url = f"{BASE_URL}/payouts"
        payload = {
            "account_number": self.account_number,
            "amount": int(amount_paise),
            "currency": "INR",
            "mode": "UPI",
            "purpose": "payout",
            "reference_id": reference_id,
            "fund_account": {
                "account_type": "vpa",
                "vpa": {"address": upi_id},
                "contact": {"name": (name or "User")[:99], "reference_id": reference_id},
            },
            "notes": {"source": "xio_payplus"},
        }
        try:
            resp = requests.post(url, json=payload, auth=self._auth(), timeout=30)
        except Exception as exc:  # noqa: BLE001
            return False, f"Payout request failed: {exc}"
        if resp.status_code not in (200, 201, 202):
            return False, f"Payout rejected ({resp.status_code}): {resp.text[:200]}"
        data: Dict[str, Any] = resp.json()
        return True, data.get("id") or "created"

    def verify_webhook_signature(self, raw_body: bytes, signature: str) -> bool:
        if not self.webhook_secret or not signature:
            return False
        expected = hmac.new(
            self.webhook_secret.encode("utf-8"), raw_body, hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature)
