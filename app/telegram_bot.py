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
        
        # Determine the source of the command (message or button click)
        if "callback_query" in update:
            callback_query = update["callback_query"]
            message = callback_query.get("message", {})
            user = callback_query.get("from", {})
            command = callback_query.get("data")
        elif "message" in update:
            message = update.get("message", {})
            user = message.get("from", {})
            command = (message.get("text") or "").strip()
        else:
            # Ignore other update types for now
            return

        chat_id = message.get("chat", {}).get("id")
        user_id = user.get("id")
        first_name = user.get("first_name", "User")

        if not user_id:
            return
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
        response = self.engine.handle_command(user_id, command)

        # If the response from the engine is a dict, it includes a reply_markup
        if isinstance(response, dict):
            reply_markup = response.get("reply_markup")
            response_text = response.get("text", "Something went wrong.")
        else:
            response_text = response
            reply_markup = None
        
        # Send the response back to the user
        self.send_message(chat_id, response_text, reply_markup)
