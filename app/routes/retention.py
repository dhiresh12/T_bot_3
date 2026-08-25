"""Flask blueprint: retention and engagement endpoints."""
from __future__ import annotations

from app.routes._helpers import (
    _check_rate_limit,
    _safe_int,
    _get_user_id_from_request,
    _require_auth_post,
    _require_auth_get,
)
from flask import Blueprint, current_app, jsonify, request

bp = Blueprint("retention", __name__)


@_require_auth_post("streak_reminder")
@bp.post("/api/retention/streak-reminder/<int:user_id>")
def streak_reminder(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    current_engine.send_daily_streak_reminder(user_id)
    return jsonify({"success": True, "message": "Streak reminder sent."}), 200


@_require_auth_post("weekly_summary")
@bp.post("/api/retention/weekly-summary/<int:user_id>")
def weekly_summary(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    current_engine.send_weekly_summary(user_id)
    return jsonify({"success": True, "message": "Weekly summary sent."}), 200


@_require_auth_get("activity_feed")
@bp.get("/api/social/activity-feed/<int:user_id>")
def activity_feed(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    limit = int(request.args.get("limit", 20))
    feed = current_engine.get_friend_activity_feed(user_id, limit=limit)
    return jsonify({"feed": feed}), 200
