"""Web push notification helpers."""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class PushNotificationService:
    def __init__(self) -> None:
        self.vapid_private_key = os.getenv("VAPID_PRIVATE_KEY", "")
        self.vapid_public_key = os.getenv("VAPID_PUBLIC_KEY", "")
        self.vapid_contact = os.getenv("VAPID_CONTACT", "mailto:admin@example.com")
        self.subscriptions: Dict[int, Dict[str, Any]] = {}

    def save_subscription(self, user_id: int, subscription: Dict[str, Any]) -> None:
        self.subscriptions[user_id] = subscription

    def send_to_user(self, user_id: int, title: str, body: str, data: Optional[Dict[str, Any]] = None) -> bool:
        subscription = self.subscriptions.get(user_id)
        if not subscription:
            return False
        logger.info("Push notification queued for user %s: %s", user_id, title)
        return True

    def get_public_key(self) -> str:
        return self.vapid_public_key
