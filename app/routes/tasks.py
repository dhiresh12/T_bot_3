"""Flask blueprint: tasks endpoints."""
from __future__ import annotations

from app.routes._helpers import (
    _check_rate_limit,
    _safe_int,
    _get_user_id_from_request,
    _require_auth_post,
    _require_auth_get,
)
from flask import Blueprint, current_app, jsonify, request

bp = Blueprint("tasks", __name__)



@_require_auth_post("complete_task")
@bp.post("/api/tasks/complete/<int:user_id>/<task_id>")
def complete_task(user_id: int, task_id: str) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    current_engine.register_user(user_id, "Guest")
    completed, message = current_engine.complete_task(user_id, task_id)
    profile = current_engine.get_profile(user_id)
    return jsonify({"completed": completed, "message": message, "wallet": profile.wallet_bot, "coins": profile.coins}), 200





# --- New Features API Endpoints ---

@bp.get("/api/challenges/<int:user_id>")
def challenges(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    current_engine.register_user(user_id, "Guest")
    challenges = current_engine.get_daily_challenges(user_id)
    return jsonify({"challenges": challenges}), 200

@_require_auth_post("complete_challenge")
@bp.post("/api/challenges/complete/<int:user_id>/<challenge_id>")
def complete_challenge(user_id: int, challenge_id: str) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    current_engine.register_user(user_id, "Guest")
    success, message, data = current_engine.complete_daily_challenge(user_id, challenge_id)
    profile = current_engine.get_profile(user_id)
    return jsonify({"success": success, "message": message, "coins": profile.coins, "xp": profile.xp, "data": data}), 200



@bp.get("/api/achievements/<int:user_id>")
def achievements(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    current_engine.register_user(user_id, "Guest")
    achievements = current_engine.get_achievements(user_id)
    return jsonify({"achievements": achievements}), 200


@_require_auth_post("scratch")
@bp.post("/api/scratch/<int:user_id>")
def scratch(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    current_engine.register_user(user_id, "Guest")
    success, message, data = current_engine.scratch_card(user_id)
    profile = current_engine.get_profile(user_id)
    return jsonify({"success": success, "message": message, "coins": profile.coins, "scratch_cards_available": profile.scratch_cards_available, "data": data}), 200


@_require_auth_post("claim_scratch")
@bp.post("/api/scratch/claim-free/<int:user_id>")
def claim_scratch(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    current_engine.register_user(user_id, "Guest")
    success, message, data = current_engine.claim_scratch_card(user_id)
    profile = current_engine.get_profile(user_id)
    return jsonify({"success": success, "message": message, "scratch_cards_available": profile.scratch_cards_available, "data": data}), 200


@_require_auth_post("streak_insurance")
@bp.post("/api/streak/insurance/<int:user_id>")
def streak_insurance(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    current_engine.register_user(user_id, "Guest")
    success, message = current_engine.use_streak_insurance(user_id)
    profile = current_engine.get_profile(user_id)
    return jsonify({"success": success, "message": message, "streak_insurance": profile.streak_insurance, "snap_streak": profile.snap_streak}), 200



@bp.get("/api/referral/tier/<int:user_id>")
def referral_tier(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    current_engine.register_user(user_id, "Guest")
    tier_info = current_engine.process_referral_tier_upgrade(user_id)
    return jsonify(tier_info), 200

