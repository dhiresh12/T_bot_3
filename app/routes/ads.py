"""Flask blueprint: ads endpoints."""
from __future__ import annotations

from app.routes._helpers import (
    _check_rate_limit,
    _safe_int,
    _get_user_id_from_request,
    _require_auth_post,
    _require_auth_get,
)
from flask import Blueprint, current_app, jsonify, request

bp = Blueprint("ads", __name__)



@bp.get("/api/ads/config")
def ads_config() -> tuple[dict, int]:
    ads_manager = current_app.config.get("ads_manager")
    if ads_manager is None:
        return jsonify({"provider": "admob"}), 200
    return jsonify(ads_manager.get_config()), 200



@_require_auth_post("watch_ads")
@bp.post("/api/ads/watch/<int:user_id>")
def watch_ads(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    current_engine.register_user(user_id, "Guest")
    success, message = current_engine.watch_ads(user_id)
    profile = current_engine.get_profile(user_id)
    return jsonify({"success": success, "message": message, "wallet": profile.wallet_bot, "coins": profile.coins}), 200


@_require_auth_post("complete_task")



@_require_auth_post("redeem_more_ads")
@bp.post("/api/ads/redeem-more-ads/<int:user_id>")
def redeem_more_ads(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    payload = request.get_json(silent=True) or {}
    code = payload.get("code", "")
    current_engine.register_user(user_id, "Guest")
    success, message = current_engine.redeem_more_ads(user_id, code)
    profile = current_engine.get_profile(user_id)
    return jsonify({"success": success, "message": message, "daily_ads_watch_count": profile.daily_ads_watch_count, "coins": profile.coins}), 200



@bp.post("/api/ads/verify")
def verify_ad() -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    payload = request.get_json(silent=True) or {}
    ad_unit_id = payload.get("ad_unit_id")
    user_id = payload.get("user_id")
    provider_data = payload.get("provider_data")
    if not ad_unit_id or not user_id:
        return jsonify({"error": "Missing ad_unit_id or user_id"}), 400
    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid user_id"}), 400
    current_engine.register_user(user_id, "Guest")
    ads_manager = current_app.config.get("ads_manager")
    if not ads_manager:
        ads_manager = current_engine.ads_manager if hasattr(current_engine, "ads_manager") else None
    if not ads_manager:
        return jsonify({"error": "Ads manager not configured"}), 500
    result = ads_manager.verify_ad_completion(ad_unit_id, user_id, provider_data)
    if result.get("valid"):
        profile = current_engine.get_profile(user_id)
        profile.coins += result.get("reward_coins", 0)
        profile.total_ads_watched += 1
        profile.daily_ads_watch_count += 1
        profile.log_activity("ad_verified", {"ad_unit_id": ad_unit_id, "reward_coins": result.get("reward_coins", 0), "reward_money": result.get("reward_money", 0.0)})
        current_engine._save_user(profile)
        return jsonify({"success": True, "coins": profile.coins, "reward_coins": result.get("reward_coins", 0), "reward_money": result.get("reward_money", 0.0)}), 200
    return jsonify({"success": False, "reason": result.get("reason", "invalid"), "reward_coins": 0, "reward_money": 0.0}), 400



@bp.get("/api/ads/unit/<int:user_id>")
def get_ad_unit(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    current_engine.register_user(user_id, "Guest")
    ads_manager = current_app.config.get("ads_manager")
    if not ads_manager:
        return jsonify({"error": "Ads manager not configured"}), 500
    ad_index = current_engine.get_profile(user_id).total_ads_watched
    payload = ads_manager.build_verification_payload(user_id, ad_index)
    return jsonify(payload), 200




# --- New Features API Endpoints ---
