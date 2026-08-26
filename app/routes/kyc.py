"""Flask blueprint: KYC endpoints."""
from __future__ import annotations

from app.routes._helpers import (
    _check_rate_limit,
    _safe_int,
    _get_user_id_from_request,
    _require_auth_post,
    _require_auth_get,
)
from flask import Blueprint, current_app, jsonify, request

bp = Blueprint("kyc", __name__)


@_require_auth_post("kyc_submit")
@bp.post("/api/kyc/submit/<int:user_id>")
def kyc_submit(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    payload = request.get_json(silent=True) or {}
    document_url = payload.get("document_url", "")
    if not document_url:
        return jsonify({"error": "Missing 'document_url' in request body."}), 400
    current_engine.register_user(user_id, "Guest")
    success, message = current_engine.submit_kyc(user_id, document_url)
    return jsonify({"success": success, "message": message}), 200


@_require_auth_get("kyc_status", sensitive=True)
@bp.get("/api/kyc/status/<int:user_id>")
def kyc_status(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    current_engine.register_user(user_id, "Guest")
    status = current_engine.get_kyc_status(user_id)
    return jsonify(status), 200


@bp.post("/api/admin/kyc/approve")
def admin_kyc_approve() -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    admin_key = request.headers.get("X-Admin-Key")
    if not admin_key or admin_key != current_engine.admin_key:
        return jsonify({"error": "Access Denied. Invalid or missing admin key."}), 403
    payload = request.get_json(silent=True) or {}
    user_id = payload.get("user_id")
    if not user_id:
        return jsonify({"error": "Missing 'user_id' in request body."}), 400
    current_engine.register_user(user_id, "Guest")
    success, message = current_engine.approve_kyc(int(payload.get("admin_id", 0)), user_id)
    return jsonify({"success": success, "message": message}), 200


@bp.post("/api/admin/kyc/reject")
def admin_kyc_reject() -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    admin_key = request.headers.get("X-Admin-Key")
    if not admin_key or admin_key != current_engine.admin_key:
        return jsonify({"error": "Access Denied. Invalid or missing admin key."}), 403
    payload = request.get_json(silent=True) or {}
    user_id = payload.get("user_id")
    if not user_id:
        return jsonify({"error": "Missing 'user_id' in request body."}), 400
    current_engine.register_user(user_id, "Guest")
    success, message = current_engine.reject_kyc(int(payload.get("admin_id", 0)), user_id)
    return jsonify({"success": success, "message": message}), 200
