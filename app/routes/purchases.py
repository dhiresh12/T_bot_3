"""Flask blueprint: in-app purchase history."""
from __future__ import annotations

from app.routes._helpers import (
    _check_rate_limit,
    _safe_int,
    _get_user_id_from_request,
    _require_auth_post,
    _require_auth_get,
)
from flask import Blueprint, current_app, jsonify, request, render_template

bp = Blueprint("purchases", __name__)


@_require_auth_get("purchases", sensitive=True)
@bp.get("/api/purchases/<int:user_id>")
def get_purchases(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    current_engine.register_user(user_id, "Guest")
    purchases = current_engine.get_purchases(user_id)
    return jsonify({"purchases": purchases}), 200


@_require_auth_get("purchase_receipt", sensitive=True)
@bp.get("/api/purchases/receipt/<int:user_id>/<purchase_id>")
def get_purchase_receipt(user_id: int, purchase_id: str) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    current_engine.register_user(user_id, "Guest")
    receipt = current_engine.get_purchase_receipt(user_id, purchase_id)
    if not receipt:
        return jsonify({"error": "Purchase receipt not found."}), 404
    return jsonify(receipt), 200
