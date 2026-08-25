"""Flask blueprint: admin analytics v2."""
from __future__ import annotations

from app.routes._helpers import (
    _check_rate_limit,
    _safe_int,
    _get_user_id_from_request,
    _require_auth_post,
    _require_auth_get,
)
from flask import Blueprint, current_app, jsonify, request

bp = Blueprint("analytics", __name__)


@bp.get("/api/admin/analytics/v2")
def admin_analytics_v2() -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    admin_key = request.headers.get("X-Admin-Key")
    if not admin_key or admin_key != current_engine.admin_key:
        return jsonify({"success": False, "message": "Admin access required"}), 403
    data = current_engine.get_admin_analytics_v2()
    return jsonify({"success": True, "data": data}), 200
