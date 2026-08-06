from app.core import BotEngine
from app.mini_app import create_app


def test_support_and_moderation_endpoints():
    engine = BotEngine(storage_path="/tmp/bot3-support.json")
    app = create_app(engine)
    client = app.test_client()

    support_response = client.get("/api/support")
    assert support_response.status_code == 200

    blocked_response = client.post(
        "/api/support/message",
        json={"message": "this is a rude word"},
    )
    assert blocked_response.status_code == 200
    assert blocked_response.get_json()["status"] == "blocked"
