from __future__ import annotations

import os
import sys
from typing import Any, Dict, Optional

try:
    import requests
except ImportError:  # pragma: no cover - requests unavailable
    requests = None  # Degrade to mock mode instead of crashing on import.

from app.core import BotEngine, _resolve_mini_app_url


def _safe_print(*args, **kwargs) -> None:
    """Print that won't crash on emojis/multibyte chars (e.g. Windows cp1252 console)."""
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        safe = " ".join(str(a).encode("ascii", "replace").decode("ascii") for a in args)
        sys.stderr.write(safe + "\n")


class TelegramBotService:
    """
    Handles the interaction between the Telegram API and the BotEngine.
    Phase 6: Upgraded to handle referral links, admin-editable messages, and reply markups.
    """

    def __init__(self, engine: Optional[BotEngine] = None) -> None:
        self.engine = engine or BotEngine(storage_path="bot_data.db")
        self.token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        # The MINI_APP_URL should be the public URL of your Render app
        self.mini_app_url = os.getenv("MINI_APP_URL") or _resolve_mini_app_url()
        self.api_url = f"https://api.telegram.org/bot{self.token}"
        self._last_sent: Optional[Dict] = None

    def set_webhook(self, url: str) -> Dict[str, Any]:
        """
        Registers this service's public URL with Telegram so that updates are
        delivered to the /webhook endpoint. Safe to call on every startup.
        """
        if not self.token:
            _safe_print("[telegram-bot][warn] TELEGRAM_BOT_TOKEN not set; webhook not registered.")
            return {"ok": False, "description": "Missing TELEGRAM_BOT_TOKEN"}
        if not url:
            _safe_print("[telegram-bot][warn] WEBHOOK_URL not set; webhook not registered.")
            return {"ok": False, "description": "Missing WEBHOOK_URL"}
        if requests is None:
            _safe_print("[telegram-bot][warn] 'requests' module not installed; skipping webhook registration.")
            return {"ok": False, "description": "requests module not available"}
        try:
            response = requests.post(
                f"{self.api_url}/setWebhook",
                json={"url": url},
                timeout=15,
            )
            result = response.json()
            _safe_print(f"[telegram-bot][webhook] setWebhook -> {result}")
            return result
        except requests.RequestException as e:
            _safe_print(f"[telegram-bot][error] setWebhook failed: {e}")
            return {"ok": False, "description": str(e)}

    def send_message(self, chat_id: int, text: str, reply_markup: Optional[Dict] = None, is_start: bool = False) -> Optional[Dict]:
        """
        Sends a message to a specific chat ID via the Telegram Bot API.

        Returns the Telegram API response dict (or None when mocked). The send
        is retried without ``parse_mode`` if Telegram rejects the Markdown
        payload, so messages with characters like `*`, `_`, or `|` never get
        swallowed silently.
        """
        payload = {"chat_id": chat_id, "text": text}
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
            try:
                sys.stderr.write(f"[telegram-bot][mock] -> {text}\n")
            except UnicodeEncodeError:
                encoded = text.encode("ascii", "replace").decode("ascii")
                sys.stderr.write(f"[telegram-bot][mock] -> {encoded}\n")
            return None

        if requests is None:
            self._last_sent = payload
            _safe_print("[telegram-bot][warn] 'requests' module not installed; message not sent.")
            return {"ok": False, "description": "requests module not available"}

        # Try Markdown first, then fall back to plain text if Telegram rejects it.
        for parse_mode in ("Markdown", None):
            candidate = dict(payload)
            if parse_mode:
                candidate["parse_mode"] = parse_mode
            try:
                resp = requests.post(f"{self.api_url}/sendMessage", json=candidate, timeout=15)
                result = resp.json()
            except requests.RequestException as e:
                _safe_print(f"[telegram-bot][error] sendMessage request error: {e}")
                return {"ok": False, "description": str(e)}

            if result.get("ok"):
                return result

            description = (result.get("description") or "").lower()
            # If Markdown failed to parse, retry once without parse_mode.
            if parse_mode and result.get("error_code") == 400 and "parse" in description:
                _safe_print(f"[telegram-bot][warn] Markdown parse failed, retrying as plain text: {description}")
                continue

            _safe_print(f"[telegram-bot][error] sendMessage API error: {result}")
            return result

        return {"ok": False, "description": "Could not send message"}

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
