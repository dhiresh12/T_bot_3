"""Flask blueprint: affiliate endpoints."""
from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

bp = Blueprint("affiliate", __name__)


@bp.get("/api/affiliate/programs")
def affiliate_programs() -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    programs = current_engine.affiliate_service.get_programs()
    return jsonify({"programs": programs}), 200


@bp.get("/api/affiliate/link/<int:user_id>/<program_id>")
def affiliate_link(user_id: int, program_id: str) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    current_engine.register_user(user_id, "Guest")
    link = current_engine.affiliate_service.generate_affiliate_link(user_id, program_id)
    return jsonify({"link": link}), 200


@bp.post("/api/affiliate/click/<int:user_id>/<program_id>")
def affiliate_click(user_id: int, program_id: str) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    ip_hash = request.headers.get("X-Forwarded-For", "").encode("utf-8").hex()[:16]
    device_hash = request.headers.get("User-Agent", "").encode("utf-8").hex()[:16]
    result = current_engine.affiliate_service.record_click(user_id, program_id, ip_hash, device_hash)
    return jsonify(result), 200


@bp.post("/api/affiliate/convert/<int:user_id>/<program_id>")
def affiliate_convert(user_id: int, program_id: str) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    payload = request.get_json(silent=True) or {}
    sale_amount = float(payload.get("sale_amount", 0))
    success, message, data = current_engine.affiliate_service.record_conversion(user_id, program_id, sale_amount)
    return jsonify({"success": success, "message": message, "data": data}), 200


@bp.get("/api/affiliate/commissions/<int:user_id>")
def affiliate_commissions(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    data = current_engine.affiliate_service.get_user_commissions(user_id)
    return jsonify(data), 200
