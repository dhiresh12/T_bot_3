"""Flask blueprint: spin endpoints."""
from __future__ import annotations

from app.routes._helpers import (
    _check_rate_limit,
    _safe_int,
    _get_user_id_from_request,
    _require_auth_post,
    _require_auth_get,
)
from flask import Blueprint, current_app, jsonify, request

bp = Blueprint("spin", __name__)



@_require_auth_post("spin")
@bp.post("/api/spin/<int:user_id>")
def spin(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    current_engine.register_user(user_id, "Guest")
    success, message, gift = current_engine.spin_wheel(user_id)
    return jsonify({"success": success, "message": message, "gift": gift, "value": gift.get("coins", 0) if gift else 0}), 200


@_require_auth_post("redeem_more_ads")



@_require_auth_post("super_spin")
@bp.post("/api/spin/super/<int:user_id>")
def super_spin(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    current_engine.register_user(user_id, "Guest")
    success, message, gift = current_engine.super_spin(user_id)
    profile = current_engine.get_profile(user_id)
    return jsonify({"success": success, "message": message, "gift": gift, "coins": profile.coins, "super_spins_available": profile.super_spins_available}), 200


@_require_auth_post("mega_spin")



@_require_auth_post("mega_spin")
@bp.post("/api/spin/mega/<int:user_id>")
def mega_spin(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    current_engine.register_user(user_id, "Guest")
    success, message, gift = current_engine.mega_spin(user_id)
    profile = current_engine.get_profile(user_id)
    return jsonify({"success": success, "message": message, "gift": gift, "coins": profile.coins, "mega_spins_available": profile.mega_spins_available}), 200

