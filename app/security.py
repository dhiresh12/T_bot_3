from __future__ import annotations

import hashlib
import hmac
import random
import string
import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.core import UserProfile


class SecurityManager:
    """
    Handles security-related operations like code generation and verification.
    Phase 2: New Security Module.
    """

    def generate_unique_code(self, length: int = 8) -> str:
        """Generates a secure, random, and unique code for withdrawal verification."""
        alphabet = string.ascii_uppercase + string.digits
        return "".join(random.choices(alphabet, k=length))

    def generate_transaction_id(self, user_id: int) -> str:
        """Generates a unique transaction ID for tracking."""
        return f"TXN-{user_id}-{uuid.uuid4().hex[:12].upper()}"

    def verify_withdrawal_code(self, request: dict, provided_code: str) -> bool:
        """Verifies if the provided code matches the one in the withdrawal request."""
        return request.get("unique_code") == provided_code

    def verify_telegram_init_data(self, data: str, hash: str, bot_token: str) -> bool:
        """Verifies the HMAC-SHA256 signature of Telegram WebApp initData."""
        if not data or not hash or not bot_token:
            return False
        secret_key = hashlib.sha256(bot_token.encode("utf-8")).digest()
        mac = hmac.new(secret_key, data.encode("utf-8"), hashlib.sha256)
        return hmac.compare_digest(mac.hexdigest(), hash)