"""Flask blueprint: mystery crates / loot boxes."""
from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

bp = Blueprint("crates", __name__)


@bp.get("/api/crates/catalog")
def crate_catalog() -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    return jsonify(current_engine.get_crate_catalog()), 200


@bp.post("/api/crates/open/<int:user_id>")
def open_crate(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    payload = request.get_json(silent=True) or {}
    crate_id = payload.get("crate_id")
    if not crate_id:
        return jsonify({"success": False, "message": "Missing crate_id"}), 400
    success, message, reward = current_engine.open_crate(user_id, crate_id)
    return jsonify({"success": success, "message": message, "reward": reward}), 200
