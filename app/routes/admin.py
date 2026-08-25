"""Flask blueprint: admin endpoints."""
from __future__ import annotations
import os

from app.routes._helpers import (
    _check_rate_limit,
    _safe_int,
    _get_user_id_from_request,
    _require_auth_post,
    _require_auth_get,
)
from flask import Blueprint, current_app, jsonify, render_template, request

bp = Blueprint("admin", __name__)



# --- Admin API Endpoints (New/Moved) ---

@bp.get("/api/admin/dashboard")
def admin_dashboard() -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    # Security Improvement: Check for a secret header
    admin_key = request.headers.get("X-Admin-Key")
    if not admin_key or admin_key != current_engine.admin_key:
        return jsonify({"error": "Access Denied. Invalid or missing admin key."}), 403

    return jsonify(current_engine.admin_service.get_admin_dashboard()), 200



@bp.get("/api/admin/users")
def admin_users() -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    # Security Improvement: Check for a secret header
    admin_key = request.headers.get("X-Admin-Key")
    if not admin_key or admin_key != current_engine.admin_key:
        return jsonify({"error": "Access Denied. Invalid or missing admin key."}), 403

    return jsonify(current_engine.admin_service.get_all_users_summary()), 200



@bp.get("/api/admin/view_user/<int:user_id>")
def admin_view_user(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    admin_key = request.headers.get("X-Admin-Key")
    if not admin_key or admin_key != current_engine.admin_key:
        return jsonify({"error": "Access Denied. Invalid or missing admin key."}), 403

    target_profile = current_engine.admin_service.get_user_full_profile(user_id)
    if not target_profile:
        return jsonify({"error": f"User {user_id} not found."}), 404

    safe_fields = {"user_id", "name", "coins", "wallet_bot", "invite_count", "admin", "registered_at", "tier", "level"}
    profile_dict = {k: getattr(target_profile, k) for k in safe_fields if hasattr(target_profile, k)}
    return jsonify(profile_dict), 200



@bp.post("/api/admin/set")
def admin_set_config() -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    # Security Improvement: Check for a secret header
    admin_key = request.headers.get("X-Admin-Key")
    if not admin_key or admin_key != current_engine.admin_key:
        return jsonify({"error": "Access Denied. Invalid or missing admin key."}), 403
        
    payload = request.get_json(silent=True) or {}
    setting = payload.get("setting")
    value = payload.get("value")

    if not setting or value is None:
        return jsonify({"error": "Missing 'setting' or 'value' in request body."}), 400
    
    success, message = current_engine.admin_service.update_bot_config(setting, value)
    return jsonify({"success": success, "message": message}), 200



@bp.post("/api/admin/commands/<command>")
def admin_command(command: str) -> tuple[dict, int]:
    """
    Generic admin command endpoint.
    Supports commands like 'bonus' to update a bot-level setting.
    """
    current_engine = current_app.config["engine"]
    admin_key = request.headers.get("X-Admin-Key")
    if not admin_key or admin_key != current_engine.admin_key:
        return jsonify({"error": "Access Denied. Invalid or missing admin key."}), 403

    payload = request.get_json(silent=True) or {}
    value = payload.get("value")

    # Map simple admin commands to engine config attributes
    config_map = {
        "bonus": "bonus_value",
        "min_withdrawal": "min_withdrawal",
        "daily_ads_limit": "daily_ads_limit",
        "daily_spin_limit": "daily_spin_limit",
        "coins_to_rupee_rate": "coins_to_rupee_rate",
        "withdrawal_fee_percent": "withdrawal_fee_percent",
    }
    setting = config_map.get(command)
    if setting is None:
        return jsonify({"error": f"Unknown admin command '{command}'."}), 400

    success, message = current_engine.admin_service.update_bot_config(setting, value)
    return jsonify({"success": success, "message": message}), 200



@bp.post("/api/admin/commands/bonus")
def admin_command_bonus() -> tuple[dict, int]:
    """Admin route to update the daily bonus value."""
    current_engine = current_app.config["engine"]
    admin_key = request.headers.get("X-Admin-Key")
    if not admin_key or admin_key != current_engine.admin_key:
        return jsonify({"error": "Access Denied. Invalid or missing admin key."}), 403

    payload = request.get_json(silent=True) or {}
    value = payload.get("value")
    if value is None:
        return jsonify({"error": "Missing 'value' in request body."}), 400

    try:
        current_engine.bonus_value = float(value)
    except (ValueError, TypeError):
        return jsonify({"error": "'value' must be a number."}), 400

    return jsonify({"success": True, "message": f"Bonus value updated to '{current_engine.bonus_value}'."}), 200



@bp.post("/api/admin/broadcast")
def admin_broadcast() -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    admin_key = request.headers.get("X-Admin-Key")
    if not admin_key or admin_key != current_engine.admin_key:
        return jsonify({"error": "Access Denied. Invalid or missing admin key."}), 403

    payload = request.get_json(silent=True) or {}
    message = payload.get("message", "")
    sender_id = payload.get("sender_id")
    if not message:
        return jsonify({"error": "Missing 'message' in request body."}), 400
    try:
        sender_id = int(sender_id) if sender_id is not None else 0
    except (TypeError, ValueError):
        sender_id = 0

    result = current_engine.broadcast_message(message, sender_id)
    return jsonify(result), 200



@bp.post("/api/admin/ban/<int:user_id>")
def admin_ban_user(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    admin_key = request.headers.get("X-Admin-Key")
    if not admin_key or admin_key != current_engine.admin_key:
        return jsonify({"error": "Access Denied. Invalid or missing admin key."}), 403

    payload = request.get_json(silent=True) or {}
    reason = payload.get("reason", "")
    success, message = current_engine.ban_user(user_id, reason)
    return jsonify({"success": success, "message": message}), 200



@bp.post("/api/admin/unban/<int:user_id>")
def admin_unban_user(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    admin_key = request.headers.get("X-Admin-Key")
    if not admin_key or admin_key != current_engine.admin_key:
        return jsonify({"error": "Access Denied. Invalid or missing admin key."}), 403

    success, message = current_engine.unban_user(user_id)
    return jsonify({"success": success, "message": message}), 200



@bp.post("/api/admin/kick/<int:user_id>")
def admin_kick_user(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    admin_key = request.headers.get("X-Admin-Key")
    if not admin_key or admin_key != current_engine.admin_key:
        return jsonify({"error": "Access Denied. Invalid or missing admin key."}), 403

    success, message = current_engine.kick_user(user_id)
    return jsonify({"success": success, "message": message}), 200



@bp.post("/api/admin/backup")
def admin_backup() -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    # Security Improvement: Check for a secret header
    admin_key = request.headers.get("X-Admin-Key")
    if not admin_key or admin_key != current_engine.admin_key:
        return jsonify({"error": "Access Denied. Invalid or missing admin key."}), 403

    message = current_engine.admin_service.create_backup()
    return jsonify({"message": message}), 200



@bp.post("/api/admin/rollback")
def admin_rollback() -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    # Security Improvement: Check for a secret header
    admin_key = request.headers.get("X-Admin-Key")
    if not admin_key or admin_key != current_engine.admin_key:
        return jsonify({"error": "Access Denied. Invalid or missing admin key."}), 403
        
    payload = request.get_json(silent=True) or {}
    filename = payload.get("filename")
    if not filename:
        return jsonify({"error": "Missing 'filename' in request body."}), 400
    
    success = current_engine.admin_service.rollback_to_backup(filename)
    message = "Rollback successful." if success else "Rollback failed. File not found or an error occurred."
    return jsonify({"success": success, "message": message}), 200



@bp.post("/api/admin/approve_withdrawal")
def admin_approve_withdrawal() -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    # Security Improvement: Check for a secret header
    admin_key = request.headers.get("X-Admin-Key")
    if not admin_key or admin_key != current_engine.admin_key:
        return jsonify({"error": "Access Denied. Invalid or missing admin key."}), 403

    admin_id = int(os.getenv("ADMIN_ID", 1))
    payload = request.get_json(silent=True) or {}
    user_id = payload.get("user_id")
    request_id = payload.get("request_id")
    verification_code = payload.get("verification_code")

    if not all([user_id, request_id, verification_code]):
        return jsonify({"error": "Missing user_id, request_id, or verification_code in request body."}), 400
    
    message = current_engine.approve_withdrawal(admin_id, user_id, request_id, verification_code)
    return jsonify({"message": message}), 200



@bp.get("/api/admin/backups")
def admin_backups() -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    admin_key = request.headers.get("X-Admin-Key")
    if not admin_key or admin_key != current_engine.admin_key:
        return jsonify({"error": "Access Denied. Invalid or missing admin key."}), 403
    
    backups = current_engine.admin_service.list_backups()
    return jsonify(backups), 200


@bp.get("/api/admin/total_balance_over_time")
def admin_total_balance_over_time() -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    admin_key = request.headers.get("X-Admin-Key")
    if not admin_key or admin_key != current_engine.admin_key:
        return jsonify({"error": "Access Denied. Invalid or missing admin key."}), 403
    
    data = current_engine.admin_service.get_total_coin_balance_over_time()
    return jsonify(data), 200



@bp.get("/api/admin/user_tier_distribution")
def admin_user_tier_distribution() -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    admin_key = request.headers.get("X-Admin-Key")
    if not admin_key or admin_key != current_engine.admin_key:
        return jsonify({"error": "Access Denied. Invalid or missing admin key."}), 403
    
    data = current_engine.admin_service.get_user_tier_distribution()
    return jsonify(data), 200



@bp.get("/api/admin/user_registrations_over_time")
def admin_user_registrations_over_time() -> tuple[dict, int]:
    """Returns the number of new user registrations grouped by date."""
    current_engine = current_app.config["engine"]
    admin_key = request.headers.get("X-Admin-Key")
    if not admin_key or admin_key != current_engine.admin_key:
        return jsonify({"error": "Access Denied. Invalid or missing admin key."}), 403
    
    data = current_engine.admin_service.get_user_registrations_over_time()
    return jsonify(data), 200












@bp.post("/api/admin/edit_user/<int:user_id>")
def admin_edit_user(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    admin_key = request.headers.get("X-Admin-Key")
    if not admin_key or admin_key != current_engine.admin_key:
        return jsonify({"error": "Access Denied. Invalid or missing admin key."}), 403

    payload = request.get_json(silent=True) or {}
    if not payload:
        return jsonify({"error": "Missing update data in request body."}), 400

    # Sanitize payload to only allow specific fields to be edited. 'coins' is intentionally left out for now.
    allowed_updates = {
        "admin": payload.get("admin"),
        "invite_count": payload.get("invite_count"),
        "total_ads_watched": payload.get("total_ads_watched"),
        "daily_spin_count": payload.get("daily_spin_count"),
        "wallet_bot": payload.get("wallet_bot"),
        "wallet_app": payload.get("wallet_app"),
    }
    # Filter out None values so we don't accidentally set fields to null
    updates_to_apply = {k: v for k, v in allowed_updates.items() if v is not None}

    success, message = current_engine.admin_service.edit_user_profile(user_id, updates_to_apply)
    return jsonify({"success": success, "message": message}), 200


# --- User Search / Discovery ---



# --- Admin manual credit ---

@bp.post("/api/admin/send-coins")
def admin_send_coins() -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    admin_key = request.headers.get("X-Admin-Key")
    if not admin_key or admin_key != current_engine.admin_key:
        return jsonify({"error": "Access Denied"}), 403

    payload = request.get_json(silent=True) or {}
    target_user_id = payload.get("target_user_id")
    amount = payload.get("amount")
    reason = payload.get("reason", "")

    if not target_user_id or amount is None:
        return jsonify({"error": "Missing target_user_id or amount"}), 400

    try:
        target_user_id = int(target_user_id)
        amount = int(amount)
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid user_id or amount"}), 400

    admin_id = int(os.getenv("ADMIN_ID", 1))
    success, message = current_engine.admin_send_coins(admin_id, target_user_id, amount, reason)
    return jsonify({"success": success, "message": message}), 200


# --- Withdrawal proof uploads ---


@bp.get("/admin")
def admin_ui() -> str:
    """Renders the dedicated Admin Dashboard UI."""
    admin_key = request.args.get("admin_key") or request.headers.get("X-Admin-Key")
    engine = current_app.config.get("engine")
    if not engine or not admin_key or admin_key != engine.admin_key:
        return "Access Denied", 403
    
    return render_template("admin.html", admin_key=admin_key)
