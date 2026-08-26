"""Flask blueprint: premium subscription endpoints."""
from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

bp = Blueprint("premium", __name__)


@bp.get("/api/premium/tiers")
def premium_tiers() -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    tiers = current_engine.premium_service.get_tiers()
    return jsonify({"tiers": tiers}), 200


@bp.get("/api/premium/subscription/<int:user_id>")
def get_subscription(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    current_engine.register_user(user_id, "Guest")
    sub = current_engine.premium_service.get_user_subscription(user_id)
    benefits = current_engine.premium_service.get_benefits(user_id)
    return jsonify({"subscription": sub, "benefits": benefits}), 200


@bp.post("/api/premium/purchase/<int:user_id>")
def purchase_subscription(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    payload = request.get_json(silent=True) or {}
    tier_id = payload.get("tier_id")
    payment_ref = payload.get("payment_ref", "")
    if not tier_id:
        return jsonify({"success": False, "message": "Missing tier_id"}), 400
    success, message, data = current_engine.premium_service.purchase_subscription(user_id, tier_id, payment_ref)
    return jsonify({"success": success, "message": message, "data": data}), 200
