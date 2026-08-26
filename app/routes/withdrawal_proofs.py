"""Flask blueprint: public withdrawal proof gallery."""
from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

bp = Blueprint("withdrawal_proofs", __name__)


@bp.get("/api/withdrawals/proofs/gallery")
def proof_gallery() -> tuple[dict, int]:
    current_engine = current_app.config["engine"]
    limit = int(request.args.get("limit", 50))
    proofs = current_engine.get_proof_gallery(limit=limit)
    return jsonify({"proofs": proofs}), 200
