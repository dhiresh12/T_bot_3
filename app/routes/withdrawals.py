"""Flask blueprint: withdrawals endpoints."""
from __future__ import annotations

from app.routes._helpers import (
    _check_rate_limit,
    _safe_int,
    _get_user_id_from_request,
    _require_auth_post,
    _require_auth_get,
)
from flask import Blueprint, current_app, jsonify, request

bp = Blueprint("withdrawals", __name__)



@_require_auth_post("withdraw")
@bp.post("/api/withdraw/<int:user_id>")
def withdraw(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    payload = request.get_json(silent=True) or {}
    amount = float(payload.get("amount", current_engine.min_withdrawal))
    method = payload.get("method", "upi")
    details = payload.get("details", "")
    current_engine.register_user(user_id, "Guest")
    message = current_engine.request_withdrawal(user_id, amount, method, details)
    return jsonify({"message": message}), 200


@_require_auth_post("spin")



# --- Withdrawal proof uploads ---

@bp.post("/api/withdrawals/proof/<int:user_id>")
def upload_withdrawal_proof(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    current_engine.register_user(user_id, "Guest")
    payload = request.get_json(silent=True) or {}
    proof_url = payload.get("proof_url", "")
    request_id = payload.get("request_id", "")

    if not proof_url or not request_id:
        return jsonify({"error": "Missing proof_url or request_id"}), 400

    success, message = current_engine.upload_withdrawal_proof(user_id, proof_url, request_id)
    return jsonify({"success": success, "message": message}), 200



@bp.get("/api/withdrawals/proofs/<int:user_id>")
def get_withdrawal_proofs(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    current_engine.register_user(user_id, "Guest")
    proofs = current_engine.get_withdrawal_proofs(user_id)
    return jsonify({"proofs": proofs}), 200


# --- Transaction history ---



# --- Transaction history ---

@bp.get("/api/transactions/<int:user_id>")
def transaction_history(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    current_engine.register_user(user_id, "Guest")
    txn_type = request.args.get("type")
    limit = _safe_int(request.args.get("limit"), 50)
    transactions = current_engine.get_transaction_history(user_id, txn_type, limit)
    return jsonify({"transactions": transactions}), 200


# --- Admin Dashboard UI ---
