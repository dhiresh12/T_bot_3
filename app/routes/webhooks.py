"""Flask blueprint: webhooks endpoints."""
from __future__ import annotations

import os
from typing import Any

try:
    import requests
except ImportError:  # pragma: no cover - requests unavailable
    requests = None

from app.routes._helpers import (
    _check_rate_limit,
    _safe_int,
    _get_user_id_from_request,
    _require_auth_post,
    _require_auth_get,
)
from flask import Blueprint, current_app, jsonify, request

bp = Blueprint("webhooks", __name__)



@bp.get("/api/webhook/status")
def webhook_status() -> tuple[dict, int]:
    """Reports whether the Telegram webhook is registered and the bot token is set."""
    from app.core import _resolve_mini_app_url
    from app.telegram_bot import TelegramBotService
    service = TelegramBotService(engine=current_app.config.get("engine"))
    result: dict[str, Any] = {
        "mini_app_url": _resolve_mini_app_url(),
        "mini_app_url_env": os.getenv("MINI_APP_URL"),
        "render_external_url": os.getenv("RENDER_EXTERNAL_URL"),
    }
    if not service.token:
        result.update({
            "token_set": False,
            "webhook_url": None,
            "message": "TELEGRAM_BOT_TOKEN is not set on the server. Add it in Render -> Environment to enable the bot.",
        })
        return jsonify(result), 200
    if requests is None:
        result.update({"token_set": True, "error": "requests module not installed"})
        return jsonify(result), 200
    try:
        info = requests.post(
            f"{service.api_url}/getWebhookInfo", timeout=15
        ).json()
    except Exception as exc:  # noqa: BLE001
        result.update({"token_set": True, "error": str(exc)})
        return jsonify(result), 200
    result.update({
        "token_set": True,
        "webhook_url": info.get("result", {}).get("url"),
        "pending_update_count": info.get("result", {}).get("pending_update_count", 0),
        "message": "Webhook configured." if info.get("result", {}).get("url") else "No webhook URL set yet.",
    })
    return jsonify(result), 200



@bp.post("/webhook")
def telegram_webhook() -> tuple[dict, int]:
    """
    This is the main entry point for Telegram updates.
    Telegram will send a POST request to this endpoint.
    """
    update = request.get_json(silent=True)
    if not update:
        return jsonify({"status": "error", "message": "Invalid JSON"}), 400

    # We create a new service instance for each request to ensure it's stateless,
    # but it uses the shared engine from the app context.
    engine = current_app.config["engine"]
    from app.telegram_bot import TelegramBotService
    telegram_service = TelegramBotService(engine=engine)
    telegram_service.handle_update(update) # The service sends the reply via API call
    return jsonify({"status": "ok"}), 200



@bp.post("/api/webhooks/razorpay")
def razorpay_webhook() -> tuple[dict, int]:
    """Receives RazorpayX payout events and updates withdrawal status.

    Configure this URL in the Razorpay dashboard with the same
    RAZORPAY_WEBHOOK_SECRET used to verify the signature.
    """
    from app.payouts import PayoutService

    svc = PayoutService()
    raw = request.get_data()
    signature = request.headers.get("X-Razorpay-Signature", "")
    if not svc.verify_webhook_signature(raw, signature):
        return jsonify({"status": "invalid signature"}), 400

    payload = request.get_json(silent=True) or {}
    event = payload.get("event", "")
    entity = (payload.get("payload") or {}).get("payout") or {}
    payout = entity.get("entity") or {}
    payout_id = payout.get("id")
    if not payout_id:
        return jsonify({"status": "ignored"}), 200

    # Map Razorpay payout status -> our status
    razorpay_status = payout.get("status")
    mapped = {
        "processed": "paid",
        "settled": "paid",
        "failed": "failed",
        "reversed": "failed",
    }
    new_status = mapped.get(razorpay_status)
    if not new_status:
        return jsonify({"status": "ignored"}), 200

    engine = current_app.config["engine"]
    engine.update_payout_status(payout_id, new_status)
    return jsonify({"status": "ok"}), 200
