"""Flask blueprint: notifications endpoints."""
from __future__ import annotations

from app.routes._helpers import (
    _check_rate_limit,
    _safe_int,
    _get_user_id_from_request,
    _require_auth_post,
    _require_auth_get,
)
from flask import Blueprint, current_app, jsonify, request

bp = Blueprint("notifications", __name__)



@_require_auth_get("notifications", sensitive=True)
@bp.get("/api/notifications/<int:user_id>")
def notifications(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    current_engine.register_user(user_id, "Guest")
    notifs = current_engine.get_notifications(user_id)
    unread = current_engine.get_profile(user_id).unread_notifications
    return jsonify({"notifications": notifs, "unread_count": unread}), 200


@_require_auth_post("mark_notifications_read")



@_require_auth_post("mark_notifications_read")
@bp.post("/api/notifications/mark-read/<int:user_id>")
def mark_notifications_read(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    current_engine.register_user(user_id, "Guest")
    count = current_engine.mark_notifications_read(user_id)
    return jsonify({"success": True, "message": f"Marked {count} notifications as read.", "unread_count": 0}), 200

