"""Flask blueprint: achievement showcase."""
from __future__ import annotations

from app.routes._helpers import (
    _check_rate_limit,
    _safe_int,
    _get_user_id_from_request,
    _require_auth_post,
    _require_auth_get,
)
from flask import Blueprint, current_app, jsonify, request

bp = Blueprint("achievements_showcase", __name__)


@_require_auth_get("showcase", sensitive=True)
@bp.get("/api/achievements/showcase/<int:user_id>")
def get_showcase(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    current_engine.register_user(user_id, "Guest")
    showcased = current_engine.get_showcased_achievements(user_id)
    all_achievements = current_engine.get_achievements(user_id)
    return jsonify({"showcased": showcased, "all_achievements": all_achievements}), 200


@_require_auth_post("showcase")
@bp.post("/api/achievements/showcase/<int:user_id>")
def set_showcase(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    payload = request.get_json(silent=True) or {}
    achievement_ids = payload.get("achievement_ids", [])
    if not isinstance(achievement_ids, list):
        return jsonify({"error": "achievement_ids must be a list."}), 400
    current_engine.register_user(user_id, "Guest")
    success, message = current_engine.set_showcased_achievements(user_id, achievement_ids)
    return jsonify({"success": success, "message": message}), 200
