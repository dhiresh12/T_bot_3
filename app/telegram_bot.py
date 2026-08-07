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
        self._last_sent: Optional[Dict] = None

    def send_message(self, chat_id: int, text: str, reply_markup: Optional[Dict] = None, is_start: bool = False):
        """Sends a message to a specific chat ID via the Telegram Bot API."""
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
        if reply_markup:
            payload["reply_markup"] = reply_markup
        # If it's the start command AND there isn't already an inline keyboard,
        # send the persistent keyboard. This prevents overwriting the main menu.
        elif is_start:
            persistent_keyboard = {
                "keyboard": [
                    [{"text": "🚀 Launch Mini App", "web_app": {"url": self.mini_app_url}}],
                    [{"text": "👤 Profile"}, {"text": "💰 Wallet"}, {"text": "🏆 Leaderboard"}]
                ],
                "resize_keyboard": True,
                "one_time_keyboard": False  # Keep it open
            }
            payload["reply_markup"] = persistent_keyboard

        # If no token is configured (e.g., during tests/local dev), simply record the
        # message instead of making a real network call.
        if not self.token:
            self._last_sent = payload
            print(f"[telegram-bot][mock] -> {text}")
            return

        try:
            requests.post(f"{self.api_url}/sendMessage", json=payload)
        except requests.RequestException as e:
            print(f"Error sending message: {e}")

    def handle_update(self, update: dict) -> str:
        """
        Processes an incoming update from Telegram and returns the response text
        that was (or would be) sent to the user.
        """
        if not update:
            return "No update"

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
            return "No handleable update"

        chat_id = message.get("chat", {}).get("id")
        # The user object may come from "from" (real Telegram payloads) or, in some
        # test payloads, the user info is embedded directly in the chat object. Be
        # robust and fall back to the chat fields when "from" is missing.
        user_id = user.get("id")
        first_name = user.get("first_name")

        if not user_id:
            # Fallback: read the user from the chat object (used by some test payloads).
            user_id = message.get("chat", {}).get("id")
            first_name = message.get("chat", {}).get("first_name")

        if not user_id:
            return "No user id"

        first_name = first_name or "User"

        inviter_id = None
        is_start_command = False

        # Phase 6: Handle referral from /start command
        # Also handle persistent keyboard commands that don't start with '/'
        normalized_command = (command or "").lower()
        if normalized_command.startswith("start"):
            parts = normalized_command.split()
            if len(parts) > 1:
                try:
                    inviter_id = int(parts[1])
                except ValueError:
                    inviter_id = None  # Invalid referral code
            is_start_command = True

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
        self.send_message(chat_id, response_text, reply_markup, is_start=is_start_command)
        return response_text
