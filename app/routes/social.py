"""Flask blueprint: social endpoints."""
from __future__ import annotations

from app.routes._helpers import (
    _check_rate_limit,
    _safe_int,
    _get_user_id_from_request,
    _require_auth_post,
    _require_auth_get,
)
from flask import Blueprint, current_app, jsonify, request

bp = Blueprint("social", __name__)



@_require_auth_get("profile", sensitive=True)
@bp.get("/api/profile/<int:user_id>")
def profile(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    current_engine.register_user(user_id, "Guest")
    profile = current_engine.get_profile(user_id)
    return jsonify(
        {
            "user_id": profile.user_id,
            "name": profile.name,
            "wallet": profile.wallet_bot,
            "coins": profile.coins,
            "activity_count": current_engine.get_activity_count(profile),
        }
    ), 200


@_require_auth_post("social_share")
@bp.post("/api/social/share/<int:user_id>")
def social_share(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    payload = request.get_json(silent=True) or {}
    platform = payload.get("platform", "telegram")
    current_engine.register_user(user_id, "Guest")
    success, message, data = current_engine.share_social(user_id, platform)
    profile = current_engine.get_profile(user_id)
    return jsonify({"success": success, "message": message, "coins": profile.coins, "xp": profile.xp, "data": data}), 200




# --- Social / Friend / Profile / Translation API Endpoints ---

@_require_auth_post("send_friend_request")
@bp.post("/api/friends/request/<int:user_id>")
def send_friend_request(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    payload = request.get_json(silent=True) or {}
    to_user_id = payload.get("to_user_id")
    if not to_user_id:
        return jsonify({"error": "Missing 'to_user_id' in request body."}), 400
    current_engine.register_user(user_id, "Guest")
    current_engine.register_user(to_user_id, "Guest")
    success, message = current_engine.send_friend_request(user_id, to_user_id)
    return jsonify({"success": success, "message": message}), 200


@_require_auth_post("accept_friend_request")
@bp.post("/api/friends/accept/<int:user_id>")
def accept_friend_request(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    payload = request.get_json(silent=True) or {}
    request_id = payload.get("request_id")
    if not request_id:
        return jsonify({"error": "Missing 'request_id' in request body."}), 400
    current_engine.register_user(user_id, "Guest")
    success, message = current_engine.accept_friend_request(user_id, request_id)
    return jsonify({"success": success, "message": message}), 200


@_require_auth_post("reject_friend_request")
@bp.post("/api/friends/reject/<int:user_id>")
def reject_friend_request(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    payload = request.get_json(silent=True) or {}
    request_id = payload.get("request_id")
    if not request_id:
        return jsonify({"error": "Missing 'request_id' in request body."}), 400
    current_engine.register_user(user_id, "Guest")
    success, message = current_engine.reject_friend_request(user_id, request_id)
    return jsonify({"success": success, "message": message}), 200


@_require_auth_get("friend_requests", sensitive=True)
@bp.get("/api/friends/requests/<int:user_id>")
def friend_requests(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    current_engine.register_user(user_id, "Guest")
    requests = current_engine.get_friend_requests(user_id)
    return jsonify({"requests": requests}), 200


@_require_auth_get("friends_list", sensitive=True)
@bp.get("/api/friends/list/<int:user_id>")
def friends_list(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    current_engine.register_user(user_id, "Guest")
    friends = current_engine.get_friends(user_id)
    return jsonify({"friends": friends}), 200


@_require_auth_post("update_bio")
@bp.post("/api/profile/bio/<int:user_id>")
def update_bio(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    payload = request.get_json(silent=True) or {}
    bio = payload.get("bio", "")
    current_engine.register_user(user_id, "Guest")
    success, message = current_engine.update_bio(user_id, bio)
    return jsonify({"success": success, "message": message}), 200



@bp.get("/api/profile/view/<int:user_id>/<int:target_id>")
def view_profile(user_id: int, target_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    current_engine.register_user(user_id, "Guest")
    current_engine.register_user(target_id, "Guest")
    profile = current_engine.get_public_profile(user_id, target_id)
    return jsonify(profile), 200



@bp.post("/api/translate")
def translate() -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    payload = request.get_json(silent=True) or {}
    text = payload.get("text", "")
    from_lang = payload.get("from_lang", "en")
    to_lang = payload.get("to_lang", "en")
    if not text:
        return jsonify({"error": "Missing 'text' in request body."}), 400
    result = current_engine.translate_text(text, from_lang, to_lang)
    return jsonify(result), 200



@bp.get("/api/chat/history/<int:user_id>")
def chat_history(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    current_engine.register_user(user_id, "Guest")
    profile = current_engine.get_profile(user_id)
    messages = []
    for activity in profile.activity_log[-50:]:
        if activity.get("action") in ["chat_message", "voice_message"]:
            messages.append(activity)
    return jsonify({"messages": messages}), 200


@_require_auth_post("send_chat_message")
@bp.post("/api/chat/send/<int:user_id>")
def send_chat_message(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    payload = request.get_json(silent=True) or {}
    message = payload.get("message", "")
    message_type = payload.get("type", "text")
    if not message:
        return jsonify({"error": "Missing 'message' in request body."}), 400
    current_engine.register_user(user_id, "Guest")
    profile = current_engine.get_profile(user_id)
    profile.log_activity("chat_message" if message_type == "text" else "voice_message", {
        "message": message[:500],
        "user_id": user_id,
        "name": profile.name,
    })
    current_engine._save_user(profile)
    return jsonify({"success": True, "message": "Message sent."}), 200


# --- Popularity & Social Features API ---

@_require_auth_post("like_profile")
@bp.post("/api/profile/like/<int:user_id>")
def like_profile(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    payload = request.get_json(silent=True) or {}
    target_id = payload.get("target_id")
    if not target_id:
        return jsonify({"error": "Missing 'target_id' in request body."}), 400
    current_engine.register_user(user_id, "Guest")
    current_engine.register_user(target_id, "Guest")
    success, message, data = current_engine.like_profile(user_id, target_id)
    return jsonify({"success": success, "message": message, "data": data}), 200


@_require_auth_post("visit_profile")
@bp.post("/api/profile/visit/<int:user_id>")
def visit_profile(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    payload = request.get_json(silent=True) or {}
    target_id = payload.get("target_id")
    if not target_id:
        return jsonify({"error": "Missing 'target_id' in request body."}), 400
    current_engine.register_user(user_id, "Guest")
    current_engine.register_user(target_id, "Guest")
    data = current_engine.visit_profile(user_id, target_id)
    return jsonify(data), 200


@_require_auth_post("update_privacy")
@bp.post("/api/profile/privacy/<int:user_id>")
def update_privacy(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    payload = request.get_json(silent=True) or {}
    settings = payload.get("settings", {})
    current_engine.register_user(user_id, "Guest")
    success, message = current_engine.update_privacy_settings(user_id, settings)
    return jsonify({"success": success, "message": message}), 200


@_require_auth_post("update_theme")
@bp.post("/api/profile/theme/<int:user_id>")
def update_theme(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    payload = request.get_json(silent=True) or {}
    theme = payload.get("theme", "dark")
    current_engine.register_user(user_id, "Guest")
    profile = current_engine.get_profile(user_id)
    profile.theme = theme
    profile.log_activity("update_theme", {"theme": theme})
    current_engine._save_user(profile)
    return jsonify({"success": True, "message": f"Theme updated to {theme}.", "theme": theme}), 200


@_require_auth_post("send_personal_message")
@bp.post("/api/messages/send/<int:user_id>")
def send_personal_message(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    payload = request.get_json(silent=True) or {}
    to_user_id = payload.get("to_user_id")
    message = payload.get("message", "")
    if not to_user_id or not message:
        return jsonify({"error": "Missing 'to_user_id' or 'message'."}), 400
    current_engine.register_user(user_id, "Guest")
    current_engine.register_user(to_user_id, "Guest")
    success, msg = current_engine.send_personal_message(user_id, to_user_id, message)
    return jsonify({"success": success, "message": msg}), 200


@_require_auth_get("get_personal_messages", sensitive=True)
@bp.get("/api/messages/<int:user_id>/with/<int:other_id>")
def get_personal_messages(user_id: int, other_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    current_engine.register_user(user_id, "Guest")
    current_engine.register_user(other_id, "Guest")
    messages = current_engine.get_personal_messages(user_id, other_id)
    return jsonify({"messages": messages}), 200


# --- Admin API Endpoints (New/Moved) ---
