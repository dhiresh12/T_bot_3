from app.mini_app import app


def test_bonus_endpoint_updates_wallet():
    client = app.test_client()
    response = client.post("/api/bonus/777", json={"name": "Nadia"})
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["wallet"] >= 0.05

    profile_response = client.get("/api/profile/777")
    assert profile_response.status_code == 200
    profile = profile_response.get_json()
    assert profile["wallet"] >= 0.05


def test_homepage_exposes_support_and_dashboard_hooks():
    client = app.test_client()
    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Support" in html
    assert "/api/support" in html
    assert "Open dashboard" in html


def test_homepage_contains_interactive_dashboard_controls():
    client = app.test_client()
    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'id="userId"' in html
    assert 'Claim Bonus' in html
    assert 'Watch Ad' in html
    assert 'Complete Task' in html
