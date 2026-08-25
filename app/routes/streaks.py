"""Flask blueprint: daily streak rewards."""
from __future__ import annotations

from app.routes._helpers import (
    _check_rate_limit,
    _safe_int,
    _get_user_id_from_request,
    _require_auth_post,
    _require_auth_get,
)
from flask import Blueprint, current_app, jsonify, request

bp = Blueprint("streaks", __name__)


@_require_auth_get("streak_info")
@bp.get("/api/streak/info/<int:user_id>")
def streak_info(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    current_engine.register_user(user_id, "Guest")
    info = current_engine.get_daily_login_streak_info(user_id)
    return jsonify(info), 200


@_require_auth_post("claim_streak")
@_check_rate_limit("claim_streak", limit=1, window=86400)
@bp.post("/api/streak/claim/<int:user_id>")
def claim_streak(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    current_engine.register_user(user_id, "Guest")
    success, message, data = current_engine.claim_daily_login_reward(user_id)
    return jsonify({"success": success, "message": message, "data": data}), 200 if success else 400
