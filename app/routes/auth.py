"""Flask blueprint: auth endpoints."""
from __future__ import annotations
import os

from app.routes._helpers import (
    _check_rate_limit,
    _safe_int,
    _get_user_id_from_request,
    _require_auth_post,
    _require_auth_get,
)
from flask import Blueprint, current_app, jsonify, request

bp = Blueprint("auth", __name__)



@bp.post("/api/auth/login")
def login() -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    payload = request.get_json(silent=True) or {}
    user_id = payload.get("user_id")
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400
    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid user_id"}), 400
    current_engine.register_user(user_id, payload.get("name", "Guest"))
    token = current_engine.create_session(user_id)
    return jsonify({"token": token, "user_id": user_id}), 200



@bp.post("/api/auth/telegram")
def telegram_auth() -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    payload = request.get_json(silent=True) or {}
    init_data = payload.get("init_data", "")
    hash_value = payload.get("hash", "")
    if not init_data or not hash_value:
        return jsonify({"error": "Missing init_data or hash"}), 400
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not bot_token:
        return jsonify({"error": "Server misconfigured: missing TELEGRAM_BOT_TOKEN"}), 500
    if not current_engine.security.verify_telegram_init_data(init_data, hash_value, bot_token):
        return jsonify({"error": "Invalid Telegram authentication"}), 401
    try:
        data_dict = dict(pair.split("=") for pair in init_data.split("&") if "=" in pair)
    except Exception:
        return jsonify({"error": "Invalid init_data format"}), 400
    user_id = data_dict.get("user_id")
    if not user_id:
        return jsonify({"error": "Missing user_id in init_data"}), 400
    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid user_id"}), 400
    first_name = data_dict.get("first_name", "TelegramUser")
    current_engine.register_user(user_id, first_name)
    token = current_engine.create_session(user_id)
    return jsonify({"token": token, "user_id": user_id, "name": first_name}), 200
