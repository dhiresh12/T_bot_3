"""Flask blueprint: app version enforcement."""
from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

bp = Blueprint("app_version", __name__)


@bp.get("/api/app/version")
def app_version() -> tuple[dict, int]:
    config = current_app.config.get("engine")
    from app.config import load_config
    cfg = load_config()
    return jsonify({
        "current_version": cfg.app_version,
        "min_supported_version": cfg.min_supported_version,
    }), 200


@bp.get("/api/app/check-update")
def check_update() -> tuple[dict, int]:
    from app.config import load_config
    cfg = load_config()
    client_version = request.args.get("version", "0.0.0")
    update_required = client_version != cfg.app_version
    return jsonify({
        "update_required": update_required,
        "current_version": cfg.app_version,
        "min_supported_version": cfg.min_supported_version,
        "client_version": client_version,
    }), 200
