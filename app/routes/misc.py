"""Flask blueprint: misc endpoints."""
from __future__ import annotations

from app.routes._helpers import (
    _check_rate_limit,
    _safe_int,
    _get_user_id_from_request,
    _require_auth_post,
    _require_auth_get,
)
from flask import Blueprint, current_app, jsonify, request

bp = Blueprint("misc", __name__)



@bp.get("/health")
def health() -> tuple[dict, int]:
    return jsonify({"status": "ok"}), 200



@bp.get("/api/sections/<int:user_id>")
def sections(user_id: int) -> tuple[dict, int]:
    engine = current_app.config.get("engine")
    if engine is None:
        return jsonify({"user_id": user_id, "sections": []}), 200
    engine.register_user(user_id, "Guest")
    profile = engine.get_profile(user_id)
    return jsonify(
        {
            "user_id": profile.user_id,
            "sections": [
                {"key": "ads", "title": "Watch Ads", "enabled": True},
                {"key": "tasks", "title": "Daily Tasks", "enabled": True},
                {"key": "invite", "title": "Invite Friends", "enabled": True},
                {"key": "wallet", "title": "Wallet", "enabled": True},
            ],
        }
    ), 200


# --- User-facing API Endpoints (Moved from mini_app.py) ---

@_require_auth_post("bonus")



# --- User-facing API Endpoints (Moved from mini_app.py) ---

@_require_auth_post("bonus")
@bp.post("/api/bonus/<int:user_id>")
def bonus(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    payload = request.get_json(silent=True) or {}
    name = payload.get("name", "User")
    current_engine.register_user(user_id, name)
    reply = current_engine.handle_command(user_id, "bonus")
    profile = current_engine.get_profile(user_id)
    return jsonify({"message": reply, "wallet": profile.wallet_bot, "coins": profile.coins}), 200


@_require_auth_get("profile", sensitive=True)



@bp.post("/api/invite/<int:user_id>")
def invite(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    current_engine.register_user(user_id, "Guest")
    # The invite_user method is now called by register_user if inviter_id is present.
    # For direct API call, we might need a specific endpoint if it's not handled by /start.
    # For now, we'll simulate the reward for the inviter if this was a direct invite.
    # This might need refinement based on how the mini-app actually triggers invites.
    # For now, let's assume this endpoint is for getting invite count.
    profile = current_engine.get_profile(user_id)
    return jsonify({"invite_count": profile.invite_count, "wallet": profile.wallet_bot, "coins": profile.coins}), 200



@bp.get("/api/help/<int:user_id>")
def help_endpoint(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    language = request.args.get("lang", "en")
    current_engine.register_user(user_id, "Guest")
    return jsonify(current_engine.get_help(language)), 200


@_require_auth_get("dashboard", sensitive=True)



@_require_auth_get("dashboard", sensitive=True)
@bp.get("/api/dashboard/<int:user_id>")
def dashboard(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    current_engine.register_user(user_id, "Guest")
    return jsonify(current_engine.get_dashboard(user_id)), 200



@bp.get("/api/engagement/<int:user_id>")
def engagement(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    current_engine.register_user(user_id, "Guest")
    profile = current_engine.get_profile(user_id)
    return jsonify(
        {
            "trust_feed": current_engine.engagement.build_trust_feed(),
            "progress": current_engine.engagement.build_progress_snapshot(profile.wallet_bot, profile.coins),
        }
    ), 200



@bp.get("/api/support")
def support() -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    return jsonify(current_engine.support.get_faq()), 200



@bp.post("/api/support/message")
def support_message() -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    payload = request.get_json(silent=True) or {}
    return jsonify(current_engine.support.build_support_message(payload.get("message", ""))), 200



@bp.get("/api/leaderboard")
def leaderboard() -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    return jsonify(current_engine.get_leaderboard()), 200


@_require_auth_post("withdraw")



@_require_auth_post("add_xp")
@bp.post("/api/xp/add/<int:user_id>")
def add_xp(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    payload = request.get_json(silent=True) or {}
    amount = int(payload.get("amount", 0))
    current_engine.register_user(user_id, "Guest")
    if amount <= 0:
        return jsonify({"error": "Invalid XP amount."}), 400
    result = current_engine.add_xp(user_id, amount)
    profile = current_engine.get_profile(user_id)
    return jsonify({"success": True, "xp": profile.xp, "level": profile.level, "data": result}), 200

# --- Shop API endpoints ---



@_require_auth_post("send_coins")
@bp.post("/api/coins/send/<int:user_id>")
def send_coins(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    payload = request.get_json(silent=True) or {}
    to_user_id = payload.get("to_user_id")
    amount = int(payload.get("amount", 0))
    if not to_user_id or amount <= 0:
        return jsonify({"error": "Missing 'to_user_id' or invalid 'amount'."}), 400
    current_engine.register_user(user_id, "Guest")
    current_engine.register_user(to_user_id, "Guest")
    success, message, data = current_engine.send_coins_to_user(user_id, to_user_id, amount)
    profile = current_engine.get_profile(user_id)
    return jsonify({"success": success, "message": message, "coins": profile.coins, "data": data}), 200


@_require_auth_post("update_privacy")



# --- User Search / Discovery ---

@bp.get("/api/users/search")
def search_users() -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    query = request.args.get("q", "")
    limit = _safe_int(request.args.get("limit"), 20)
    results = current_engine.search_users(query, limit)
    return jsonify({"results": results}), 200



@bp.get("/api/users/discover/<int:user_id>")
def discover_users(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    current_engine.register_user(user_id, "Guest")
    data = current_engine.get_user_discovery(user_id)
    return jsonify(data), 200


# --- Admin manual credit ---



# --- Admin Dashboard UI ---


# --- A/B Testing ---

@_require_auth_get("ab_variant")
@bp.get("/api/ab/variant/<int:user_id>")
def ab_variant(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    current_engine.register_user(user_id, "Guest")
    test_name = request.args.get("test", "default")
    variant = current_engine.get_ab_variant(user_id, test_name)
    return jsonify({"variant": variant}), 200


# --- Offline Sync ---

@_require_auth_post("offline_sync")
@bp.post("/api/offline/sync/<int:user_id>")
def offline_sync(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    current_engine.register_user(user_id, "Guest")
    synced = current_engine.process_offline_actions(user_id)
    return jsonify({"success": True, "synced": synced}), 200


# --- A/B Testing ---

@_require_auth_get("ab_variant")
@bp.get("/api/ab/variant/<int:user_id>")
def ab_variant(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    current_engine.register_user(user_id, "Guest")
    test_name = request.args.get("test", "default")
    variant = current_engine.get_ab_variant(user_id, test_name)
    return jsonify({"variant": variant}), 200


# --- Offline Sync ---

@_require_auth_post("offline_sync")
@bp.post("/api/offline/sync/<int:user_id>")
def offline_sync(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    current_engine.register_user(user_id, "Guest")
    synced = current_engine.process_offline_actions(user_id)
    return jsonify({"success": True, "synced": synced}), 200

# --- PWA Manifest ---

@bp.get("/manifest.json")
def pwa_manifest() -> tuple[dict, int]:
    return jsonify({
        "name": "Xio_PayPlus",
        "short_name": "XioPay",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#0a0e1a",
        "theme_color": "#6366f1",
        "icons": [
            {"src": "https://cdn.jsdelivr.net/npm/@xio/icon@1.0.0/icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "https://cdn.jsdelivr.net/npm/@xio/icon@1.0.0/icon-512.png", "sizes": "512x512", "type": "image/png"}
        ]
    }), 200
