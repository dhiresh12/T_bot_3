from app.core import BotEngine
from app.mini_app import create_app


def test_bonus_endpoint_updates_wallet():
    engine = BotEngine(storage_path="/tmp/bot3-miniapp-bonus.json")
    app = create_app(engine)
    client = app.test_client()
    response = client.post("/api/bonus/777", json={"name": "Nadia"})
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["wallet"] >= 0.05

    profile_response = client.get("/api/profile/777")
    assert profile_response.status_code == 200
    profile = profile_response.get_json()
    assert profile["wallet"] >= 0.05


def test_homepage_exposes_dashboard_and_action_hooks():
    engine = BotEngine(storage_path="/tmp/bot3-miniapp-home.json")
    app = create_app(engine)
    client = app.test_client()
    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "/api/dashboard" in html
    assert "Spin for a Gift!" in html
    assert "Withdraw Funds" in html


def test_homepage_contains_interactive_dashboard_controls():
    engine = BotEngine(storage_path="/tmp/bot3-miniapp-controls.json")
    app = create_app(engine)
    client = app.test_client()
    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'id="user-id"' in html
    assert 'id="task-list"' in html
    assert 'id="withdraw-amount"' in html
    assert 'id="invite-link"' in html
