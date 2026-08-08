from app.core import BotEngine
from app.mini_app import create_app
from app.telegram_bot import TelegramBotService


def test_leaderboard_and_withdraw_endpoints():
    engine = BotEngine(storage_path="/tmp/bot3-advanced.json")
    app = create_app(engine)
    client = app.test_client()

    client.post("/api/bonus/901", json={"name": "Mina"})
    response = client.get("/api/leaderboard")
    assert response.status_code == 200
    payload = response.get_json()
    assert isinstance(payload, list)

    # Relax the withdrawal requirements and fund the user so the request succeeds.
    engine.withdrawal_reqs = {"min_invites": 0, "min_tasks": 0, "min_ads": 0}
    profile = engine.get_profile(901)
    profile.coins = 200000  # Worth ₹20 at the default 10,000 coins = ₹1 rate
    profile.wallet_bot = round(profile.coins * engine.coins_to_rupee_rate, 4)
    engine._save_user(profile)

    withdraw_response = client.post("/api/withdraw/901", json={"amount": 10})
    assert withdraw_response.status_code == 200
    body = withdraw_response.get_json()
    assert "submitted" in body["message"].lower()


def test_telegram_bot_handles_ads_command():
    engine = BotEngine(storage_path="/tmp/bot3-telegram-advanced.json")
    service = TelegramBotService(engine=engine)

    update = {
        "message": {
            "chat": {"id": 321, "first_name": "Sara"},
            "text": "/ads",
        }
    }

    response = service.handle_update(update)
    assert "ads" in response.lower() or "watch" in response.lower()


def test_admin_bonus_command_endpoint():
    """Bug #1: /api/admin/commands/bonus endpoint must exist and work."""
    engine = BotEngine(storage_path="/tmp/bot3-admin-bonus.json")
    app = create_app(engine)
    client = app.test_client()

    # Call the admin bonus command endpoint to update the bonus value
    response = client.post(
        "/api/admin/commands/bonus",
        json={"value": 0.10},
        headers={"X-Admin-Key": engine.admin_key},
    )
    assert response.status_code == 200
    body = response.get_json()
    assert body.get("success") is True
    assert engine.bonus_value == 0.10
    assert "bonus" in body.get("message", "").lower()


def test_admin_user_registrations_over_time_endpoint():
    """Bug #2: /api/admin/user_registrations_over_time endpoint must exist."""
    engine = BotEngine(storage_path="/tmp/bot3-admin-registrations.json")
    app = create_app(engine)
    client = app.test_client()

    # Register a user so there's data
    client.post("/api/bonus/888", json={"name": "RegTest"})

    response = client.get(
        "/api/admin/user_registrations_over_time",
        headers={"X-Admin-Key": engine.admin_key},
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert isinstance(payload, list)
