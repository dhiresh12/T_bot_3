from app.core import BotEngine
from app.mini_app import create_app


def test_engagement_layer_and_endpoint():
    engine = BotEngine(storage_path="/tmp/bot3-engagement.json")
    app = create_app(engine)
    client = app.test_client()

    response = client.get("/api/engagement/900")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["progress"]["tier"] in {"Bronze", "Silver", "Gold", "Diamond"}
    assert len(payload["trust_feed"]) >= 1
