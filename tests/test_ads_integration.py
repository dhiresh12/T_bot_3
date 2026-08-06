from app.ads import AdsManager
from app.core import BotEngine
from app.mini_app import create_app


def test_ads_manager_uses_provider_config():
    manager = AdsManager(provider="admob")
    config = manager.get_config()
    assert config["provider"] == "admob"
    assert config["reward_per_ad"] > 0
    assert config["reward_currency"] == "rupees"


def test_app_factory_creates_app():
    app = create_app(BotEngine(storage_path="/tmp/bot3-deploy.json"))
    client = app.test_client()
    response = client.get("/health")
    assert response.status_code == 200


def test_dashboard_and_ads_endpoints():
    engine = BotEngine(storage_path="/tmp/bot3-deploy-2.json")
    app = create_app(engine)
    client = app.test_client()

    ads_response = client.post("/api/ads/watch/123")
    assert ads_response.status_code == 200

    dashboard_response = client.get("/api/dashboard/123")
    assert dashboard_response.status_code == 200
    body = dashboard_response.get_json()
    assert body["wallet"] >= 0.002
