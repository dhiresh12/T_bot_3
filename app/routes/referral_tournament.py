"""Flask blueprint: referral tournament."""
from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

bp = Blueprint("referral_tournament", __name__)


@bp.get("/api/tournament/leaderboard")
def tournament_leaderboard() -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    data = current_engine.get_tournament_leaderboard()
    return jsonify(data), 200
