from __future__ import annotations

import os
import requests
from typing import Any, Dict, Optional

from app.core import BotEngine


class TelegramBotService:
    """
    Handles the interaction between the Telegram API and the BotEngine.
    Phase 6: Upgraded to handle referral links, admin-editable messages, and reply markups.
    """
    def __init__(self, engine: Optional[BotEngine] = None) -> None:
        self.engine = engine or BotEngine(storage_path="bot_data.db")
        self.token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        # The MINI_APP_URL should be the public URL of your Render app
        self.mini_app_url = os.getenv("MINI_APP_URL", "https://your-render-app.onrender.com")
        self.api_url = f"https://api.telegram.org/bot{self.token}"

    def send_message(self, chat_id: int, text: str, reply_markup: Optional[Dict] = None):
        """Sends a message to a specific chat ID via the Telegram Bot API."""
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
        if reply_markup:
            payload["reply_markup"] = reply_markup
        
        try:
            requests.post(f"{self.api_url}/sendMessage", json=payload)
        except requests.RequestException as e:
            print(f"Error sending message: {e}")

    def handle_update(self, update: dict) -> None:
        """
        Processes an incoming update from Telegram and returns a structured response
        for the Telegram API (including text and reply_markup).
        """
        if not update:
            return {"text": "No update"}

        message = update.get("message", {})
        if not message:
            # This could be a callback_query or other update type, ignore for now.
            return

        chat = message.get("chat", {})
        text = (message.get("text") or "").strip()
        user_id = chat.get("id")
        first_name = chat.get("first_name", "User")

        if not user_id:
            return

        user_id = int(user_id)
        command = text
        inviter_id = None

        # Phase 6: Handle referral from /start command
        if text.startswith("/start"):
            parts = text.split()
            if len(parts) > 1:
                try:
                    inviter_id = int(parts[1])
                except ValueError:
                    inviter_id = None # Invalid referral code
            command = "/start" # Normalize command

        # Register user, potentially with an inviter
        self.engine.register_user(user_id, first_name, inviter_id=inviter_id)

        # Let the engine handle the logic
        response_text = self.engine.handle_command(user_id, command)

        # --- Build the reply markup if needed ---
        reply_markup = None

        # Phase 6: Add "Mini App" button after successful bonus claim
        if "Congratulations! You won" in response_text:
            reply_markup = {
                "inline_keyboard": [
                    [
                        {"text": "🚀 Launch Mini App", "web_app": {"url": self.mini_app_url}}
                    ]
                ]
            }
        
        # Send the response back to the user
        self.send_message(user_id, response_text, reply_markup)
