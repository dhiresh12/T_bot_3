"""Flask blueprint: leaderboard endpoints."""
from __future__ import annotations

from app.routes._helpers import (
    _check_rate_limit,
    _safe_int,
    _get_user_id_from_request,
    _require_auth_post,
    _require_auth_get,
)
from flask import Blueprint, current_app, jsonify, request

bp = Blueprint("leaderboard", __name__)



@bp.get("/api/leaderboard/level")
def level_leaderboard() -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    return jsonify(current_engine.get_level_leaderboard()), 200


@_require_auth_get("leaderboard_rewards", sensitive=True)



@_require_auth_get("leaderboard_rewards", sensitive=True)
@bp.get("/api/leaderboard/rewards/<int:user_id>")
def leaderboard_rewards(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    current_engine.register_user(user_id, "Guest")
    reward_info = current_engine.check_leaderboard_rewards(user_id)
    return jsonify(reward_info), 200


@_require_auth_post("claim_leaderboard_reward")



@_require_auth_post("claim_leaderboard_reward")
@bp.post("/api/leaderboard/claim-reward/<int:user_id>")
def claim_leaderboard_reward(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    current_engine.register_user(user_id, "Guest")
    success, message, data = current_engine.claim_leaderboard_reward(user_id)
    profile = current_engine.get_profile(user_id)
    return jsonify({"success": success, "message": message, "coins": profile.coins, "xp": profile.xp, "data": data}), 200

