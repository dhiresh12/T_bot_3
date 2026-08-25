"""Flask blueprint: achievement sharing rewards."""
from __future__ import annotations

from app.routes._helpers import (
    _check_rate_limit,
    _safe_int,
    _get_user_id_from_request,
    _require_auth_post,
    _require_auth_get,
)
from flask import Blueprint, current_app, jsonify, request

bp = Blueprint("achievements_share", __name__)


@_require_auth_post("share_achievement")
@_check_rate_limit("share_achievement", limit=3, window=3600)
@bp.post("/api/achievements/share/<int:user_id>")
def share_achievement(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    current_engine.register_user(user_id, "Guest")
    data = request.get_json(silent=True) or {}
    achievement_id = str(data.get("achievement_id", "")).strip()
    if not achievement_id:
        return jsonify({"success": False, "message": "achievement_id is required"}), 400
    success, message, reward_data = current_engine.record_share_reward(user_id, achievement_id)
    return jsonify({"success": success, "message": message, "data": reward_data}), 200 if success else 400
