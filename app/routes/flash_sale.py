"""Flask blueprint: flash sales."""
from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

bp = Blueprint("flash_sale", __name__)


@bp.get("/api/flash-sale/active")
def active_flash_sale() -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    data = current_engine.get_active_flash_sale()
    return jsonify(data), 200
