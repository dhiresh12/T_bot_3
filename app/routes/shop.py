"""Flask blueprint: shop endpoints."""
from __future__ import annotations

from app.routes._helpers import (
    _check_rate_limit,
    _safe_int,
    _get_user_id_from_request,
    _require_auth_post,
    _require_auth_get,
)
from flask import Blueprint, current_app, jsonify, request

bp = Blueprint("shop", __name__)


# --- Shop API endpoints ---

@bp.get("/api/shop/catalog")
def shop_catalog() -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    return jsonify(current_engine.get_shop_catalog()), 200


@_require_auth_post("shop_redeem")



@_require_auth_post("shop_redeem")
@bp.post("/api/shop/redeem/<int:user_id>")
def shop_redeem(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    payload = request.get_json(silent=True) or {}
    item_id = payload.get("item_id")
    if not item_id:
        return jsonify({"error": "Missing 'item_id' in request body."}), 400
    current_engine.register_user(user_id, "Guest")
    success, message, item = current_engine.redeem_shop_item(user_id, item_id)
    profile = current_engine.get_profile(user_id)
    return jsonify({"success": success, "message": message, "item": item, "coins": profile.coins}), 200


@_require_auth_post("exchange_coins")



@_require_auth_post("exchange_coins")
@bp.post("/api/shop/exchange-coins/<int:user_id>")
def exchange_coins(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    current_engine.register_user(user_id, "Guest")
    success, message, data = current_engine.exchange_coins_to_money(user_id)
    profile = current_engine.get_profile(user_id)
    return jsonify({"success": success, "message": message, "wallet_bot": profile.wallet_bot, "coins": profile.coins, "data": data}), 200



# --- Social / Friend / Profile / Translation API Endpoints ---
