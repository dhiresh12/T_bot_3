"""Flask blueprint: data insights endpoints."""
from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

bp = Blueprint("insights", __name__)


@bp.post("/api/insights/consent/<int:user_id>")
def set_consent(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    payload = request.get_json(silent=True) or {}
    analytics = bool(payload.get("analytics"))
    personalization = bool(payload.get("personalization"))
    ads_personalization = bool(payload.get("ads_personalization"))
    consent = current_engine.insights_service.set_consent(user_id, analytics, personalization, ads_personalization)
    return jsonify({"success": True, "consent": consent}), 200


@bp.get("/api/insights/consent/<int:user_id>")
def get_consent(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    consent = current_engine.insights_service.get_consent(user_id)
    return jsonify(consent), 200


@bp.post("/api/insights/track/<int:user_id>")
def track_event(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    payload = request.get_json(silent=True) or {}
    event_name = payload.get("event", "")
    properties = payload.get("properties", {})
    if not event_name:
        return jsonify({"error": "Missing event"}), 400
    current_engine.insights_service.record_event(user_id, event_name, properties)
    return jsonify({"success": True}), 200


@bp.get("/api/admin/insights/summary")
def insights_summary() -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    admin_key = request.headers.get("X-Admin-Key")
    if not admin_key or admin_key != current_engine.admin_key:
        return jsonify({"error": "Access Denied"}), 403
    summary = current_engine.insights_service.get_aggregated_insights()
    return jsonify(summary), 200
