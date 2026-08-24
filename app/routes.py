"""Backward-compatible routes shim.

Legacy imports like ``from app.routes import bp as routes_bp`` keep working
through this module while the real implementations now live in ``app.routes.*``.
"""
from __future__ import annotations

from app.routes import bp, register_all_blueprints

__all__ = ["bp", "register_all_blueprints"]
