from app.core import BotEngine
from app.mini_app import create_app


def test_sections_endpoint_returns_reusable_sections():
    app = create_app(BotEngine(storage_path="/tmp/bot3-sections.json"))
    client = app.test_client()

    response = client.get("/api/sections/42")
    assert response.status_code == 200

    payload = response.get_json()
    assert payload["user_id"] == 42
    assert any(section["key"] == "ads" for section in payload["sections"])
