"""Flask blueprint: gamified onboarding quest."""
from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

bp = Blueprint("quests", __name__)


@bp.get("/api/quests/status/<int:user_id>")
def quest_status(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    data = current_engine.get_quest_status(user_id)
    return jsonify(data), 200


@bp.post("/api/quests/claim/<int:user_id>")
def claim_quest_reward(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    success, message, reward = current_engine.claim_quest_reward(user_id)
    return jsonify({"success": success, "message": message, "reward": reward}), 200
