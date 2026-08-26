"""Flask blueprint: transaction receipts."""
from __future__ import annotations

from app.routes._helpers import (
    _check_rate_limit,
    _safe_int,
    _get_user_id_from_request,
    _require_auth_post,
    _require_auth_get,
)
from flask import Blueprint, current_app, jsonify, request, render_template

bp = Blueprint("receipts", __name__)


@_require_auth_get("receipt", sensitive=True)
@bp.get("/api/receipt/<int:user_id>/<request_id>")
def api_receipt(user_id: int, request_id: str) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    current_engine.register_user(user_id, "Guest")
    receipt = current_engine.get_receipt(user_id, request_id)
    if not receipt:
        return jsonify({"error": "Receipt not found."}), 404
    return jsonify(receipt), 200


@bp.get("/receipt/<int:user_id>/<request_id>")
def printable_receipt(user_id: int, request_id: str) -> str:
    current_engine = current_app.config["engine"]
    current_engine.register_user(user_id, "Guest")
    receipt = current_engine.get_receipt(user_id, request_id)
    if not receipt:
        return jsonify({"error": "Receipt not found."}), 404
    return render_template("receipt.html", receipt=receipt)
