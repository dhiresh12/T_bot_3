"""Flask blueprint: web push notifications."""
from __future__ import annotations

from app.routes._helpers import (
    _check_rate_limit,
    _safe_int,
    _get_user_id_from_request,
    _require_auth_post,
    _require_auth_get,
)
from flask import Blueprint, current_app, jsonify, request

bp = Blueprint("push", __name__)


@_require_auth_post("push_subscribe")
@bp.post("/api/push/subscribe/<int:user_id>")
def push_subscribe(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    payload = request.get_json(silent=True) or {}
    endpoint = payload.get("endpoint", "")
    keys = payload.get("keys", {})
    current_engine.register_user(user_id, "Guest")
    success, message = current_engine.subscribe_push(user_id, endpoint, keys)
    return jsonify({"success": success, "message": message}), 200


@_require_auth_post("push_unsubscribe")
@bp.post("/api/push/unsubscribe/<int:user_id>")
def push_unsubscribe(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    payload = request.get_json(silent=True) or {}
    endpoint = payload.get("endpoint", "")
    current_engine.register_user(user_id, "Guest")
    success, message = current_engine.unsubscribe_push(user_id, endpoint)
    return jsonify({"success": success, "message": message}), 200


@_require_auth_get("push_subscriptions", sensitive=True)
@bp.get("/api/push/subscriptions/<int:user_id>")
def get_push_subscriptions(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    current_engine.register_user(user_id, "Guest")
    subscriptions = current_engine.get_push_subscriptions(user_id)
    return jsonify({"subscriptions": subscriptions}), 200
