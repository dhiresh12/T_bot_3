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
