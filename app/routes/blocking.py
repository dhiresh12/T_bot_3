"""Flask blueprint: user blocking and reporting."""
from __future__ import annotations

from app.routes._helpers import (
    _check_rate_limit,
    _safe_int,
    _get_user_id_from_request,
    _require_auth_post,
    _require_auth_get,
)
from flask import Blueprint, current_app, jsonify, request

bp = Blueprint("blocking", __name__)


@_require_auth_post("block_user")
@bp.post("/api/users/block/<int:user_id>")
def block_user(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    payload = request.get_json(silent=True) or {}
    target_user_id = payload.get("target_user_id")
    if not target_user_id:
        return jsonify({"error": "Missing 'target_user_id' in request body."}), 400
    current_engine.register_user(user_id, "Guest")
    current_engine.register_user(target_user_id, "Guest")
    success, message = current_engine.block_user(user_id, target_user_id)
    return jsonify({"success": success, "message": message}), 200


@_require_auth_post("unblock_user")
@bp.post("/api/users/unblock/<int:user_id>")
def unblock_user(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    payload = request.get_json(silent=True) or {}
    target_user_id = payload.get("target_user_id")
    if not target_user_id:
        return jsonify({"error": "Missing 'target_user_id' in request body."}), 400
    current_engine.register_user(user_id, "Guest")
    current_engine.register_user(target_user_id, "Guest")
    success, message = current_engine.unblock_user(user_id, target_user_id)
    return jsonify({"success": success, "message": message}), 200


@_require_auth_post("report_user")
@bp.post("/api/users/report/<int:user_id>")
def report_user(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    payload = request.get_json(silent=True) or {}
    target_user_id = payload.get("target_user_id")
    reason = payload.get("reason", "")
    if not target_user_id or not reason:
        return jsonify({"error": "Missing 'target_user_id' or 'reason' in request body."}), 400
    current_engine.register_user(user_id, "Guest")
    current_engine.register_user(target_user_id, "Guest")
    success, message = current_engine.report_user(user_id, target_user_id, reason)
    return jsonify({"success": success, "message": message}), 200


@_require_auth_get("blocked_users", sensitive=True)
@bp.get("/api/users/blocked/<int:user_id>")
def get_blocked_users(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    current_engine.register_user(user_id, "Guest")
    blocked = current_engine.get_blocked_users(user_id)
    return jsonify({"blocked_users": blocked}), 200
