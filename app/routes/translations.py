"""Flask blueprint: translations API."""
from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

bp = Blueprint("translations", __name__)


@bp.get("/api/translations")
def get_translations() -> tuple[dict, int]:
    lang = request.args.get("lang", "en")
    engine = current_app.config.get("engine")
    if not engine:
        return jsonify({"error": "Engine not available."}), 500
    pack = engine.support.translations.get(lang, engine.support.translations.get("en", {}))
    return jsonify(pack), 200
