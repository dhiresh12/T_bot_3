"""Flask blueprint: referral deep link tracking."""
from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

bp = Blueprint("referral_tracking", __name__)


@bp.get("/api/referral/track")
def track_referral() -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    user_id = request.args.get("user_id", type=int)
    utm_source = request.args.get("utm_source", "")
    channel = request.args.get("channel", "")
    referrer_id = request.args.get("referrer_id", type=int)
    if not user_id:
        return jsonify({"error": "Missing 'user_id' query parameter."}), 400
    current_engine.register_user(user_id, "Guest")
    if referrer_id:
        current_engine.register_user(referrer_id, "Guest")
    source = current_engine.track_referral(user_id, utm_source, channel, referrer_id)
    return jsonify(source), 200
