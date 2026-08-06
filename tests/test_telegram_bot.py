from app.telegram_bot import TelegramBotService
from app.core import BotEngine


def test_telegram_bot_handles_start_command():
    engine = BotEngine(storage_path="/tmp/bot3-telegram.json")
    service = TelegramBotService(engine=engine)

    update = {
        "message": {
            "chat": {"id": 555, "first_name": "Amina"},
            "text": "/start",
        }
    }

    response = service.handle_update(update)
    assert "Welcome Amina" in response
