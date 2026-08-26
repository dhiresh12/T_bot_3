"""Flask blueprint: enhanced withdrawal features."""
from __future__ import annotations

from app.routes._helpers import (
    _check_rate_limit,
    _safe_int,
    _get_user_id_from_request,
    _require_auth_post,
    _require_auth_get,
)
from flask import Blueprint, current_app, jsonify, request

bp = Blueprint("withdrawal_enhanced", __name__)


@_require_auth_post("withdraw_schedule")
@bp.post("/api/withdraw/schedule/<int:user_id>")
def schedule_withdrawal(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    payload = request.get_json(silent=True) or {}
    amount = float(payload.get("amount", current_engine.min_withdrawal))
    frequency = payload.get("frequency", "weekly")
    method = payload.get("method", "upi")
    details = payload.get("details", "")
    current_engine.register_user(user_id, "Guest")
    success, message = current_engine.schedule_withdrawal(user_id, amount, frequency, method, details)
    return jsonify({"success": success, "message": message}), 200


@_require_auth_get("withdraw_schedules", sensitive=True)
@bp.get("/api/withdraw/schedules/<int:user_id>")
def get_schedules(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    current_engine.register_user(user_id, "Guest")
    schedules = current_engine.get_withdrawal_schedules(user_id)
    return jsonify({"schedules": schedules}), 200


@_require_auth_post("verify_account")
@bp.post("/api/withdraw/verify-account/<int:user_id>")
def verify_account(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    payload = request.get_json(silent=True) or {}
    account_number = payload.get("account_number", "")
    ifsc = payload.get("ifsc", "")
    account_holder = payload.get("account_holder", "")
    if not account_number or not ifsc or not account_holder:
        return jsonify({"error": "Missing account details."}), 400
    current_engine.register_user(user_id, "Guest")
    success, message = current_engine.verify_bank_account(user_id, account_number, ifsc, account_holder)
    return jsonify({"success": success, "message": message}), 200


@_require_auth_get("verified_accounts", sensitive=True)
@bp.get("/api/withdraw/verified-accounts/<int:user_id>")
def get_verified_accounts(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    current_engine.register_user(user_id, "Guest")
    accounts = current_engine.get_verified_bank_accounts(user_id)
    return jsonify({"accounts": accounts}), 200
