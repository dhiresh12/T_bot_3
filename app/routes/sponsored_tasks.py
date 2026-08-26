"""Flask blueprint: sponsored tasks with verification."""
from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

bp = Blueprint("sponsored_tasks", __name__)


@bp.get("/api/sponsored-tasks/<int:user_id>")
def sponsored_tasks(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    current_engine.register_user(user_id, "Guest")
    tasks = current_engine.get_sponsored_tasks(user_id)
    return jsonify({"tasks": tasks}), 200


@bp.post("/api/sponsored-tasks/complete/<int:user_id>")
def complete_sponsored_task(user_id: int) -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    payload = request.get_json(silent=True) or {}
    task_id = payload.get("task_id")
    proof = payload.get("proof", "")
    if not task_id:
        return jsonify({"success": False, "message": "Missing task_id"}), 400
    success, message, reward = current_engine.complete_sponsored_task(user_id, task_id, proof)
    return jsonify({"success": success, "message": message, "reward": reward}), 200
