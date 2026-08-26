"""Flask blueprint: level perks."""
from __future__ import annotations

from app.routes._helpers import (
    _check_rate_limit,
    _safe_int,
    _get_user_id_from_request,
    _require_auth_post,
    _require_auth_get,
)
from flask import Blueprint, current_app, jsonify, request

bp = Blueprint("perks", __name__)


@_require_auth_get("perks", sensitive=True)
@bp.get("/api/perks/<int:user_id>")
def get_perks(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    current_engine.register_user(user_id, "Guest")
    perks = current_engine.get_perks(user_id)
    return jsonify(perks), 200
