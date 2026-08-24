"""Shared route helpers used across blueprints."""
from __future__ import annotations

import time
from collections import defaultdict
from typing import Any

from flask import Blueprint, current_app, jsonify, request

_rate_limit_store: dict = defaultdict(list)
_RATE_LIMIT_WINDOW = 60
_RATE_LIMIT_MAX = 30


def _check_rate_limit(key: str) -> bool:
    now = time.time()
    window_start = now - _RATE_LIMIT_WINDOW
    _rate_limit_store[key] = [t for t in _rate_limit_store[key] if t > window_start]
    if len(_rate_limit_store[key]) >= _RATE_LIMIT_MAX:
        return False
    _rate_limit_store[key].append(now)
    return True


def _safe_int(value: Any, default: int) -> int:
    """Parses a query-string integer, falling back to a default on bad input."""
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _get_user_id_from_request() -> tuple[int, str]:
    user_id = request.view_args.get("user_id") if request.view_args else None
    if user_id is None:
        return 0, "Missing user_id"
    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        return 0, "Invalid user_id"
    token = request.headers.get("X-User-Token")
    engine = current_app.config.get("engine")
    if not engine:
        return user_id, "ok"
    if not token:
        return user_id, "Missing token"
    if not engine.verify_session(user_id, token):
        return user_id, "Invalid or expired session"
    return user_id, "ok"


def _require_auth_post(endpoint_name: str):
    def decorator(f):
        def wrapper(*args, **kwargs):
            user_id, error = _get_user_id_from_request()
            if error and error != "ok":
                return jsonify({"error": f"Unauthorized: {error}"}), 401
            if not _check_rate_limit(f"post:{user_id}:{endpoint_name}"):
                return jsonify({"error": "Rate limit exceeded. Try again later."}), 429
            return f(*args, **kwargs)
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator


def _require_auth_get(endpoint_name: str, sensitive: bool = False):
    def decorator(f):
        def wrapper(*args, **kwargs):
            user_id, error = _get_user_id_from_request()
            if sensitive and error and error != "ok":
                return jsonify({"error": f"Unauthorized: {error}"}), 401
            if sensitive and not _check_rate_limit(f"get:{user_id}:{endpoint_name}"):
                return jsonify({"error": "Rate limit exceeded. Try again later."}), 429
            return f(*args, **kwargs)
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator
