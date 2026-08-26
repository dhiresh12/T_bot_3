"""Route blueprints package.

Each feature area lives in its own module so one broken endpoint
does not prevent the rest of the app from starting.
"""
from __future__ import annotations

from flask import Blueprint

bp = Blueprint("main", __name__)


def register_all_blueprints(app) -> None:
    """Register every route blueprint on the given Flask app.

    If a single blueprint module fails to import, it is skipped and the
    remaining blueprints are still registered.
    """
    modules = [
        "app.routes.auth",
        "app.routes.webhooks",
        "app.routes.ads",
        "app.routes.tasks",
        "app.routes.social",
        "app.routes.popularity",
        "app.routes.withdrawals",
        "app.routes.spin",
        "app.routes.shop",
        "app.routes.notifications",
        "app.routes.leaderboard",
        "app.routes.admin",
        "app.routes.misc",
        "app.routes.streaks",
        "app.routes.events",
        "app.routes.security",
        "app.routes.achievements_share",
        "app.routes.analytics",
        "app.routes.retention",
        "app.routes.withdrawal_proofs",
        "app.routes.referral_tournament",
        "app.routes.flash_sale",
        "app.routes.crates",
        "app.routes.quests",
        "app.routes.kyc",
        "app.routes.receipts",
        "app.routes.app_version",
        "app.routes.withdrawal_enhanced",
        "app.routes.spin_enhanced",
        "app.routes.blocking",
        "app.routes.perks",
        "app.routes.achievements_showcase",
        "app.routes.push_notifications",
        "app.routes.referral_tracking",
        "app.routes.purchases",
        "app.routes.translations",
        "app.routes.affiliate",
        "app.routes.premium",
        "app.routes.insights",
    ]
    for module_name in modules:
        try:
            mod = __import__(module_name, fromlist=["bp"])
            child_bp = getattr(mod, "bp", None)
            if child_bp is not None:
                app.register_blueprint(child_bp)
        except Exception as exc:  # noqa: BLE001
            print(f"[routes][warn] Skipping {module_name}: {exc}")
