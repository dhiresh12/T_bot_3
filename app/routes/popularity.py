"""Flask blueprint: popularity endpoints."""
from __future__ import annotations

from app.routes._helpers import (
    _check_rate_limit,
    _safe_int,
    _get_user_id_from_request,
    _require_auth_post,
    _require_auth_get,
)
from flask import Blueprint, current_app, jsonify, request

bp = Blueprint("popularity", __name__)



# --- Popularity & Social Features API ---

@_require_auth_post("claim_daily_popularity")
@bp.post("/api/popularity/claim-daily/<int:user_id>")
def claim_daily_popularity(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    current_engine.register_user(user_id, "Guest")
    success, message, data = current_engine.claim_daily_popularity(user_id)
    profile = current_engine.get_profile(user_id)
    return jsonify({"success": success, "message": message, "popularity_points": profile.popularity_points, "data": data}), 200


@_require_auth_post("buy_popularity_coins")



@_require_auth_post("buy_popularity_coins")
@bp.post("/api/popularity/buy-coins/<int:user_id>")
def buy_popularity_coins(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    payload = request.get_json(silent=True) or {}
    amount = int(payload.get("amount", 0))
    if amount <= 0:
        return jsonify({"error": "Invalid amount."}), 400
    current_engine.register_user(user_id, "Guest")
    success, message, data = current_engine.buy_popularity_with_coins(user_id, amount)
    profile = current_engine.get_profile(user_id)
    return jsonify({"success": success, "message": message, "popularity_points": profile.popularity_points, "coins": profile.coins, "data": data}), 200


@_require_auth_post("buy_popularity_money")



@_require_auth_post("buy_popularity_money")
@bp.post("/api/popularity/buy-money/<int:user_id>")
def buy_popularity_money(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    payload = request.get_json(silent=True) or {}
    amount = int(payload.get("amount", 0))
    if amount <= 0:
        return jsonify({"error": "Invalid amount."}), 400
    current_engine.register_user(user_id, "Guest")
    success, message, data = current_engine.buy_popularity_with_money(user_id, amount)
    profile = current_engine.get_profile(user_id)
    return jsonify({"success": success, "message": message, "popularity_points": profile.popularity_points, "wallet_bot": profile.wallet_bot, "data": data}), 200


@_require_auth_post("send_popularity")



@_require_auth_post("send_popularity")
@bp.post("/api/popularity/send/<int:user_id>")
def send_popularity(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    payload = request.get_json(silent=True) or {}
    to_user_id = payload.get("to_user_id")
    amount = int(payload.get("amount", 0))
    if not to_user_id or amount <= 0:
        return jsonify({"error": "Missing 'to_user_id' or invalid 'amount'."}), 400
    current_engine.register_user(user_id, "Guest")
    current_engine.register_user(to_user_id, "Guest")
    success, message, data = current_engine.send_popularity(user_id, to_user_id, amount)
    profile = current_engine.get_profile(user_id)
    return jsonify({"success": success, "message": message, "popularity_points": profile.popularity_points, "data": data}), 200

