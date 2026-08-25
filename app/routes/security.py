"""Flask blueprint: security features (PIN lock)."""
from __future__ import annotations

from app.routes._helpers import (
    _check_rate_limit,
    _safe_int,
    _get_user_id_from_request,
    _require_auth_post,
    _require_auth_get,
)
from flask import Blueprint, current_app, jsonify, request

bp = Blueprint("security", __name__)


@_require_auth_post("set_pin")
@bp.post("/api/security/set-pin/<int:user_id>")
def set_pin(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    current_engine.register_user(user_id, "Guest")
    data = request.get_json(silent=True) or {}
    pin = str(data.get("pin", "")).strip()
    if not pin:
        return jsonify({"success": False, "message": "PIN is required"}), 400
    success, message = current_engine.set_pin(user_id, pin)
    return jsonify({"success": success, "message": message}), 200 if success else 400


@_require_auth_post("verify_pin")
@bp.post("/api/security/verify-pin/<int:user_id>")
def verify_pin(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    current_engine.register_user(user_id, "Guest")
    data = request.get_json(silent=True) or {}
    pin = str(data.get("pin", "")).strip()
    if not pin:
        return jsonify({"success": False, "message": "PIN is required"}), 400
    valid = current_engine.verify_pin(user_id, pin)
    return jsonify({"success": valid, "message": "PIN verified" if valid else "Invalid PIN"}), 200 if valid else 401


@_require_auth_get("pin_status")
@bp.get("/api/security/pin-status/<int:user_id>")
def pin_status(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    current_engine.register_user(user_id, "Guest")
    profile = current_engine.get_profile(user_id)
    return jsonify({"pin_set": profile.pin_set}), 200
