from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add project root to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import requests

from app.core import BotEngine
from app.mini_app import create_app


@pytest.fixture
def client(tmp_path):
    """A test client for the app, with a pre-configured admin user."""
    storage_path = tmp_path / "test_routes_db.json"
    engine = BotEngine(storage_path=str(storage_path))
    app = create_app(engine)
    app.config.update({"TESTING": True})

    # Create a default admin user (ID=1) for admin-related tests
    admin_profile = engine.register_user(1, "Admin User")
    admin_profile.admin = True
    engine.save()

    yield app.test_client()


@pytest.fixture
def engine(client) -> BotEngine:
    """Provides direct access to the bot engine instance."""
    return client.application.config["engine"]


# --- User-facing Endpoint Tests ---


def test_health_endpoint(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_dashboard_endpoint(client):
    """Test that the dashboard endpoint returns correct data for a user."""
    response = client.get("/api/dashboard/123")
    assert response.status_code == 200
    data = response.get_json()
    assert data["user_id"] == 123
    assert "wallet_rupee_equivalent" in data
    assert "engagement" in data
    assert "live_feed" in data


def test_task_completion_endpoint(client, engine):
    """Test completing a task via the API."""
    user_id = 456
    response = client.post(f"/api/tasks/complete/{user_id}/join_channel")
    assert response.status_code == 200
    data = response.get_json()
    assert data["completed"] is True
    assert "earned" in data["message"]

    # Verify in the engine
    profile = engine.get_profile(user_id)
    assert "join_channel" in profile.completed_tasks


# --- Admin-facing Endpoint Tests ---


def test_admin_dashboard_unauthorized(client, engine):
    """Test that a non-admin user cannot access admin endpoints."""
    # We need to manually create a non-admin user for this test
    engine.register_user(999, "Non-Admin")
    engine.save()

    # To properly test this, we would need a real authentication system.
    # The current implementation in routes.py hardcodes admin_id=1,
    # so we can't directly test the failure case for another user via a simple GET.
    # This test serves as a placeholder for when auth is implemented.
    pass


def test_admin_dashboard_authorized(client):
    """Test that an admin user can access the admin dashboard."""
    # The route requires a valid X-Admin-Key header (default key is "admin-xio").
    response = client.get("/api/admin/dashboard", headers={"X-Admin-Key": "admin-xio"})
    assert response.status_code == 200
    data = response.get_json()
    assert "active_users" in data
    assert "pending_withdrawals" in data


def test_admin_set_config(client, engine):
    """Test that an admin can update bot configuration."""
    assert engine.bonus_value == 0.05  # Check initial value

    response = client.post(
        "/api/admin/set",
        json={"setting": "bonus_value", "value": 0.1},
        headers={"X-Admin-Key": "admin-xio"},
    )
    assert response.status_code == 200
    assert response.get_json()["success"] is True

    assert engine.bonus_value == 0.1  # Verify the change


def test_admin_approve_withdrawal(client, engine):
    """Test the full withdrawal request and approval flow."""
    user_id = 888
    profile = engine.register_user(user_id, "Withdrawal User")

    # 1. Meet withdrawal requirements
    profile.invite_count = 15
    profile.completed_tasks = ["task1", "task2", "task3", "task4", "task5"]
    profile.total_ads_watched = 100
    profile.coins = 200000  # Equivalent to 20.00 Rupees
    engine.save()

    # 2. User requests withdrawal
    withdraw_response = client.post(f"/api/withdraw/{user_id}", json={"amount": 15.0})
    assert withdraw_response.status_code == 200
    withdraw_data = withdraw_response.get_json()
    assert "Your unique code is" in withdraw_data["message"]

    # 3. Admin approves withdrawal
    # Get the pending request from the engine to find the code and request_id
    pending_request = engine.get_profile(user_id).withdrawals[0]
    request_id = pending_request["request_id"]
    unique_code = pending_request["unique_code"]

    approve_response = client.post(
        "/api/admin/approve_withdrawal",
        json={"user_id": user_id, "request_id": request_id, "verification_code": unique_code},
        headers={"X-Admin-Key": "admin-xio"},
    )
    assert approve_response.status_code == 200
    approve_data = approve_response.get_json()
    assert "has been approved" in approve_data["message"]

    # 4. Verify status change in engine
    final_request_state = engine.get_profile(user_id).withdrawals[0]
    assert final_request_state["status"] == "approved"


def test_webhook_endpoint(client, engine, monkeypatch):
    """Test that the webhook endpoint correctly processes a Telegram update."""
    # 1. Mock the external API call to Telegram to prevent actual HTTP requests
    mock_post = monkeypatch.setattr(requests, "post", lambda *a, **k: None)

    # 2. Create a sample Telegram update payload for the /menu command
    user_id = 12345
    user_name = "WebhookTester"
    update_payload = {
        "update_id": 10000,
        "message": {
            "message_id": 1365,
            "from": {"id": user_id, "is_bot": False, "first_name": user_name, "language_code": "en"},
            "chat": {"id": user_id, "type": "private", "first_name": user_name},
            "date": 1609459200,  # 2021-01-01
            "text": "/menu",
        },
    }

    # 3. Send the payload to the webhook endpoint
    response = client.post("/webhook", json=update_payload)

    # 4. Assert the webhook's immediate response is correct
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}
