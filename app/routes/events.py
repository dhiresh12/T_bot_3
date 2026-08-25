"""Flask blueprint: limited-time events."""
from __future__ import annotations

from app.routes._helpers import (
    _check_rate_limit,
    _safe_int,
    _get_user_id_from_request,
    _require_auth_post,
    _require_auth_get,
)
from flask import Blueprint, current_app, jsonify, request

bp = Blueprint("events", __name__)


@_require_auth_get("active_event")
@bp.get("/api/events/active")
def active_event() -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    event = current_engine.get_active_event()
    if event:
        return jsonify({"active": True, "event_id": event.get("id"), "title": event.get("title"), "description": event.get("description"), "emoji": event.get("emoji"), "reward": event.get("reward"), "end": event.get("end")}), 200
    return jsonify({"active": False}), 200


@_require_auth_post("claim_event")
@bp.post("/api/events/claim/<int:user_id>")
def claim_event(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    current_engine.register_user(user_id, "Guest")
    event = current_engine.get_active_event()
    if not event:
        return jsonify({"success": False, "message": "No active event"}), 404
    success, message, data = current_engine.claim_event_reward(user_id, event["id"])
    return jsonify({"success": success, "message": message, "data": data}), 200 if success else 400
