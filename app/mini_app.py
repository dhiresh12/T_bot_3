from __future__ import annotations

import json
import os

from flask import Flask, render_template

from app.ads import AdsManager
from app.config import load_config
from app.core import BotEngine
from app.routes import register_all_blueprints


def create_app(engine: BotEngine | None = None) -> Flask:
    app = Flask(__name__, template_folder="templates")
    app.config["SECRET_KEY"] = load_config().secret_key

    current_engine = engine or BotEngine(storage_path="bot_data.db")
    ads_manager = AdsManager(provider=load_config().ads_provider)

    app.config["engine"] = current_engine
    app.config["ads_manager"] = ads_manager
    register_all_blueprints(app)

    # --- Auto-register Telegram webhook on startup ---
    try:
        from app.telegram_bot import TelegramBotService
        bot_service = TelegramBotService(engine=current_engine)
        external_url = os.getenv("RENDER_EXTERNAL_URL") or os.getenv("WEBHOOK_URL")
        if external_url:
            webhook_url = external_url.rstrip("/") + "/webhook"
            bot_service.set_webhook(webhook_url)
        else:
            print("[mini-app][info] RENDER_EXTERNAL_URL/WEBHOOK_URL not set; skipping webhook registration.")
    except Exception as exc:  # noqa: BLE001
        print(f"[mini-app][warn] Webhook registration skipped: {exc}")

    @app.get("/")
    def index() -> str:
        config = load_config()
        return render_template(
            "mini_app.html",
            app_name=config.app_name,
            translations_json=json.dumps(current_engine.support.translations),
            lang_config_json=json.dumps(current_engine.support.lang_config),
            support_links_json=json.dumps(current_engine.support.get_support_links()),
            bot_username=os.getenv("TELEGRAM_BOT_USERNAME", "xiolis_bot"),
            provider=ads_manager.get_config()["provider"],
        )

    return app


app = create_app()

if __name__ == "__main__":
    config = load_config()
    app.run(host=config.host, port=config.port, debug=(config.environment == "development"))
